from client_autenticado import cliente_autenticado
from datetime import date, datetime, timedelta

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db, init_db
from app.seed import seed_db

AGORA = datetime(2026, 10, 10, 15, 0, tzinfo=TZ)
HOJE = AGORA.date()


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db"), "CLOCK": relogio_fixo(AGORA)})
    with app.app_context():
        init_db()
        seed_db(HOJE, AGORA)
    return app


@pytest.fixture
def client(app):
    return cliente_autenticado(app)


def clientes(client, **params):
    return client.get("/api/clientes", query_string=params).get_json()["clientes"]


def por_nome(client, prefixo):
    return next(c for c in clientes(client) if c["nome"].startswith(prefixo))


# ---- lista / detalhe
def test_ca01_lista_ordenada_por_prioridade_pendencia_e_nome(client):
    lista = clientes(client)
    assert [c["nome"].split()[0] for c in lista] == ["Bruno", "Ana", "Carla", "Diego", "Eva"]
    assert [c["prioridade"] for c in lista] == ["alta", "alta", "alta", "media", "baixa"]


def test_ca01_busca_e_filtro(client):
    assert [c["nome"].split()[0] for c in clientes(client, q="ana")] == ["Ana"]
    assert [c["nome"].split()[0] for c in clientes(client, prioridade="baixa")] == ["Eva"]
    assert client.get("/api/clientes?prioridade=urgente").status_code == 400


def test_ca02_detalhe_somente_dados_do_cliente(client):
    d = client.get("/api/clientes/1").get_json()
    assert d["cliente"]["id"] == 1
    assert all(p["cliente_id"] == 1 for p in d["posicoes"] + d["interacoes"] + d["datas_importantes"])


def test_ca02_cliente_inexistente_404(client):
    r = client.get("/api/clientes/999")
    assert r.status_code == 404 and r.get_json()["erro"]["codigo"] == "nao_encontrado"


def test_ca05_posicao_com_delta_31_nao_gera_alerta_e_aniversario_sem_permissao_some(client):
    ana = client.get("/api/clientes/1").get_json()
    assert not any(a["entidade_origem_id"] == 2 and a["regra"] == "vencimento" for a in ana["alertas"])  # LCI Δ31
    bruno = client.get("/api/clientes/2").get_json()
    assert not any(a["regra"] == "aniversario" for a in bruno["alertas"])  # permite = 0


def test_ca37_resumo_com_fontes_e_ausencias(client):
    eva = client.get("/api/clientes/5").get_json()["resumo"]
    assert set(eva["ausencias"]) >= {"Nenhuma posição cadastrada", "Nenhuma interação registrada", "Não avaliado"}
    ana = client.get("/api/clientes/1").get_json()["resumo"]
    assert ana["fatos"] and all(f["fonte"]["tipo_fonte"] for f in ana["fatos"])


# ---- interações
def test_ca03_registrar_interacao_persiste_apos_reiniciar_aplicacao(app, client, tmp_path):
    r = client.post("/api/clientes/5/interacoes", json={"canal": "email", "texto": " Olá "})
    assert r.status_code == 201
    app2 = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"], "CLOCK": relogio_fixo(AGORA)})
    d = cliente_autenticado(app2).get("/api/clientes/5").get_json()
    assert [i["texto"] for i in d["interacoes"]] == ["Olá"]


@pytest.mark.parametrize(
    "corpo",
    [
        {"canal": "sms", "texto": "x"},
        {"canal": "email", "texto": "   "},
        {"canal": "email"},
        {"canal": "email", "texto": "x", "ocorrida_em": "2026-10-11T10:00:00-03:00"},
        {"canal": "email", "texto": "x", "ocorrida_em": "ontem"},
    ],
)
def test_ca04_interacao_invalida_nao_cria_registro(client, corpo):
    r = client.post("/api/clientes/5/interacoes", json=corpo)
    assert r.status_code == 400
    assert client.get("/api/clientes/5").get_json()["interacoes"] == []


def test_ca04_interacao_cliente_inexistente_404(client):
    assert client.post("/api/clientes/999/interacoes", json={"canal": "email", "texto": "x"}).status_code == 404


def test_ca36_historico_ordenado_por_ocorrencia_nao_por_registro(client):
    client.post("/api/clientes/5/interacoes", json={"canal": "telefone", "texto": "hoje",
                                                    "ocorrida_em": "2026-10-10T09:00:00-03:00"})
    client.post("/api/clientes/5/interacoes", json={"canal": "presencial", "texto": "ontem",
                                                    "ocorrida_em": "2026-10-09T09:00:00"})  # sem fuso = São Paulo
    textos = [i["texto"] for i in client.get("/api/clientes/5").get_json()["interacoes"]]
    assert textos == ["hoje", "ontem"]


# ---- tratar alerta
def alerta_pendente(client, cid):
    d = client.get(f"/api/clientes/{cid}").get_json()
    return next(a for a in d["alertas"] if a["estado"] == "pendente")


