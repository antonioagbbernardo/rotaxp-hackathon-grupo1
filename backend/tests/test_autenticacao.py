"""RF31 / CA79–CA83: acesso real, sem bypass de autenticação nos testes."""
from datetime import datetime, timedelta, UTC
from pathlib import Path
import stat

import pytest

from app import create_app
from app.clock import Clock
from app.db import get_db
from app.seed import seed_db


@pytest.fixture
def ambiente(tmp_path):
    agora = [datetime(2026, 10, 10, 16, 0, tzinfo=UTC)]
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text('<html><div id="root">XP Pulse</div></html>')
    (dist / "assets").mkdir()
    (dist / "assets" / "logo.svg").write_text("<svg/>")
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "login.db"),
                      "CLOCK": Clock(lambda: agora[0]), "FRONTEND_DIST": str(dist),
                      "SECRET_KEY": "assinatura-ficticia-apenas-nos-testes"})
    with app.app_context():
        seed_db(app.config["CLOCK"].hoje(), app.config["CLOCK"].agora())
    return app, app.test_client(), agora


def entrar(client, usuario="admin", senha="admin"):
    token = client.get("/api/auth/sessao").get_json()["csrf_token"]
    return client.post("/api/auth/login", json={"usuario": usuario, "senha": senha},
                       headers={"X-CSRF-Token": token})


def test_ca79_login_publico_e_paginas_protegidas(ambiente):
    _, c, _ = ambiente
    assert c.get("/login").status_code == 200
    for caminho in ("/", "/legacy"):
        resposta = c.get(caminho)
        assert resposta.status_code == 302 and resposta.headers["Location"] == "/login"
    assert c.get("/assets/logo.svg").status_code == 200
    assert c.get("/api/auth/sessao").get_json()["autenticado"] is False


def test_ca79_todas_as_apis_exigem_acesso_antes_do_servico(ambiente):
    app, c, _ = ambiente
    # Percorre o mapa de rotas para também abranger extensões futuras.
    for regra in app.url_map.iter_rules():
        if not regra.rule.startswith("/api/") or regra.rule.startswith("/api/auth/"):
            continue
        caminho = regra.rule
        for argumento in regra.arguments:
            caminho = caminho.replace(f"<int:{argumento}>", "1").replace(f"<{argumento}>", "teste")
        for metodo in regra.methods - {"HEAD", "OPTIONS"}:
            resposta = c.open(caminho, method=metodo, json={})
            assert resposta.status_code == 401, (metodo, caminho)
            assert resposta.get_json()["erro"]["codigo"] == "sessao_necessaria"
            assert resposta.headers["Cache-Control"] == "no-store"
    assert c.get("/api/futura-rota").status_code == 401


def test_ca80_login_cookie_e_acesso_sem_csrf_na_leitura(ambiente):
    _, c, _ = ambiente
    antes = c.get("/api/auth/sessao").get_json()["csrf_token"]
    r = entrar(c, " admin ")
    assert r.status_code == 200
    assert r.get_json()["autenticado"] is True and r.get_json()["usuario"] == "admin"
    assert r.get_json()["csrf_token"] != antes
    assert "HttpOnly" in r.headers["Set-Cookie"] and "SameSite=Lax" in r.headers["Set-Cookie"]
    assert "senha" not in r.get_json()
    assert c.get("/api/clientes").status_code == 200
    assert c.get("/").status_code == 200
    assert c.get("/legacy").status_code == 200
    assert c.get("/login").headers["Location"] == "/"


@pytest.mark.parametrize("usuario,senha", [("admin", "errada"), ("errado", "admin"),
                                          ("Admin", "admin"), ("admin", "admin ")])
def test_ca80_credenciais_invalidas_nao_criam_sessao(ambiente, usuario, senha):
    app, c, _ = ambiente
    r = entrar(c, usuario, senha)
    assert r.status_code == 401
    assert r.get_json()["erro"] == {"codigo": "credenciais_invalidas", "campo": None,
                                   "mensagem": "Usuário ou senha incorretos."}
    assert c.get("/api/pulse").status_code == 401
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM sessao_acesso").fetchone()[0] == 0


@pytest.mark.parametrize("corpo,campo", [({}, "usuario"), ({"usuario": "admin"}, "senha"),
    ({"usuario": "   ", "senha": "admin"}, "usuario"),
    ({"usuario": 7, "senha": "admin"}, "usuario"),
    ({"usuario": "admin", "senha": False}, "senha"),
    ({"usuario": "x" * 81, "senha": "admin"}, "usuario"),
    ({"usuario": "admin", "senha": "x" * 257}, "senha"),
    ({"usuario": "admin", "senha": "admin", "perfil": "admin"}, "perfil"),
    ([], "corpo")])
