"""Testes dos critérios de aceite que a suíte principal cobria só em parte.

Rastreabilidade: docs/planejamento/rastreabilidade-testes.md. As expectativas
vêm do texto de spec.md/requisitos.md e do seed, não da saída da aplicação.
"""
from datetime import UTC, date, datetime, timedelta

import pytest

from app import create_app
from app.clock import TZ, formatar_utc, relogio_fixo
from app.rules import classificar_vencimento
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
    alerta = next(a for a in ana["alertas"] if a["estado"] == "pendente" and a["regra"] == "vencimento")
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
    assert carla["alertas_pendentes"] == 3  # CRA (alta), LCA e aniversário da esposa (médias), conforme o seed
    assert "Carla" in nomes(lista(client, prioridade="alta"))
    assert "Carla" not in nomes(lista(client, prioridade="media"))

    r = client.post("/api/alertas/tratar", json={"cliente_id": 3, "chave_ocorrencia": altas[0]["chave_ocorrencia"]})
    assert r.status_code == 201

    depois = next(c for c in lista(client) if c["nome"].startswith("Carla"))
    assert depois["prioridade"] == "media"
    assert depois["alertas_pendentes"] == 2
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


def test_rn02_empate_de_ocorrencia_desempata_por_registro_mais_recente_e_nao_pelo_id(app):
    banco = app.config["DATABASE"]
    mesma_ocorrencia = "2026-10-09T08:00:00-03:00"

    def registrar(instante, texto):
        c = app_em(banco, instante).test_client()
        r = c.post("/api/clientes/5/interacoes", json={"canal": "email", "texto": texto, "ocorrida_em": mesma_ocorrencia})
        assert r.status_code == 201

    registrar(datetime(2026, 10, 10, 11, 0, tzinfo=TZ), "registrada-as-11h")  # id menor, registro mais recente
    registrar(datetime(2026, 10, 10, 10, 0, tzinfo=TZ), "registrada-as-10h")  # id maior, registro mais antigo

    itens = app_em(banco, AGORA).test_client().get("/api/clientes/5").get_json()["interacoes"]
    assert [i["texto"] for i in itens] == ["registrada-as-11h", "registrada-as-10h"]


def test_rn02_empate_total_desempata_pelo_id_mais_recente(app):
    banco = app.config["DATABASE"]
    c = app_em(banco, AGORA).test_client()
    for texto in ("primeira", "segunda"):
        assert c.post("/api/clientes/5/interacoes", json={
            "canal": "email", "texto": texto, "ocorrida_em": "2026-10-09T08:00:00-03:00"}).status_code == 201
    itens = c.get("/api/clientes/5").get_json()["interacoes"]
    assert [i["texto"] for i in itens] == ["segunda", "primeira"]


# ---- CA03/RN02: instantes automáticos e entrada sem fuso
def test_ca03_ocorrida_em_padrao_e_registrada_em_sao_o_instante_do_relogio(client):
    r = client.post("/api/clientes/5/interacoes", json={"canal": "email", "texto": "agora"})
    assert r.status_code == 201
    i = r.get_json()["interacao"]
    assert i["canal"] == "email"
    assert i["ocorrida_em"] == formatar_utc(AGORA) and i["registrada_em"] == formatar_utc(AGORA)


def test_rn02_registrada_em_e_automatica_mesmo_com_ocorrencia_anterior(client):
    i = client.post("/api/clientes/5/interacoes", json={
        "canal": "email", "texto": "ontem", "ocorrida_em": "2026-10-08T08:00:00-03:00"}).get_json()["interacao"]
    assert i["ocorrida_em"] == formatar_utc(datetime(2026, 10, 8, 11, 0, tzinfo=UTC))
    assert i["registrada_em"] == formatar_utc(AGORA)