def test_ca08_tratar_alerta_reduz_pendencias_persiste_e_e_idempotente(app, client):
    antes = por_nome(client, "Bruno")["alertas_pendentes"]
    a = alerta_pendente(client, 2)
    corpo = {"cliente_id": 2, "chave_ocorrencia": a["chave_ocorrencia"]}
    assert client.post("/api/alertas/tratar", json=corpo).status_code == 201
    assert client.post("/api/alertas/tratar", json=corpo).status_code == 200  # idempotente
    assert por_nome(client, "Bruno")["alertas_pendentes"] == antes - 1
    app2 = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"], "CLOCK": relogio_fixo(AGORA)})
    c2 = cliente_autenticado(app2)
    d = c2.get("/api/clientes/2").get_json()
    assert next(x for x in d["alertas"] if x["chave_ocorrencia"] == a["chave_ocorrencia"])["estado"] == "tratado"
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM tratamento_alerta").fetchone()[0] == 1


def test_ca34_prioridade_recalculada_apos_tratar(client):
    carla = client.get("/api/clientes/3").get_json()
    altas = [a for a in carla["alertas"] if a["prioridade"] == "alta"]
    assert carla["prioridade"] == "alta" and len(altas) == 1
    client.post("/api/alertas/tratar", json={"cliente_id": 3, "chave_ocorrencia": altas[0]["chave_ocorrencia"]})
    assert client.get("/api/clientes/3").get_json()["prioridade"] == "media"


def test_ca08_tratar_chave_inexistente_ou_de_outro_cliente(client):
    chave_ana = alerta_pendente(client, 1)["chave_ocorrencia"]
    assert client.post("/api/alertas/tratar", json={"cliente_id": 2, "chave_ocorrencia": chave_ana}).status_code == 404
    assert client.post("/api/alertas/tratar", json={"cliente_id": 999, "chave_ocorrencia": "x"}).status_code == 404
    assert client.post("/api/alertas/tratar", json={"cliente_id": "1"}).status_code == 400


def test_ca39_atualizar_varias_vezes_nao_duplica_alertas(client):
    n = len(client.get("/api/clientes/1").get_json()["alertas"])
    for _ in range(5):
        client.get("/api/clientes")
    assert len(client.get("/api/clientes/1").get_json()["alertas"]) == n


# ---- relacionamento e preferências
def test_ca09_relacionamento_exige_justificativa_e_nao_altera_prioridade(client):
    antes = client.get("/api/clientes/1").get_json()
    assert client.post("/api/clientes/1/relacionamento", json={"estado": "negativo", "justificativa": " "}).status_code == 400
    assert client.post("/api/clientes/1/relacionamento", json={"estado": "otimo", "justificativa": "x"}).status_code == 400
    r = client.post("/api/clientes/1/relacionamento", json={"estado": "negativo", "justificativa": "Reclamou da taxa"})
    assert r.status_code == 201
    depois = client.get("/api/clientes/1").get_json()
    assert depois["relacionamento"]["estado"] == "negativo" and len(depois["historico_avaliacoes"]) == 1
    assert depois["prioridade"] == antes["prioridade"]


def test_ca14_preferencias_permissao_pessoal_remove_aniversario(client):
    antes = client.get("/api/clientes/1").get_json()["alertas"]
    assert any(a["regra"] == "aniversario" for a in antes)
    r = client.patch("/api/clientes/1/preferencias", json={"permite_assuntos_pessoais": False})
    assert r.status_code == 200
    depois = client.get("/api/clientes/1").get_json()["alertas"]
    assert not any(a["regra"] == "aniversario" for a in depois)
    assert any(a["regra"] == "vencimento" for a in depois)  # alertas financeiros permanecem


def test_rn13_preferencias_validam_entrada(client):
    assert client.patch("/api/clientes/1/preferencias", json={"intervalo_minimo_dias": 10}).status_code == 400
    assert client.patch("/api/clientes/1/preferencias", json={"canal_preferido": "sms"}).status_code == 400
    assert client.patch("/api/clientes/1/preferencias", json={"permite_assuntos_pessoais": "sim"}).status_code == 400


# ---- relógio e seed
def test_ca38_resultado_independe_do_dia_real(tmp_path):
    outro = datetime(2031, 3, 1, 12, 0, tzinfo=TZ)
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "x.db"), "CLOCK": relogio_fixo(outro)})
    with app.app_context():
        init_db()
        seed_db(outro.date(), outro)
    nomes = [c["nome"].split()[0] for c in cliente_autenticado(app).get("/api/clientes").get_json()["clientes"]]
    assert nomes == ["Bruno", "Ana", "Carla", "Diego", "Eva"]


def test_ca38_seed_nao_sobrescreve_base_populada(app):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE cliente SET nome = 'Alterado' WHERE id = 1")
        db.commit()
        assert seed_db(HOJE + timedelta(days=40), AGORA) is False
        assert db.execute("SELECT nome FROM cliente WHERE id = 1").fetchone()[0] == "Alterado"
        assert db.execute("SELECT COUNT(*) FROM cliente").fetchone()[0] == 5


def test_ca10_parcial_pagina_base_responde(client):
    assert client.get("/").status_code == 200
