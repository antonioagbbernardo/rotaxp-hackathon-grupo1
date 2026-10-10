"""Regressões da revisão documental; a suíte anterior permanece intacta."""
from datetime import datetime

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.seed import seed_db

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


@pytest.fixture
def aplicacao(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "regressoes.db"),
                      "CLOCK": relogio_fixo(AGORA)})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app


@pytest.mark.parametrize("valor", [None, "", "2026-10-09", 123, False,
                                  "0001-01-01T00:00:00+03:00", "9999-12-31T23:59:59-03:00",
                                  "0001-01-01T00:00:00Z"])
def test_instante_invalido_nao_vira_agora_nem_persiste(aplicacao, valor):
    client = aplicacao.test_client()
    r = client.post("/api/clientes/5/interacoes", json={
        "canal": "email", "texto": "Contato", "ocorrida_em": valor})
    assert r.status_code == 400
    assert r.get_json()["erro"]["campo"] == "ocorrida_em"
    assert client.get("/api/clientes/5").get_json()["interacoes"] == []


@pytest.mark.parametrize("valor", ["20261009T120000-0300", "20261009T120000",
                                  "2026-10-09T12:00:00-03:00"])
def test_instante_iso_basico_e_estendido_preservam_ocorrencia(aplicacao, valor):
    client = aplicacao.test_client()
    r = client.post("/api/clientes/5/interacoes", json={
        "canal": "email", "texto": "Contato", "ocorrida_em": valor})
    assert r.status_code == 201
    assert r.get_json()["interacao"]["ocorrida_em"] == "2026-10-09T15:00:00.000000+00:00"


@pytest.mark.parametrize("valor", [7.0, True, "7", None, [7]])
def test_intervalo_invalido_nao_atualiza_outros_campos(aplicacao, valor):
    client = aplicacao.test_client()
    antes = client.get("/api/clientes/5").get_json()["cliente"]["preferencias"]
    r = client.patch("/api/clientes/5/preferencias", json={
        "canal_preferido": "telefone", "intervalo_minimo_dias": valor})
    assert r.status_code == 400
    assert r.get_json()["erro"]["campo"] == "intervalo_minimo_dias"
    assert client.get("/api/clientes/5").get_json()["cliente"]["preferencias"] == antes


@pytest.mark.parametrize("rota,metodo,status", [
    ("/api/inexistente", "get", 404),
    ("/api/clientes/abc", "get", 404),
    ("/api/clientes", "delete", 405),
])
def test_erro_de_roteamento_da_api_e_json(aplicacao, rota, metodo, status):
    r = getattr(aplicacao.test_client(), metodo)(rota)
    assert r.status_code == status
    assert r.is_json
    assert set(r.get_json()["erro"]) == {"codigo", "campo", "mensagem"}