def test_rn02_entrada_sem_fuso_e_horario_de_sao_paulo(client):
    # 16h sem fuso é 16h em São Paulo, depois das 15h do relógio: futuro, deve ser recusado.
    r = client.post("/api/clientes/5/interacoes", json={
        "canal": "email", "texto": "x", "ocorrida_em": "2026-10-10T16:00:00"})
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == "ocorrida_em"
    # 09h sem fuso é 12h UTC, gravado em UTC.
    i = client.post("/api/clientes/5/interacoes", json={
        "canal": "email", "texto": "x", "ocorrida_em": "2026-10-09T09:00:00"}).get_json()["interacao"]
    assert i["ocorrida_em"].startswith("2026-10-09T12:00:00") and i["ocorrida_em"].endswith("+00:00")


# ---- CA04: o erro identifica a entrada inválida
@pytest.mark.parametrize(
    "corpo,campo",
    [
        ({"canal": "sms", "texto": "x"}, "canal"),
        ({"canal": "email", "texto": "  "}, "texto"),
        ({"canal": "email", "texto": "x", "ocorrida_em": "2026-10-11T10:00:00-03:00"}, "ocorrida_em"),
        ({"canal": "email", "texto": "x", "ocorrida_em": "ontem"}, "ocorrida_em"),
    ],
)
def test_ca04_erro_identifica_o_campo_e_nada_e_criado(app, client, corpo, campo):
    antes = contar(app, "interacao")
    r = client.post("/api/clientes/5/interacoes", json=corpo)
    assert r.status_code == 400
    assert r.get_json()["erro"]["campo"] == campo
    assert contar(app, "interacao") == antes


# ---- CA05: vencido há muito tempo continua vencido, alta e com rótulo correto
@pytest.mark.parametrize("delta", [-31, -400])
def test_ca05_vencido_ha_mais_de_30_dias_continua_alta(delta):
    r = classificar_vencimento(HOJE + timedelta(days=delta), HOJE)
    assert (r["classificacao"], r["prioridade"], r["rotulo"]) == ("vencido", "alta", f"Vencido há {-delta} dias")


# ---- CA01: busca e filtros combinados, sem acento e sem resultado
def test_ca01_busca_ignora_acento_e_caixa(client):
    assert len(nomes(lista(client, q="ficticio"))) == 5
    assert len(nomes(lista(client, q="FICTÍCIO"))) == 5
    assert nomes(lista(client, q="souza")) == ["Ana"]
    assert lista(client, q="zzz") == []


def test_ca01_filtros_por_faixa_e_combinados_com_a_busca(client):
    assert nomes(lista(client, prioridade="alta")) == ["Bruno", "Ana", "Carla"]
    assert nomes(lista(client, prioridade="media")) == ["Diego"]
    assert nomes(lista(client, prioridade="baixa")) == ["Eva"]
    assert nomes(lista(client, q="a", prioridade="media")) == ["Diego"]  # todo nome do seed contém "a"
    assert nomes(lista(client, q="ana", prioridade="media")) == []


# ---- CA08/CA39: contagens absolutas do seed
CONTAGENS_SEED = {"Ana": 2, "Bruno": 2, "Carla": 3, "Diego": 1, "Eva": 0}


def test_ca39_contagens_do_seed_sao_estaveis_e_alertas_nao_se_repetem(app, client):
    def contagens():
        return {c["nome"].split()[0]: c["alertas_pendentes"] for c in lista(client)}

    assert contagens() == CONTAGENS_SEED
    for _ in range(5):
        lista(client)
        client.get("/api/clientes/1")
    assert contagens() == CONTAGENS_SEED
    chaves = [a["chave_ocorrencia"] for a in client.get("/api/clientes/1").get_json()["alertas"]]
    assert len(chaves) == 2 and len(set(chaves)) == 2
    assert contar(app, "tratamento_alerta") == 0


