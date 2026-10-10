"""Login local: sessão revogável, chave persistente e proteção de escritas."""
from datetime import timedelta
from hashlib import sha256
from hmac import compare_digest
import os
from pathlib import Path
from secrets import token_urlsafe
from tempfile import mkstemp

from flask import Blueprint, current_app, jsonify, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .autenticacao_rules import ErroCredenciais, validar_login
from .db import get_db

bp = Blueprint("autenticacao", __name__, url_prefix="/api/auth")
PUBLICAS = {"autenticacao.consultar_sessao", "autenticacao.login"}
VALIDADE = 8 * 60 * 60


def _agora():
    return int(current_app.config["CLOCK"].agora().timestamp())


def _hash_token(token):
    return sha256(token.encode()).hexdigest()


def _limpar_sessao():
    token = session.get("acesso")
    if isinstance(token, str):
        db = get_db()
        db.execute("DELETE FROM sessao_acesso WHERE token_hash=?", (_hash_token(token),))
        db.commit()
    session.clear()


def autenticado():
    token = session.get("acesso")
    if not isinstance(token, str):
        return False
    registro = get_db().execute("SELECT expira_em FROM sessao_acesso WHERE token_hash=?",
                               (_hash_token(token),)).fetchone()
    if registro is not None and registro["expira_em"] > _agora():
        return True
    _limpar_sessao()
    return False


def _estado():
    acesso = autenticado()
    if "csrf" not in session:
        session["csrf"] = token_urlsafe(32)
    return jsonify(autenticado=acesso, usuario="admin" if acesso else None,
                   csrf_token=session["csrf"])


def _erro(codigo, mensagem, status, campo=None):
    return jsonify(erro={"codigo": codigo, "campo": campo, "mensagem": mensagem}), status


@bp.get("/sessao")
def consultar_sessao():
    return _estado()


@bp.post("/login")
def login():
    if request.content_length is not None and request.content_length > 8192:
        return _erro("entrada_invalida", "Corpo do login muito grande.", 400, "corpo")
    try:
        usuario, senha = validar_login(request.get_json(silent=True))
    except ErroCredenciais as exc:
        return _erro("entrada_invalida", str(exc), 400, exc.campo)
    usuario_correto = compare_digest(usuario.encode(), b"admin")
    senha_correta = check_password_hash(current_app.config["LOGIN_SENHA_HASH"], senha)
    if not (usuario_correto and senha_correta):
        return _erro("credenciais_invalidas", "Usuário ou senha incorretos.", 401)
    _limpar_sessao()
    token, agora = token_urlsafe(32), _agora()
    db = get_db()
    db.execute("DELETE FROM sessao_acesso WHERE expira_em<=?", (agora,))
    db.execute("INSERT INTO sessao_acesso(token_hash, expira_em) VALUES (?,?)",
               (_hash_token(token), agora + VALIDADE))
    db.commit()
    session["acesso"] = token
    session["csrf"] = token_urlsafe(32)
    return _estado()


@bp.post("/logout")
def logout():
    _limpar_sessao()
    return _estado()


def _chave_local(caminho_banco):
    """Publicar arquivo já completo de forma atômica; nunca imprimir seu valor."""
    pasta = Path(caminho_banco).parent
    caminho = pasta / "session.key"
    if not caminho.exists():
        fd, temporario = mkstemp(prefix=".session-", dir=pasta)  # permissão 0600
        try:
            with os.fdopen(fd, "w") as arquivo:
                arquivo.write(token_urlsafe(48))
            try:
                os.link(temporario, caminho)
            except FileExistsError:
                pass  # outra inicialização publicou primeiro
        finally:
            os.unlink(temporario)
    chave = caminho.read_text().strip()
    if len(chave) < 32:
        raise RuntimeError("Chave de sessão local inválida; configure SECRET_KEY.")
    return chave


def init_app(app):
    if not app.secret_key:
        app.secret_key = _chave_local(app.config["DATABASE"])
    app.config.update(SESSION_COOKIE_NAME="xp_pulse_session", SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", SESSION_REFRESH_EACH_REQUEST=False,
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
    app.config["LOGIN_SENHA_HASH"] = generate_password_hash("admin")
    app.register_blueprint(bp)

    @app.before_request
    def proteger_acesso():
        if request.path in {"/", "/legacy"} and not autenticado():
            return redirect("/login")
        if request.path == "/login" and autenticado():
            return redirect("/")
        if request.path == "/api" or request.path.startswith("/api/"):
            if request.endpoint not in PUBLICAS and not autenticado():
                return _erro("sessao_necessaria", "Entre novamente para acessar o XP Pulse.", 401)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                recebido = request.headers.get("X-CSRF-Token", "")
                esperado = session.get("csrf", "")
                if not recebido or not esperado or not compare_digest(recebido.encode(), esperado.encode()):
                    return _erro("csrf_invalido", "Atualize a sessão antes de tentar novamente.", 403, "csrf_token")

    @app.after_request
    def proteger_cache(resposta):
        if request.path in {"/", "/login", "/legacy", "/api"} or request.path.startswith("/api/"):
            resposta.headers["Cache-Control"] = "no-store"
            resposta.headers["X-Content-Type-Options"] = "nosniff"
            resposta.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resposta
