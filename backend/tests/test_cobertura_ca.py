"""Testes dos critérios de aceite que a suíte principal cobria só em parte.

Rastreabilidade: docs/planejamento/rastreabilidade-testes.md. As expectativas
vêm do texto de spec.md/requisitos.md e do seed, não da saída da aplicação.
"""
from datetime import datetime, timedelta

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
    return app.test_client()


def app_em(caminho_banco: str, instante: datetime):
    """Nova instância sobre o mesmo banco, com outro instante no relógio."""
    return create_app({"TESTING": True, "DATABASE": caminho_banco, "CLOCK": relogio_fixo(instante)})


def contar(app, tabela: str, cliente_id: int | None = None) -> int:
    with app.app_context():
        if cliente_id is None:
            return get_db().execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        return get_db().execute(f"SELECT COUNT(*) FROM {tabela} WHERE cliente_id = ?", (cliente_id,)).fetchone()[0]


def ids_no_banco(app, tabela: str, cliente_id: int) -> set[int]:
    with app.app_context():
        return {r[0] for r in get_db().execute(f"SELECT id FROM {tabela} WHERE cliente_id = ?", (cliente_id,))}


def lista(client, **params):
    return client.get("/api/clientes", query_string=params).get_json()["clientes"]


def nomes(clientes):
    return [c["nome"].split()[0] for c in clientes]


# ---- CA02: abrir um cliente mostra somente suas posições, interações e preferências
@pytest.mark.parametrize(
    "cid,canal,intervalo,permite",
    [(1, "telefone", 7, True), (2, "email", 14, False), (4, None, 7, False)],
)
def test_ca02_detalhe_traz_exatamente_os_dados_e_preferencias_do_cliente(app, client, cid, canal, intervalo, permite):
    d = client.get(f"/api/clientes/{cid}").get_json()
    assert d["cliente"]["preferencias"] == {
        "canal_preferido": canal, "intervalo_minimo_dias": intervalo, "permite_assuntos_pessoais": permite}
    for chave, tabela in (("posicoes", "posicao"), ("interacoes", "interacao"), ("datas_importantes", "data_importante")):
        esperado = ids_no_banco(app, tabela, cid)
        assert {x["id"] for x in d[chave]} == esperado  # nem de outro cliente, nem faltando
        assert len(d[chave]) == len(esperado)
        assert contar(app, tabela) > len(esperado) or not esperado  # o banco tem dados de outros clientes


# ---- CA04: cliente inexistente não cria registro
def test_ca04_cliente_inexistente_recusa_sem_criar_registro(app, client):
    antes = contar(app, "interacao")
    r = client.post("/api/clientes/999/interacoes", json={"canal": "email", "texto": "x"})
    assert r.status_code == 404
    assert r.get_json()["erro"]["codigo"] == "nao_encontrado"
    assert contar(app, "interacao") == antes
    assert contar(app, "interacao", 999) == 0


# ---- CA09: alertas financeiros não alteram o relacionamento
def test_ca09_tratar_alertas_financeiros_nao_altera_avaliacao_existente(app, client):
    antes = client.get("/api/clientes/2").get_json()  # Bruno: avaliado 'atencao', com vencimentos
    assert antes["relacionamento"]["estado"] == "atencao"
    financeiros = [a for a in antes["alertas"] if a["regra"] == "vencimento" and a["estado"] == "pendente"]
    assert financeiros
    for a in financeiros:
        r = client.post("/api/alertas/tratar", json={"cliente_id": 2, "chave_ocorrencia": a["chave_ocorrencia"]})
        assert r.status_code == 201
    depois = client.get("/api/clientes/2").get_json()
    assert depois["relacionamento"] == antes["relacionamento"]
    assert depois["historico_avaliacoes"] == antes["historico_avaliacoes"]
    assert contar(app, "avaliacao_relacionamento", 2) == 1


def test_ca09_cliente_nao_avaliado_continua_sem_avaliacao_apos_alertas_e_passagem_do_tempo(app, client):
    ana = client.get("/api/clientes/1").get_json()
    assert ana["relacionamento"] is None
    alerta = next(a for a in ana["alertas"] if a["estado"] == "pendente")
    assert client.post("/api/alertas/tratar", json={"cliente_id": 1, "chave_ocorrencia": alerta["chave_ocorrencia"]}
                       ).status_code == 201
    depois_do_tempo = app_em(app.config["DATABASE"], AGORA + timedelta(days=45)).test_client()
    d = depois_do_tempo.get("/api/clientes/1").get_json()
    assert d["relacionamento"] is None and d["historico_avaliacoes"] == []
    assert contar(app, "avaliacao_relacionamento", 1) == 0