def test_ca08_tratar_um_alerta_reduz_a_contagem_do_seed_em_exatamente_um(client):
    bruno = client.get("/api/clientes/2").get_json()
    assert next(c for c in lista(client) if c["nome"].startswith("Bruno"))["alertas_pendentes"] == 2
    alerta = next(a for a in bruno["alertas"] if a["estado"] == "pendente")
    assert client.post("/api/alertas/tratar", json={
        "cliente_id": 2, "chave_ocorrencia": alerta["chave_ocorrencia"]}).status_code == 201
    assert next(c for c in lista(client) if c["nome"].startswith("Bruno"))["alertas_pendentes"] == 1
    assert {c["nome"].split()[0]: c["alertas_pendentes"] for c in lista(client)} == CONTAGENS_SEED | {"Bruno": 1}


# ---- CA07/RN13 de ponta a ponta: o intervalo vem do histórico real
def regras_do_cliente(client, cid):
    return [a["regra"] for a in client.get(f"/api/clientes/{cid}").get_json()["alertas"]]


def registrar(client, cid, **corpo):
    r = client.post(f"/api/clientes/{cid}/interacoes", json={"canal": "telefone", "texto": "contato"} | corpo)
    assert r.status_code == 201, r.get_data(as_text=True)


def test_ca07_contato_de_hoje_bloqueia_o_pessoal_e_mantem_o_financeiro(client):
    assert regras_do_cliente(client, 1) == ["aniversario", "vencimento"]
    registrar(client, 1)
    assert regras_do_cliente(client, 1) == ["vencimento"]


@pytest.mark.parametrize("dias_atras,aniversario_aparece", [(7, True), (6, False)])
def test_ca07_limite_do_intervalo_minimo_de_7_dias(client, dias_atras, aniversario_aparece):
    registrar(client, 1, ocorrida_em=(AGORA - timedelta(days=dias_atras)).isoformat())
    regras = regras_do_cliente(client, 1)
    assert ("aniversario" in regras) is aniversario_aparece
    assert "vencimento" in regras


def test_ca07_ultimo_contato_e_o_de_ocorrencia_mais_recente_nao_o_ultimo_registrado(client):
    # Ana falou há 10 dias (seed). Registrar hoje uma conversa antiga (há 20 dias) não renova o contato.
    registrar(client, 1, ocorrida_em=(AGORA - timedelta(days=20)).isoformat())
    assert "aniversario" in regras_do_cliente(client, 1)


def test_ca07_intervalo_das_preferencias_e_aplicado_e_financeiros_permanecem(client):
    antes = regras_do_cliente(client, 3)  # Carla: intervalo 14, último contato há 20 dias
    assert antes.count("aniversario") == 1 and antes.count("vencimento") == 2
    assert client.patch("/api/clientes/3/preferencias", json={"intervalo_minimo_dias": 30}).status_code == 200
    depois = regras_do_cliente(client, 3)
    assert depois.count("aniversario") == 0 and depois.count("vencimento") == 2


@pytest.mark.parametrize("ocorrida,aniversario_aparece", [
    ("2026-10-03T22:00:00-03:00", True),   # 7 dias no calendário local (já 04/10 em UTC)
    ("2026-10-04T22:00:00-03:00", False),  # 6 dias
])
def test_ca07_dia_do_ultimo_contato_e_o_dia_local_perto_da_meia_noite(app, ocorrida, aniversario_aparece):
    noite = app_em(app.config["DATABASE"], datetime(2026, 10, 10, 23, 30, tzinfo=TZ)).test_client()
    registrar(noite, 1, ocorrida_em=ocorrida)
    assert ("aniversario" in regras_do_cliente(noite, 1)) is aniversario_aparece


# ---- CA09/RN11: relacionamento e prioridade independentes nos dois sentidos
def test_ca09_tratar_alerta_nao_cria_avaliacao_para_cliente_nao_avaliado(app, client):
    antes = contar(app, "avaliacao_relacionamento")
    for cid in (1, 3):
        d = client.get(f"/api/clientes/{cid}").get_json()
        assert d["relacionamento"] is None
        for a in [a for a in d["alertas"] if a["estado"] == "pendente"]:
            assert client.post("/api/alertas/tratar", json={
                "cliente_id": cid, "chave_ocorrencia": a["chave_ocorrencia"]}).status_code == 201
        depois = client.get(f"/api/clientes/{cid}").get_json()
        assert depois["relacionamento"] is None and depois["historico_avaliacoes"] == []
    assert contar(app, "avaliacao_relacionamento") == antes


