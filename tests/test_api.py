from datetime import date

import pytest

from app import create_app
from app.db import init_db
from app.seed import seed_db


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db"), "HOJE": lambda: date(2026, 10, 10)})
    with app.app_context():
        init_db()
        seed_db(date(2026, 10, 10))
    return app.test_client()


def test_lista_clientes(client):
    r = client.get("/api/clientes")
    assert r.status_code == 200
    nomes = [c["nome"] for c in r.get_json()["clientes"]]
    assert len(nomes) == 3


def test_detalhe_somente_dados_do_cliente(client):
    dados = client.get("/api/clientes/1").get_json()
    assert dados["cliente"]["id"] == 1
    assert all(p["cliente_id"] == 1 for p in dados["posicoes"])


def test_cliente_inexistente_404(client):
    r = client.get("/api/clientes/999")
    assert r.status_code == 404
    assert r.get_json()["erro"]["codigo"] == "nao_encontrado"


def test_rotas_pendentes_devolvem_501_explicito(client):
    assert client.post("/api/clientes/1/interacoes", json={}).status_code == 501
    assert client.post("/api/alertas/1/tratar").status_code == 501


def test_pagina_base(client):
    assert client.get("/").status_code == 200