# ---- CA12: tratar a última pendência alta recalcula filtros, contagens e prioridade
def test_ca12_tratar_ultima_pendencia_alta_recalcula_filtros_contagens_e_prioridade(client):
    carla = next(c for c in lista(client) if c["nome"].startswith("Carla"))
    d = client.get("/api/clientes/3").get_json()
    altas = [a for a in d["alertas"] if a["estado"] == "pendente" and a["prioridade"] == "alta"]
    assert carla["prioridade"] == "alta" and len(altas) == 1  # a última pendência alta
    outras = carla["alertas_pendentes"] - 1
    assert outras >= 1  # restam pendências de menor prioridade
    assert "Carla" in nomes(lista(client, prioridade="alta"))
    assert "Carla" not in nomes(lista(client, prioridade="media"))

    r = client.post("/api/alertas/tratar", json={"cliente_id": 3, "chave_ocorrencia": altas[0]["chave_ocorrencia"]})
    assert r.status_code == 201

    depois = next(c for c in lista(client) if c["nome"].startswith("Carla"))
    assert depois["prioridade"] == "media"
    assert depois["alertas_pendentes"] == outras
    assert "Carla" not in nomes(lista(client, prioridade="alta"))
    assert "Carla" in nomes(lista(client, prioridade="media"))
    assert {"Ana", "Bruno"} <= set(nomes(lista(client, prioridade="alta")))  # os demais não mudam


# ---- CA35: no ano seguinte o aniversário é uma nova ocorrência
def test_ca35_aniversario_tratado_volta_como_nova_ocorrencia_pendente_no_ano_seguinte(app, client):
    ana = client.get("/api/clientes/1").get_json()
    aniv = next(a for a in ana["alertas"] if a["regra"] == "aniversario")
    assert aniv["ocorrencia"] == "2026-10-13" and aniv["estado"] == "pendente"
    assert client.post("/api/alertas/tratar", json={"cliente_id": 1, "chave_ocorrencia": aniv["chave_ocorrencia"]}
                       ).status_code == 201

    ano_seguinte = app_em(app.config["DATABASE"], datetime(2027, 10, 12, 12, 0, tzinfo=TZ)).test_client()
    alertas = [a for a in ano_seguinte.get("/api/clientes/1").get_json()["alertas"]
               if a["regra"] == "aniversario" and a["entidade_origem_id"] == aniv["entidade_origem_id"]]
    assert len(alertas) == 1
    novo = alertas[0]
    assert novo["ocorrencia"] == "2027-10-13"
    assert novo["chave_ocorrencia"] != aniv["chave_ocorrencia"]
    assert novo["estado"] == "pendente"
    assert contar(app, "tratamento_alerta") == 1  # o tratamento de 2026 permanece, só dele


# ---- CA36 / RN02: ordenação do histórico por ocorrência, depois por registro, depois por id
def test_ca36_reuniao_de_ontem_cadastrada_hoje_nao_fica_acima_de_conversa_de_hoje(app):
    banco = app.config["DATABASE"]
    conversa = app_em(banco, datetime(2026, 10, 10, 10, 0, tzinfo=TZ)).test_client()
    reuniao = app_em(banco, datetime(2026, 10, 10, 15, 0, tzinfo=TZ)).test_client()  # cadastrada depois
    assert conversa.post("/api/clientes/5/interacoes", json={
        "canal": "telefone", "texto": "conversa de hoje", "ocorrida_em": "2026-10-10T09:00:00-03:00"}).status_code == 201
    assert reuniao.post("/api/clientes/5/interacoes", json={
        "canal": "presencial", "texto": "reunião de ontem", "ocorrida_em": "2026-10-09T16:00:00-03:00"}).status_code == 201

    itens = reuniao.get("/api/clientes/5").get_json()["interacoes"]
    por_texto = {i["texto"]: i for i in itens}
    assert por_texto["reunião de ontem"]["registrada_em"] > por_texto["conversa de hoje"]["registrada_em"]
    assert [i["texto"] for i in itens] == ["conversa de hoje", "reunião de ontem"]


def test_rn02_empate_de_ocorrencia_desempata_por_registro_e_depois_por_id(app):
    banco = app.config["DATABASE"]
    mesma_ocorrencia = "2026-10-09T08:00:00-03:00"

    def registrar(instante, texto):
        c = app_em(banco, instante).test_client()
        r = c.post("/api/clientes/5/interacoes", json={"canal": "email", "texto": texto, "ocorrida_em": mesma_ocorrencia})
        assert r.status_code == 201

    registrar(datetime(2026, 10, 10, 10, 0, tzinfo=TZ), "A")
    registrar(datetime(2026, 10, 10, 11, 0, tzinfo=TZ), "B")
    registrar(datetime(2026, 10, 10, 11, 0, tzinfo=TZ), "C")  # mesmo registro que B: vale o id

    itens = app_em(banco, AGORA).test_client().get("/api/clientes/5").get_json()["interacoes"]
    assert [i["texto"] for i in itens] == ["C", "B", "A"]