@pytest.mark.parametrize("cid,estado,prioridade_esperada", [
    (5, "negativo", "baixa"),   # Eva sem alertas: negativo não sobe
    (4, "negativo", "media"),   # Diego com só um vencimento futuro
    (2, "positivo", "alta"),    # Bruno com vencimentos: positivo não desce
])
def test_rn11_relacionamento_nao_altera_prioridade_em_nenhuma_faixa(client, cid, estado, prioridade_esperada):
    r = client.post(f"/api/clientes/{cid}/relacionamento", json={"estado": estado, "justificativa": "motivo"})
    assert r.status_code == 201
    assert client.get(f"/api/clientes/{cid}").get_json()["prioridade"] == prioridade_esperada
    assert next(c for c in lista(client) if c["id"] == cid)["prioridade"] == prioridade_esperada


def test_rn11_empate_de_faixa_e_data_desempata_pelo_nome(app, client):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO cliente (id, nome) VALUES (101, 'Zeca Empate (fictício)'), (102, 'Abel Empate (fictício)')")
        vencimento = (HOJE + timedelta(days=3)).isoformat()  # mesma pendência mais próxima da Ana (aniversário em 3 dias)
        for cid in (101, 102):
            db.execute("INSERT INTO posicao (cliente_id, ativo, valor, vencimento, fonte) VALUES (?, 'CDB Teste', '1000.00', ?, 'teste')",
                       (cid, vencimento))
        db.commit()
    assert nomes(lista(client, prioridade="alta")) == ["Bruno", "Abel", "Ana", "Zeca", "Carla"]


# ---- CA35: o tratamento vale só para aquela ocorrência
def test_ca35_aniversario_tratado_continua_tratado_dias_depois_no_mesmo_ano(app, client):
    aniv = next(a for a in client.get("/api/clientes/1").get_json()["alertas"] if a["regra"] == "aniversario")
    client.post("/api/alertas/tratar", json={"cliente_id": 1, "chave_ocorrencia": aniv["chave_ocorrencia"]})
    dois_dias_depois = app_em(app.config["DATABASE"], AGORA + timedelta(days=2)).test_client()
    mesmo = next(a for a in dois_dias_depois.get("/api/clientes/1").get_json()["alertas"]
                 if a["chave_ocorrencia"] == aniv["chave_ocorrencia"])
    assert mesmo["estado"] == "tratado"


# ---- CA37: cada fato aponta para registro real do mesmo cliente; ausência não vira conclusão
def _registro_da_fonte(app, tipo, id_fonte):
    tabela = {"cliente": "cliente", "posicao": "posicao", "interacao": "interacao",
              "avaliacao_relacionamento": "avaliacao_relacionamento"}[tipo]
    with app.app_context():
        return get_db().execute(f"SELECT * FROM {tabela} WHERE id = ?", (id_fonte,)).fetchone()


@pytest.mark.parametrize("cid", [1, 2, 3, 4])
def test_ca37_fonte_de_cada_fato_existe_e_pertence_ao_cliente(app, client, cid):
    fatos = client.get(f"/api/clientes/{cid}").get_json()["resumo"]["fatos"]
    assert fatos
    for f in fatos:
        fonte = f["fonte"]
        assert fonte["tipo_fonte"] and fonte["id_fonte"] not in (None, [], "")
        ids = fonte["id_fonte"] if isinstance(fonte["id_fonte"], list) else [fonte["id_fonte"]]
        for i in ids:
            row = _registro_da_fonte(app, fonte["tipo_fonte"], i)
            assert row is not None, f
            dono = row["id"] if fonte["tipo_fonte"] == "cliente" else row["cliente_id"]
            assert dono == cid, f


