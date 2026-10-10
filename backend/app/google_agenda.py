"""OAuth e sincronização unidirecional com o calendário principal do Google."""
import base64
from datetime import timedelta
from hashlib import sha256
from hmac import new as hmac_new
import json
from secrets import compare_digest, token_urlsafe
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app, session
from cryptography.fernet import Fernet, InvalidToken

from .clock import TZ, formatar_utc, parse_instante
from .db import get_db

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
API_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
ESCOPO = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email"
TIMEOUT = 15


class ErroGoogleAgenda(Exception):
    def __init__(self, mensagem, status=502):
        self.mensagem, self.status = mensagem, status


def _configurado():
    return all(current_app.config.get(chave) for chave in (
        "GOOGLE_CALENDAR_CLIENT_ID", "GOOGLE_CALENDAR_CLIENT_SECRET", "GOOGLE_CALENDAR_REDIRECT_URI"))


def _fernet():
    segredo = current_app.secret_key
    if isinstance(segredo, str):
        segredo = segredo.encode()
    chave = hmac_new(segredo, b"xp-pulse-google-agenda-token", sha256).digest()
    return Fernet(base64.urlsafe_b64encode(chave))


def _cifrar(valor):
    return _fernet().encrypt(valor.encode()).decode()


def _decifrar(valor):
    try:
        return _fernet().decrypt(valor.encode()).decode()
    except InvalidToken as exc:
        raise ErroGoogleAgenda("Não foi possível abrir o token local. Confira a chave de sessão persistente.") from exc


def _resposta_erro(exc):
    try:
        dados = json.loads(exc.read())
    except (json.JSONDecodeError, UnicodeDecodeError):
        dados = {}
    erro = dados.get("error_description") if isinstance(dados, dict) else None
    if not erro and isinstance(dados, dict) and isinstance(dados.get("error"), dict):
        erro = dados["error"].get("message")
    return erro if isinstance(erro, str) and erro else f"Google Agenda respondeu HTTP {exc.code}."


def _solicitar(metodo, url, dados=None, access_token=None, formulario=False):
    corpo = (urlencode(dados).encode() if formulario else json.dumps(dados).encode()) if dados is not None else None
    cabecalhos = {"Accept": "application/json"}
    if corpo is not None:
        cabecalhos["Content-Type"] = "application/x-www-form-urlencoded" if formulario else "application/json"
    if access_token:
        cabecalhos["Authorization"] = f"Bearer {access_token}"
    pedido = Request(url, data=corpo, headers=cabecalhos, method=metodo)
    try:
        with urlopen(pedido, timeout=TIMEOUT) as resposta:
            bruto = resposta.read()
    except HTTPError as exc:
        raise ErroGoogleAgenda(_resposta_erro(exc), exc.code) from exc
    except (URLError, TimeoutError) as exc:
        raise ErroGoogleAgenda("Não foi possível conectar ao Google Agenda.") from exc
    if not bruto:
        return {}
    try:
        return json.loads(bruto)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ErroGoogleAgenda("O Google Agenda retornou uma resposta inválida.") from exc


def estado():
    token = get_db().execute("SELECT email FROM google_agenda_token WHERE id=1").fetchone()
    return {
        "configurado": _configurado(),
        "conectado": token is not None,
        "email": token["email"] if token else None,
    }


def url_autorizacao():
    if not _configurado():
        raise ErroGoogleAgenda("Configure client ID, client secret e URI de retorno OAuth no backend.", 503)
    estado_oauth = token_urlsafe(32)
    session["google_agenda_oauth_state"] = estado_oauth
    parametros = {
        "client_id": current_app.config["GOOGLE_CALENDAR_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_CALENDAR_REDIRECT_URI"],
        "response_type": "code",
        "scope": ESCOPO,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": estado_oauth,
    }
    return {"url": f"{AUTH_URL}?{urlencode(parametros)}"}