def test_ca80_corpo_invalido_e_campos_extras(ambiente, corpo, campo):
    _, c, _ = ambiente
    token = c.get("/api/auth/sessao").get_json()["csrf_token"]
    r = c.post("/api/auth/login", json=corpo, headers={"X-CSRF-Token": token})
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == campo
    assert c.get("/api/auth/sessao").get_json()["autenticado"] is False


def test_ca80_json_malformado_e_sem_content_type(ambiente):
    _, c, _ = ambiente
    token = c.get("/api/auth/sessao").get_json()["csrf_token"]
    for content_type in ("application/json", "text/plain"):
        r = c.post("/api/auth/login", data="{quebrado", content_type=content_type,
                   headers={"X-CSRF-Token": token})
        assert r.status_code == 400 and r.get_json()["erro"]["campo"] == "corpo"


def test_ca81_csrf_obrigatorio_no_login_e_mutacao_sem_gravacao(ambiente):
    app, c, _ = ambiente
    assert c.post("/api/auth/login", json={"usuario": "admin", "senha": "admin"}).status_code == 403
    token_antigo = c.get("/api/auth/sessao").get_json()["csrf_token"]
    token = entrar(c).get_json()["csrf_token"]
    corpo = {"canal": "telefone", "texto": "Contato fictício autorizado."}
    for headers in ({}, {"X-CSRF-Token": "errado"}, {"X-CSRF-Token": token_antigo}):
        r = c.post("/api/clientes/5/interacoes", json=corpo, headers=headers)
        assert r.status_code == 403 and r.get_json()["erro"]["codigo"] == "csrf_invalido"
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM interacao WHERE cliente_id=5").fetchone()[0] == 0
    assert c.post("/api/clientes/5/interacoes", json=corpo, headers={"X-CSRF-Token": token}).status_code == 201
    outro = app.test_client()
    token_outro = entrar(outro).get_json()["csrf_token"]
    assert c.post("/api/auth/logout", headers={"X-CSRF-Token": token_outro}).status_code == 403
    assert c.get("/api/clientes").status_code == 200


def test_ca82_expiracao_absoluta_pelo_clock(ambiente):
    app, c, agora = ambiente
    assert entrar(c).status_code == 200
    agora[0] += timedelta(hours=8, seconds=-1)
    assert c.get("/api/clientes").status_code == 200
    agora[0] += timedelta(seconds=1)
    assert c.get("/api/clientes").status_code == 401
    assert c.get("/api/auth/sessao").get_json()["autenticado"] is False
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM sessao_acesso").fetchone()[0] == 0


def test_ca82_logout_revoga_cookie_copiado_sem_apagar_clientes(ambiente):
    app, c, _ = ambiente
    token = entrar(c).get_json()["csrf_token"]
    cookie = c.get_cookie(app.config["SESSION_COOKIE_NAME"]).value
    assert c.post("/api/auth/logout", headers={"X-CSRF-Token": token}).get_json()["autenticado"] is False
    assert c.get("/api/pulse").status_code == 401
    outro = app.test_client()
    outro.set_cookie(app.config["SESSION_COOKIE_NAME"], cookie)
    assert outro.get("/api/clientes").status_code == 401
    assert entrar(c).status_code == 200
    assert len(c.get("/api/clientes").get_json()["clientes"]) == 5


def test_ca82_cookie_adulterado_nao_concede_acesso(ambiente):
    app, c, _ = ambiente
    entrar(c)
    nome = app.config["SESSION_COOKIE_NAME"]
    cookie = c.get_cookie(nome).value
    outro = app.test_client()
    outro.set_cookie(nome, ("A" if cookie[0] != "A" else "B") + cookie[1:])
    assert outro.get("/api/pulse").status_code == 401


def test_ca82_chave_local_persiste_e_cookie_funciona_apos_reinicio(tmp_path):
    config = {"TESTING": True, "DATABASE": str(tmp_path / "reinicio.db"), "SECRET_KEY": None}
    app = create_app(config)
    with app.app_context():
        seed_db(app.config["CLOCK"].hoje(), app.config["CLOCK"].agora())
    c = app.test_client()
    entrar(c)
    cookie = c.get_cookie(app.config["SESSION_COOKIE_NAME"]).value
    nova = create_app(config)
    assert nova.secret_key == app.secret_key and len(app.secret_key) >= 32
    arquivo = Path(config["DATABASE"]).parent / "session.key"
    assert stat.S_IMODE(arquivo.stat().st_mode) == 0o600
    outro = nova.test_client()
    outro.set_cookie(nova.config["SESSION_COOKIE_NAME"], cookie)
    assert outro.get("/api/pulse").status_code == 200


def test_ca83_html_e_api_nao_ficam_em_cache(ambiente):
    _, c, _ = ambiente
    entrar(c)
    for caminho in ("/", "/legacy", "/login", "/api/auth/sessao", "/api/pulse"):
        assert c.get(caminho).headers["Cache-Control"] == "no-store"