def test_ca37_fato_de_posicao_referencia_o_vencimento_do_registro(app, client):
    fatos = client.get("/api/clientes/1").get_json()["resumo"]["fatos"]
    individuais = [f for f in fatos if f["fonte"]["tipo_fonte"] == "posicao" and not isinstance(f["fonte"]["id_fonte"], list)]
    assert len(individuais) == 2
    for f in individuais:
        assert f["fonte"]["data_referencia"] == _registro_da_fonte(app, "posicao", f["fonte"]["id_fonte"])["vencimento"]


def test_ca37_ausencia_nao_vira_fato_nem_conclusao(client):
    eva = client.get("/api/clientes/5").get_json()["resumo"]
    assert eva["fatos"] == []
    assert {"Nenhuma posição cadastrada", "Nenhuma interação registrada", "Não avaliado"} <= set(eva["ausencias"])

    diego = client.get("/api/clientes/4").get_json()["resumo"]  # tem posição, nunca teve contato nem avaliação
    textos = [f["texto"] for f in diego["fatos"]]
    assert "Nenhuma interação registrada" in diego["ausencias"] and "Não avaliado" in diego["ausencias"]
    assert "Nenhuma posição cadastrada" not in diego["ausencias"]
    assert not any(t.startswith(("Último contato", "Próximos passos", "Relacionamento")) for t in textos)


def test_ca37_ultimo_contato_proximos_passos_e_relacionamento_aparecem_com_fonte(client):
    ana = client.get("/api/clientes/1").get_json()["resumo"]
    assert any(f["texto"] == "Próximos passos: Enviar opções de reinvestimento." for f in ana["fatos"])
    assert any(f["texto"].startswith("Último contato há 10 dia(s)") for f in ana["fatos"])
    assert not any(f["texto"].startswith("Relacionamento") for f in ana["fatos"])  # Ana não foi avaliada
    bruno = client.get("/api/clientes/2").get_json()["resumo"]
    assert any(f["texto"] == "Relacionamento: Atenção" for f in bruno["fatos"])


# ---- CA38: independência do dia real e do fuso; seed não altera base populada
def test_ca38_hoje_e_a_data_local_de_sao_paulo():
    assert relogio_fixo(datetime(2026, 10, 10, 22, 0, tzinfo=TZ)).hoje() == date(2026, 10, 10)  # já é 11/10 em UTC


def test_ca38_detalhe_e_tratamento_independem_do_dia_real(tmp_path):
    outro = datetime(2031, 3, 1, 12, 0, tzinfo=TZ)
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "x.db"), "CLOCK": relogio_fixo(outro)})
    with app.app_context():
        init_db()
        seed_db(outro.date(), outro)
    c = app.test_client()
    venc = [a for a in c.get("/api/clientes/2").get_json()["alertas"] if a["regra"] == "vencimento"]
    assert [a["rotulo"] for a in venc] == ["Vencido há 2 dias", "Vence hoje"]
    r = c.post("/api/alertas/tratar", json={"cliente_id": 2, "chave_ocorrencia": venc[0]["chave_ocorrencia"]})
    assert r.status_code == 201
    estados = {a["rotulo"]: a["estado"] for a in c.get("/api/clientes/2").get_json()["alertas"]}
    assert estados["Vencido há 2 dias"] == "tratado" and estados["Vence hoje"] == "pendente"


TABELAS = ("assessor", "cliente", "posicao", "data_importante", "interacao", "avaliacao_relacionamento",
           "tratamento_alerta")


def _dump(app):
    with app.app_context():
        db = get_db()
        return {t: [tuple(r) for r in db.execute(f"SELECT * FROM {t} ORDER BY 1")] for t in TABELAS}


def test_ca38_seed_nao_altera_nenhuma_tabela_de_base_populada(app, client):
    registrar(client, 5)
    client.patch("/api/clientes/1/preferencias", json={"intervalo_minimo_dias": 14})
    antes = _dump(app)
    with app.app_context():
        assert seed_db(HOJE + timedelta(days=40), AGORA + timedelta(days=40)) is False
    assert _dump(app) == antes