def _gravar_token(email, access_token, refresh_token, expira_em):
    get_db().execute(
        """INSERT INTO google_agenda_token(id,email,access_token,refresh_token,expira_em)
           VALUES (1,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET email=excluded.email, access_token=excluded.access_token,
             refresh_token=excluded.refresh_token, expira_em=excluded.expira_em""",
        (email, _cifrar(access_token), _cifrar(refresh_token), expira_em),
    )
    get_db().commit()


def concluir_oauth(code, estado_recebido):
    estado_esperado = session.pop("google_agenda_oauth_state", None)
    if not isinstance(estado_esperado, str) or not isinstance(estado_recebido, str) or not compare_digest(estado_esperado, estado_recebido):
        raise ErroGoogleAgenda("A validação de segurança OAuth falhou. Inicie a conexão novamente.", 400)
    if not _configurado():
        raise ErroGoogleAgenda("A configuração OAuth do Google Agenda está incompleta.", 503)
    resposta = _solicitar("POST", TOKEN_URL, {
        "code": code,
        "client_id": current_app.config["GOOGLE_CALENDAR_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CALENDAR_CLIENT_SECRET"],
        "redirect_uri": current_app.config["GOOGLE_CALENDAR_REDIRECT_URI"],
        "grant_type": "authorization_code",
    }, formulario=True)
    if not isinstance(resposta, dict):
        raise ErroGoogleAgenda("O Google retornou uma resposta OAuth inválida.")
    access_token, refresh_token = resposta.get("access_token"), resposta.get("refresh_token")
    if not isinstance(access_token, str) or not access_token:
        raise ErroGoogleAgenda("O Google não retornou um token de acesso válido.")
    anterior = get_db().execute("SELECT refresh_token FROM google_agenda_token WHERE id=1").fetchone()
    if not refresh_token and anterior:
        try:
            refresh_token = _decifrar(anterior["refresh_token"])
        except ErroGoogleAgenda:
            refresh_token = None
    if not isinstance(refresh_token, str) or not refresh_token:
        raise ErroGoogleAgenda("O Google não retornou autorização para renovação. Tente conectar novamente.")
    try:
        validade = int(resposta["expires_in"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ErroGoogleAgenda("O Google retornou validade de token inválida.") from exc
    if validade <= 0:
        raise ErroGoogleAgenda("O Google retornou validade de token inválida.")
    usuario = _solicitar("GET", USERINFO_URL, access_token=access_token)
    if not isinstance(usuario, dict):
        raise ErroGoogleAgenda("O Google retornou dados de conta inválidos.")
    email = usuario.get("email")
    if not isinstance(email, str) or not email:
        raise ErroGoogleAgenda("Não foi possível identificar a conta Google conectada.")
    expira_em = formatar_utc(current_app.config["CLOCK"].agora() + timedelta(seconds=validade))
    _gravar_token(email, access_token, refresh_token, expira_em)


def _token(forcar_renovacao=False):
    db = get_db()
    registro = db.execute("SELECT * FROM google_agenda_token WHERE id=1").fetchone()
    if registro is None:
        raise ErroGoogleAgenda("Conecte uma conta Google antes de sincronizar.")
    expira_em = parse_instante(registro["expira_em"])
    agora = current_app.config["CLOCK"].agora()
    if not forcar_renovacao and expira_em > agora + timedelta(seconds=60):
        return _decifrar(registro["access_token"])
    resposta = _solicitar("POST", TOKEN_URL, {
        "client_id": current_app.config["GOOGLE_CALENDAR_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CALENDAR_CLIENT_SECRET"],
        "refresh_token": _decifrar(registro["refresh_token"]),
        "grant_type": "refresh_token",
    }, formulario=True)
    if not isinstance(resposta, dict):
        raise ErroGoogleAgenda("O Google retornou uma resposta de renovação inválida.")
    access_token = resposta.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ErroGoogleAgenda("O Google não conseguiu renovar a autorização.")
    try:
        validade = int(resposta["expires_in"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ErroGoogleAgenda("O Google retornou validade de token inválida.") from exc
    if validade <= 0:
        raise ErroGoogleAgenda("O Google retornou validade de token inválida.")
    db.execute(
        "UPDATE google_agenda_token SET access_token=?, expira_em=? WHERE id=1",
        (_cifrar(access_token), formatar_utc(agora + timedelta(seconds=validade))),
    )
    db.commit()
    return access_token


def _api(metodo, url, dados=None, permitir_404=False):
    token = _token()
    try:
        return _solicitar(metodo, url, dados, token)
    except ErroGoogleAgenda as exc:
        if permitir_404 and exc.status == 404:
            return None
        if exc.status != 401:
            raise
    token = _token(forcar_renovacao=True)
    try:
        return _solicitar(metodo, url, dados, token)
    except ErroGoogleAgenda as exc:
        if permitir_404 and exc.status == 404:
            return None
        raise


def _id_evento(reuniao_id):
    digest = sha256(f"xp-pulse-reuniao:{reuniao_id}".encode()).digest()
    return base64.b32hexencode(digest).decode("ascii").lower().rstrip("=")


def _evento(r):
    inicio = parse_instante(r["inicio_em"]).astimezone(TZ)
    fim = inicio + timedelta(hours=1)
    return {
        "summary": f"Reunião com {r['cliente_nome']}",
        "description": r["objetivo"],
        "start": {"dateTime": inicio.isoformat(timespec="seconds"), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": fim.isoformat(timespec="seconds"), "timeZone": "America/Sao_Paulo"},
    }


def _marcar(reuniao_id, estado_sync, erro=None, evento_id=None, url=None):
    get_db().execute(
        """UPDATE reuniao SET google_sync_status=?, google_sync_error=?,
           google_event_id=COALESCE(?,google_event_id),
           google_event_url=CASE WHEN ? IS NULL THEN google_event_url ELSE ? END
           WHERE id=?""",
        (estado_sync, erro, evento_id, url, url, reuniao_id),
    )
    get_db().commit()


def sincronizar(reuniao):
    rid = reuniao["id"]
    if not _configurado():
        _marcar(rid, "nao_configurado")
        return
    if get_db().execute("SELECT 1 FROM google_agenda_token WHERE id=1").fetchone() is None:
        _marcar(rid, "nao_conectado")
        return
    if reuniao["estado"] == "concluida":
        return
    evento_id = _id_evento(rid)
    try:
        url = f"{API_URL}/{evento_id}"
        if reuniao["estado"] == "cancelada":
            _api("DELETE", url, permitir_404=True)
            _marcar(rid, "sincronizado", evento_id=evento_id, url="")
            return
        evento_atual = _api("GET", url, permitir_404=True)
        if evento_atual is None:
            try:
                evento_atual = _api("POST", API_URL, {"id": evento_id, **_evento(reuniao)})
            except ErroGoogleAgenda as exc:
                if exc.status != 409:
                    raise
                evento_atual = _api("GET", url)
        else:
            evento_atual = _api("PATCH", url, _evento(reuniao))
        if not isinstance(evento_atual, dict):
            raise ErroGoogleAgenda("O Google retornou dados de evento inválidos.")
        _marcar(rid, "sincronizado", evento_id=evento_id, url=evento_atual.get("htmlLink"))
    except ErroGoogleAgenda as exc:
        current_app.logger.warning("Falha ao sincronizar reunião %s com Google Agenda: %s", rid, exc.mensagem)
        _marcar(rid, "falhou", erro=exc.mensagem)


def desconectar():
    db = get_db()
    token = db.execute("SELECT access_token FROM google_agenda_token WHERE id=1").fetchone()
    aviso = None
    if token:
        try:
            _solicitar("POST", REVOKE_URL, {"token": _decifrar(token["access_token"])}, formulario=True)
        except ErroGoogleAgenda as exc:
            aviso = f"A autorização local foi removida, mas não foi possível revogá-la no Google: {exc.mensagem}"
        db.execute("DELETE FROM google_agenda_token WHERE id=1")
        db.commit()
    return {"conectado": False, "aviso": aviso}
