"""Login local: sessão revogável, chave persistente e proteção de escritas."""
from datetime import timedelta
from hashlib import sha256
from hmac import compare_digest
import os
import sqlite3
import click
from pathlib import Path
from secrets import token_urlsafe
from tempfile import mkstemp

from flask import Blueprint, current_app, g, jsonify, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .autenticacao_rules import ErroCredenciais, validar_login
from .db import get_db

bp = Blueprint("autenticacao", __name__, url_prefix="/api/auth")
PUBLICAS = {"autenticacao.consultar_sessao", "autenticacao.login"}
VALIDADE = 8 * 60 * 60


def _auth_db():
    if 'auth_db' not in g:
        g.auth_db = sqlite3.connect(current_app.config['DATABASE'])
        g.auth_db.row_factory = sqlite3.Row
    return g.auth_db


def banco_usuario(usuario):
    row = _auth_db().execute('SELECT banco FROM usuario_acesso WHERE usuario=?',(usuario,)).fetchone()
    return row['banco'] if row else None


def _demo():
    return bool(current_app.config.get('PULSE_DEMO_LOGIN', True)) and not _auth_db().execute('SELECT 1 FROM usuario_acesso LIMIT 1').fetchone()


def criar_acesso(usuario, senha, nome):
    """Conta local e base própria. Credenciais nunca são gravadas em texto puro."""
    from .db import init_db, close_db
    usuario, senha = validar_login({'usuario':usuario,'senha':senha})
    if len(senha) < 12 or senha == 'admin':
        raise click.ClickException('Use uma senha de pelo menos 12 caracteres.')
    controle = _auth_db()
    if controle.execute('SELECT 1 FROM usuario_acesso WHERE usuario=?',(usuario,)).fetchone():
        raise click.ClickException('Usuário já cadastrado.')
    pasta = Path(current_app.config['DATABASE']).parent / 'assessores'
    pasta.mkdir(mode=0o700, exist_ok=True)
    banco = pasta / f'{token_urlsafe(24)}.db'
    # Outro contexto impede que o provisionamento troque a conexão de quem chamou.
    with current_app.app_context():
        g.tenant_database = str(banco)
        init_db()
        get_db().execute('INSERT INTO assessor(id,nome) VALUES(1,?)',(nome.strip(),))
        get_db().commit()
        close_db()
    banco.chmod(0o600)
    controle.execute('INSERT INTO usuario_acesso(usuario,senha_hash,banco) VALUES(?,?,?)',
                     (usuario,generate_password_hash(senha),str(banco)))
    # A primeira conta real encerra sessões de demonstração existentes.
    controle.execute("DELETE FROM sessao_acesso WHERE usuario IS NULL OR usuario='__demo__'")
    controle.commit()
    return str(banco)


def _reservar_tentativa(usuario):
    db, agora = _auth_db(), _agora()
    chaves = [('usuario:'+_hash_token(usuario),5), ('ip:'+_hash_token(request.remote_addr or 'local'),20)]
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute('DELETE FROM tentativa_login WHERE expira_em<=?',(agora,))
        for chave, limite in chaves:
            r = db.execute('SELECT * FROM tentativa_login WHERE chave=?',(chave,)).fetchone()
            if r and r['tentativas'] >= limite:
                db.rollback()
                return r['expira_em'] - agora
        for chave, _ in chaves:
            db.execute('INSERT INTO tentativa_login VALUES(?,1,?) ON CONFLICT(chave) DO UPDATE SET tentativas=tentativas+1',
                       (chave,agora+900))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return 0


def _agora():
    return int(current_app.config["CLOCK"].agora().timestamp())


def _hash_token(token):
    return sha256(token.encode()).hexdigest()


def _limpar_sessao():
    token = session.get("acesso")
    if isinstance(token, str):
        db = _auth_db()
        db.execute("DELETE FROM sessao_acesso WHERE token_hash=?", (_hash_token(token),))
        db.commit()
    session.clear()
    g.pop('usuario', None)
    g.pop('tenant_database', None)


def autenticado():
    token = session.get("acesso")
    if not isinstance(token, str):
        return False
    registro = _auth_db().execute("SELECT expira_em,usuario FROM sessao_acesso WHERE token_hash=?",
                               (_hash_token(token),)).fetchone()
    if registro is not None and registro["expira_em"] > _agora():
        usuario = registro['usuario']
        if usuario == '__demo__' and _demo():
            g.usuario = 'admin'
            return True
        banco = banco_usuario(usuario)
        if banco and Path(banco).is_file():
            g.usuario = usuario
            g.tenant_database = banco
            return True
    _limpar_sessao()
    return False


def _estado():
    acesso = autenticado()
    if "csrf" not in session:
        session["csrf"] = token_urlsafe(32)
    return jsonify(autenticado=acesso, usuario=g.get('usuario') if acesso else None,
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
    espera = _reservar_tentativa(usuario)
    if espera:
        resposta, status = _erro('tentativas_excedidas','Muitas tentativas. Aguarde antes de entrar novamente.',429)
        resposta.headers['Retry-After'] = str(espera)
        return resposta,status
    conta = _auth_db().execute('SELECT senha_hash FROM usuario_acesso WHERE usuario=?',(usuario,)).fetchone()
    demo = _demo()
    usuario_correto = conta is not None or (demo and compare_digest(usuario.encode(), b'admin'))
    senha_correta = check_password_hash(conta['senha_hash'] if conta else current_app.config['LOGIN_SENHA_HASH'],senha)
    if not (usuario_correto and senha_correta):
        return _erro("credenciais_invalidas", "Usuário ou senha incorretos.", 401)
    _limpar_sessao()
    token, agora = token_urlsafe(32), _agora()
    db = _auth_db()
    db.execute("DELETE FROM sessao_acesso WHERE expira_em<=?", (agora,))
    db.execute('DELETE FROM tentativa_login WHERE chave=?',('usuario:'+_hash_token(usuario),))
    db.execute("INSERT INTO sessao_acesso(token_hash, expira_em,usuario) VALUES (?,?,?)",
               (_hash_token(token), agora + VALIDADE, usuario if conta else '__demo__'))
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
    with app.app_context():
        contas=_auth_db().execute('SELECT banco FROM usuario_acesso').fetchall()
        for conta in contas:
            if Path(conta['banco']).is_file():
                with app.app_context():
                    from .db import init_db
                    g.tenant_database=conta['banco']
                    init_db()

    @app.cli.command('criar-acesso')
    @click.option('--usuario', required=True)
    @click.option('--nome', required=True)
    @click.option('--senha', prompt=True, hide_input=True, confirmation_prompt=True)
    def criar_conta(usuario,nome,senha):
        """Cria um assessor com base vazia e desativa o login de demonstração."""
        criar_acesso(usuario,senha,nome)
        click.echo('Acesso criado com base isolada. Login de demonstração desativado.')

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
