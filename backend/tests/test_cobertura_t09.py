"""Testes dos critérios de T09 (CA40–CA56) que a suíte dos incrementos 01 e 02 protegia mal.

Rastreabilidade: README.md e especificações anteriores no histórico Git. Os casos vêm de
revisão independente e de mutação da aplicação; as expectativas vêm de
incrementos e contratos de especificação preservados no histórico Git, não da saída da aplicação.
"""
import json
from datetime import datetime, timedelta
from io import BytesIO
from urllib.error import HTTPError

import pytest
from client_autenticado import renovar_acesso

from app.clock import TZ, formatar_utc, relogio_fixo
from app.contexto_rules import ErroContexto
from app.db import get_db
from app.ia_gemini import GeminiExtractor
from test_contexto import AGORA, ambiente, contexto, processar, revisar  # noqa: F401 (fixture)
from test_fontes import app, client, documento, fontes, importar, lote  # noqa: F401 (fixtures)

MOTIVO = "Conferido pelo assessor fictício."
SEIS_DIAS_DEPOIS = datetime(2026, 10, 16, 15, tzinfo=TZ)  # intervalo de 7 dias já cumprido


def formulario(**campos):
    base = documento(registro_id="formulario-01", tipo="formulario", conteudo={"aniversario": "12/10"}, **campos)
    base.pop("canal")
    return base


def detalhe(client, cid=1):
    return client.get(f"/api/clientes/{cid}").get_json()


def interacao_por_id(client, interacao_id, cid=1):
    return next(i for i in detalhe(client, cid)["interacoes"] if i["id"] == interacao_id)


# ====================== Incremento 01: fontes ======================
def test_ca40_consulta_ordena_por_ocorrencia_decrescente(client):
    importar(client, lote(documento(registro_id="velha", ocorrida_em="2026-10-08T10:00:00-03:00"),
                          documento(registro_id="nova", ocorrida_em="2026-10-09T10:00:00-03:00")))
    assert [d["registro_id"] for d in fontes(client)] == ["nova", "velha"]


def test_ca40_conteudo_com_espacos_nas_pontas_volta_identico(client):
    importar(client, lote(documento(conteudo="  texto com bordas  ")))
    assert fontes(client)[0]["conteudo"] == "  texto com bordas  "


def test_ca41_reimportar_formulario_com_respostas_em_outra_ordem_nao_conflita(client):
    def enviar(corpo_json):  # corpo bruto: json= do cliente de teste reordena as chaves
        return client.post("/api/fontes/importar", data=corpo_json, content_type="application/json")
    base = ('{"origem": "teste-ficticio", "ficticio": true, "documentos": [{"registro_id": "f", "versao": 1,'
            ' "cliente_id": 1, "tipo": "formulario", "ocorrida_em": "2026-10-09T10:00:00-03:00",'
            ' "conteudo": %s}]}')
    assert enviar(base % '{"a": "1", "b": "2"}').status_code == 200
    r = enviar(base % '{"b": "2", "a": "1"}')
    assert r.status_code == 200
    assert r.get_json() == {"importados": 0, "reutilizados": 1, "pendentes": 0}


def test_ca42_pendencia_reutilizada_continua_contada_e_guarda_a_referencia(client):
    orfao = documento(registro_id="orfao", cliente_id=999)
    assert importar(client, lote(orfao)).get_json() == {"importados": 1, "reutilizados": 0, "pendentes": 1}
    assert importar(client, lote(orfao)).get_json() == {"importados": 0, "reutilizados": 1, "pendentes": 1}
    pendencia = client.get("/api/fontes/pendencias").get_json()["pendencias"][0]
    assert pendencia["cliente_referencia"] == 999 and pendencia["cliente_id"] is None
    assert pendencia["interacao_id"] is None


def test_ca43_versoes_fora_de_ordem_mantem_a_maior_e_arquivam_todas(client):
    for versao, texto in ((1, "texto v1"), (3, "texto v3"), (2, "texto v2")):
        r = importar(client, lote(documento(versao=versao, conteudo=texto)))
        assert r.get_json()["importados"] == 1
    docs = fontes(client)
    assert sorted(d["versao"] for d in docs) == [1, 2, 3]
    assert [d["versao"] for d in docs if d["atual"]] == [3]
    assert {d["interacao_id"] for d in docs} != {None} and len({d["interacao_id"] for d in docs}) == 1
    assert interacao_por_id(client, docs[0]["interacao_id"])["texto"] == "texto v3"


def test_ca43_nova_versao_atualiza_ocorrencia_e_preserva_registro(app, client):
    importar(client, lote(documento(conteudo="texto v1")))
    interacao_id = fontes(client)[0]["interacao_id"]
    antes = interacao_por_id(client, interacao_id)
    app.config["CLOCK"] = relogio_fixo(AGORA + timedelta(hours=1))
    importar(client, lote(documento(versao=2, conteudo="texto v2", ocorrida_em="2026-10-09T11:00:00-03:00")))
    depois = interacao_por_id(client, interacao_id)
    assert depois["texto"] == "texto v2" and depois["ocorrida_em"] != antes["ocorrida_em"]
    assert depois["registrada_em"] == antes["registrada_em"] == formatar_utc(AGORA)


@pytest.mark.parametrize("campos,campo", [
    ({"conteudo": "mudou"}, "documentos[1].versao"),
    ({"canal": "email"}, "documentos[1].versao"),
    ({"ocorrida_em": "2026-10-09T11:00:00-03:00"}, "documentos[1].versao"),
    ({"cliente_id": 2, "versao": 2}, "documentos[1].cliente_id"),
    ({"tipo": "formulario", "canal": None, "conteudo": {"a": "b"}, "versao": 2}, "documentos[1].tipo"),
])
def test_ca44_conflito_identifica_o_campo_e_nao_grava_o_lote(client, campos, campo):
    assert importar(client, lote(documento())).status_code == 200
    r = importar(client, lote(documento(registro_id="ok"), documento(**campos)))
    assert r.status_code == 409
    assert r.get_json()["erro"]["campo"] == campo
    assert [d["registro_id"] for d in fontes(client)] == ["conversa-01"]


@pytest.mark.parametrize("corpo", [
    {"origem": "x", "documentos": [documento()]},
    {"origem": "x", "ficticio": None, "documentos": [documento()]},
    {"origem": "x", "ficticio": "true", "documentos": [documento()]},
])
def test_ca45_lote_sem_marca_ficticia_verdadeira_e_recusado(client, corpo):
    r = importar(client, corpo)
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == "ficticio"
    assert fontes(client) == []


def test_ca45_lote_com_exatamente_100_documentos_e_aceito(client):
    docs = [documento(registro_id=f"doc-{n}") for n in range(100)]
    r = importar(client, lote(*docs))
    assert r.status_code == 200 and r.get_json()["importados"] == 100


def test_ca45_formulario_com_canal_e_recusado(client):
    r = importar(client, lote(documento(registro_id="f", tipo="formulario", conteudo={"a": "b"}, canal="email")))
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == "documentos[0].canal"
    assert fontes(client) == []


def test_ca46_importacao_preserva_interacoes_manuais_campo_a_campo(client):
    r = client.post("/api/clientes/1/interacoes", json={
        "canal": "telefone", "texto": "nota manual", "ocorrida_em": "2026-10-09T10:00:00-03:00",
        "proximos_passos": "Ligar de novo."})
    assert r.status_code == 201
    antes = detalhe(client)["interacoes"]
    importar(client, lote(documento(ocorrida_em="2026-10-09T10:00:00-03:00")))
    importar(client, lote(documento(versao=2, conteudo="v2", ocorrida_em="2026-10-09T10:00:00-03:00")))
    depois = detalhe(client)["interacoes"]
    assert all(i in depois for i in antes)
    assert len(depois) == len(antes) + 1


# ====================== Incremento 02: contexto ======================
def raw(c, cid=1):
    return c.get(f"/api/clientes/{cid}/contexto").get_json()


def inserir_tentativa(app, segundos_atras):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO processamento_contexto (cliente_id,modelo,prompt_versao,assinatura,documentos,estado,inicio_em)"
                   " VALUES (1,'modelo-teste','contexto-v1','abandonada','[]','em_processamento',?)",
                   (formatar_utc(AGORA - timedelta(seconds=segundos_atras)),))
        db.commit()


def test_ca49_tentativa_que_falhou_nao_conta_como_processada(ambiente):
    _, c, e = ambiente
    e.transformar = lambda itens: [itens[0] | {"categoria": "humor"}]
    assert processar(c).status_code == 502
    e.transformar = lambda itens: itens
    r = processar(c)
    assert r.status_code == 200
    assert r.get_json() == {"novos": 1, "documentos_processados": 1, "reutilizado": False}
    assert len(e.chamadas) == 2 and len(contexto(c)) == 1


def test_ca49_cache_e_separado_por_modelo(ambiente):
    _, c, e = ambiente
    processar(c)
    e.modelo = "outro-modelo"
    r = processar(c)
    assert r.get_json()["reutilizado"] is False and len(e.chamadas) == 2


def test_ca49_documento_novo_e_o_unico_enviado_na_segunda_chamada(ambiente):
    _, c, e = ambiente
    processar(c)
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova", conteudo="Prefiro futebol.")))
    processar(c)
    assert [d["registro_id"] for d in e.chamadas[1]] == ["nova"]


@pytest.mark.parametrize("segundos,status", [(90, 409), (150, 200)])
def test_rn27_fronteira_de_dois_minutos_para_retomar_tentativa(ambiente, segundos, status):
    app, c, _ = ambiente
    inserir_tentativa(app, segundos)
    assert processar(c).status_code == status


def test_rn27_processamento_concorrente_e_recusado_sem_recursao(ambiente):
    _, c, e = ambiente
    original, estado = e.extrair, {}

    def concorrente(docs):
        if "interno" not in estado:
            estado["interno"] = processar(c).status_code
        return original(docs)
    e.extrair = concorrente
    assert processar(c).status_code == 200
    assert estado["interno"] == 409


def test_ca55_tentativa_substituida_por_retomada_nao_grava_a_antiga(ambiente):
    app, c, e = ambiente
    original, estado = e.extrair, {}

    def retomada(docs):
        if "interno" not in estado:
            app.config["CLOCK"] = relogio_fixo(AGORA + timedelta(minutes=3))
            estado["interno"] = processar(c).status_code
        return original(docs)
    e.extrair = retomada
    assert processar(c).status_code == 409
    assert estado["interno"] == 200
    assert len(contexto(c)) == 1


def _item(itens, **mudancas):
    return [itens[0] | mudancas]


@pytest.mark.parametrize("transformar,campo", [
    (lambda itens: itens * 31, "itens"),
    (lambda itens: _item(itens, evidencias=[]), "itens[0].evidencias"),
    (lambda itens: _item(itens, evidencias=itens[0]["evidencias"] * 6), "itens[0].evidencias"),
    (lambda itens: _item(itens, assunto="a" * 81), "itens[0].assunto"),
    (lambda itens: _item(itens, valor="x" * 501), "itens[0].valor"),
    (lambda itens: _item(itens, evidencias=[itens[0]["evidencias"][0] | {
        "trecho": itens[0]["evidencias"][0]["trecho"].upper()}]), "itens[0].evidencias.trecho"),
    (lambda itens: _item(itens, evidencias=[itens[0]["evidencias"][0] | {"campo": "campo"}]),
     "itens[0].evidencias.campo"),
], ids=["31-itens", "0-evidencias", "6-evidencias", "slug-81", "valor-501", "trecho-caixa", "campo-em-conversa"])
def test_ca50_limites_e_literalidade_recusam_com_o_campo_certo(ambiente, transformar, campo):
    _, c, e = ambiente
    e.transformar = transformar
    r = processar(c)
    assert r.status_code == 502 and r.get_json()["erro"]["campo"] == campo
    assert contexto(c) == []


@pytest.mark.parametrize("transformar,total", [
    (lambda itens: itens * 30, 30),
    (lambda itens: _item(itens, evidencias=itens[0]["evidencias"] * 5), 1),
    (lambda itens: _item(itens, assunto="a" * 80), 1),
    (lambda itens: _item(itens, valor="x" * 500), 1),
    (lambda itens: [], 0),
], ids=["30-itens", "5-evidencias", "slug-80", "valor-500", "zero-itens"])
def test_ca50_limites_exatos_sao_aceitos(ambiente, transformar, total):
    _, c, e = ambiente
    e.transformar = transformar
    r = processar(c)
    assert r.status_code == 200 and r.get_json()["novos"] == total
    assert len(contexto(c)) == total


def test_ca50_campo_inexistente_em_formulario_e_recusado(ambiente):
    _, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(formulario()))
    e.transformar = lambda itens: [next(i for i in itens if i["evidencias"][0]["campo"]) | {
        "evidencias": [{"documento_id": next(i for i in itens if i["evidencias"][0]["campo"])["evidencias"][0]["documento_id"],
                        "trecho": "12/10", "campo": "inexistente"}]}]
    r = processar(c)
    assert r.status_code == 502 and r.get_json()["erro"]["campo"] == "itens[0].evidencias.campo"


def test_ca50_evidencia_de_documento_de_outro_cliente_e_recusada(ambiente):
    _, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="do-outro", cliente_id=2)))
    alheio = c.get("/api/clientes/2/fontes").get_json()["fontes"][0]
    e.transformar = lambda itens: [itens[0] | {"evidencias": [
        {"documento_id": alheio["id"], "trecho": "Dados", "campo": None}]}]
    r = processar(c)
    assert r.status_code == 502 and r.get_json()["erro"]["campo"] == "itens[0].evidencias.documento_id"


def test_ca51_historico_guarda_acao_motivo_versao_e_data_e_preserva_a_correcao(ambiente):
    _, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    assert revisar(c, item, acao="corrigir", valor="Corrigido pelo assessor").status_code == 200
    item = contexto(c)[0]
    assert revisar(c, item, acao="adiar", adiado_ate="2026-10-11").status_code == 200
    item = contexto(c)[0]
    assert item["estado"] == "adiado" and item["valor_revisado"] == "Corrigido pelo assessor"
    assert revisar(c, item).status_code == 200
    final = contexto(c)[0]
    assert final["estado"] == "confirmado" and final["valor_revisado"] == "Corrigido pelo assessor"
    historico = final["historico_revisoes"]
    assert [h["acao"] for h in historico] == ["corrigir", "adiar", "aprovar"]
    assert [h["revisao"] for h in historico] == [1, 2, 3]
    assert all(h["motivo"] == MOTIVO and h["assessor_id"] == 1 for h in historico)
    assert all(h["revisada_em"] == formatar_utc(AGORA) for h in historico)
    assert historico[0]["valor"] == "Corrigido pelo assessor"
    assert historico[1]["adiado_ate"] == "2026-10-11"


def test_ca51_item_pendente_nao_e_elegivel_nem_com_intervalo_cumprido(ambiente):
    app, c, e = ambiente
    e.transformar = lambda itens: _item(itens, categoria="objetivo")
    processar(c)
    app.config["CLOCK"] = relogio_fixo(SEIS_DIAS_DEPOIS)
    renovar_acesso(c)
    item = contexto(c)[0]
    assert item["estado"] == "pendente" and item["elegivel_contato"] is False
    assert revisar(c, item).status_code == 200
    assert contexto(c)[0]["elegivel_contato"] is True


@pytest.mark.parametrize("sujeito,esperado", [("cliente", True), ("familiar", False), ("terceiro", False),
                                              ("incerto", False)])
def test_ca52_so_item_sobre_o_cliente_pode_ser_elegivel(ambiente, sujeito, esperado):
    app, c, e = ambiente
    e.transformar = lambda itens: _item(itens, categoria="objetivo", sujeito=sujeito)
    processar(c)
    app.config["CLOCK"] = relogio_fixo(SEIS_DIAS_DEPOIS)
    renovar_acesso(c)
    item = contexto(c)[0]
    assert item["sujeito"] == sujeito
    assert revisar(c, item).status_code == 200
    assert contexto(c)[0]["elegivel_contato"] is esperado


def test_ca52_conflito_so_existe_entre_itens_do_mesmo_sujeito(ambiente):
    _, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="filha", conteudo="Minha filha gosta de F1.")))
    e.transformar = lambda itens: [itens[0] | {"sujeito": "cliente"}, itens[1] | {"sujeito": "familiar"}]
    processar(c)
    itens = contexto(c)
    assert len(itens) == 2 and {i["sujeito"] for i in itens} == {"cliente", "familiar"}
    assert all(i["conflitos"] == [] for i in itens)


def test_ca52_conflito_tira_a_elegibilidade_ate_o_descarte(ambiente):
    app, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="a", conteudo="Meta A: aposentar aos 55."),
                                             documento(registro_id="b", conteudo="Meta B: comprar um imóvel.")))
    e.transformar = lambda itens: [i | {"categoria": "objetivo"} for i in itens]
    processar(c)
    app.config["CLOCK"] = relogio_fixo(SEIS_DIAS_DEPOIS)
    renovar_acesso(c)
    for item in contexto(c):
        assert revisar(c, item).status_code == 200
    todos = contexto(c)
    assert len(todos) == 3 and all(i["conflitos"] and not i["elegivel_contato"] for i in todos)
    for item in todos[:2]:
        assert revisar(c, item, acao="descartar").status_code == 200
    restante = next(i for i in contexto(c) if i["estado"] == "confirmado")
    assert restante["conflitos"] == [] and restante["elegivel_contato"] is True


def test_ca52_evidencia_desatualizada_tira_a_elegibilidade(ambiente):
    app, c, e = ambiente
    e.transformar = lambda itens: _item(itens, categoria="objetivo")
    processar(c)
    app.config["CLOCK"] = relogio_fixo(SEIS_DIAS_DEPOIS)
    renovar_acesso(c)
    revisar(c, contexto(c)[0])
    assert contexto(c)[0]["elegivel_contato"] is True
    c.post("/api/fontes/importar", json=lote(documento(versao=2, conteudo="Mudou de ideia.")))
    item = contexto(c)[0]
    assert item["evidencia_atual"] is False and item["elegivel_contato"] is False


def test_ca52_evidencia_e_atual_somente_se_todas_as_fontes_forem_atuais(ambiente):
    _, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="b", conteudo="Segunda fonte.")))
    e.transformar = lambda itens: [itens[0] | {"evidencias": [i["evidencias"][0] for i in itens]}]
    processar(c)
    assert contexto(c)[0]["evidencia_atual"] is True
    c.post("/api/fontes/importar", json=lote(documento(registro_id="b", versao=2, conteudo="Segunda fonte v2.")))
    assert contexto(c)[0]["evidencia_atual"] is False


def test_ca53_bloqueio_de_um_cliente_nao_aparece_em_outro(ambiente):
    _, c, _ = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="c2", cliente_id=2)))
    processar(c)
    processar(c, 2)
    assert c.post("/api/clientes/1/assuntos/formula-1", json={"bloqueado": True, "motivo": "Evitar."}).status_code == 200
    assert contexto(c)[0]["bloqueado"] is True
    assert contexto(c, 2)[0]["bloqueado"] is False


def test_ca53_descartar_um_item_nao_descarta_nem_bloqueia_os_outros_do_assunto(ambiente):
    _, c, _ = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="b", conteudo="Outra conversa sobre F1.")))
    processar(c)
    itens = contexto(c)
    assert len(itens) == 2
    assert revisar(c, itens[0], acao="descartar").status_code == 200
    depois = {i["id"]: i for i in contexto(c)}
    assert depois[itens[0]["id"]]["estado"] == "descartado"
    assert depois[itens[1]["id"]]["estado"] == "pendente"
    assert not any(i["bloqueado"] for i in depois.values())


@pytest.mark.parametrize("corpo", [
    {"bloqueado": "sim", "motivo": "x"}, {"bloqueado": 1, "motivo": "x"},
    {"bloqueado": True, "motivo": "x", "extra": 1}, {"bloqueado": True}, {"bloqueado": True, "motivo": " "},
])
def test_ca53_bloqueio_invalido_nao_grava_historico(ambiente, corpo):
    app, c, _ = ambiente
    processar(c)
    r = c.post("/api/clientes/1/assuntos/formula-1", json=corpo)
    assert r.status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM historico_assunto").fetchone()[0] == 0
    assert contexto(c)[0]["bloqueado"] is False


def test_ca54_consulta_informa_fontes_novas_modelo_e_configuracao(ambiente):
    app, c, _ = ambiente
    antes = raw(c)
    assert antes["fontes_novas"] == 1 and antes["configurado"] is True and antes["modelo"] == "modelo-teste"
    processar(c)
    assert raw(c)["fontes_novas"] == 0
    app.config["EXTRATOR_IA"] = None
    assert raw(c)["configurado"] is False
    app.config["GEMINI_API_KEY"] = "chave-ficticia-local"
    resposta = c.get("/api/clientes/1/contexto")
    assert resposta.get_json()["configurado"] is True
    assert "chave-ficticia-local" not in resposta.get_data(as_text=True)


def test_ca54_falha_real_do_provedor_preserva_contexto_e_nao_repete_chamada(ambiente):
    app, c, _ = ambiente
    processar(c)
    antes = contexto(c)
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova")))
    chamadas = []

    def transporte(*args, **kwargs):
        chamadas.append(1)
        raise HTTPError("https://x", 429, "segredo-do-provedor", {}, None)
    app.config["EXTRATOR_IA"] = GeminiExtractor("chave-ficticia", transporte=transporte)
    r = processar(c)
    assert r.status_code == 503 and "chave-ficticia" not in r.get_data(as_text=True)
    assert "segredo-do-provedor" not in r.get_data(as_text=True)
    assert len(chamadas) == 1
    assert contexto(c) == antes


@pytest.mark.parametrize("campos,campo", [
    ({"motivo": " "}, "motivo"), ({"revisao": True}, "revisao"), ({"acao": "enviar"}, "acao"),
    ({"acao": "corrigir", "valor": ""}, "valor"), ({"acao": "adiar", "adiado_ate": "2026-10-10"}, "adiado_ate"),
    ({"acao": "adiar", "adiado_ate": "amanha"}, "adiado_ate"), ({"valor": "sem correcao"}, "acao"),
    ({"extra": "x"}, "acao"),
])
def test_ca55_revisao_invalida_identifica_o_campo(ambiente, campos, campo):
    _, c, _ = ambiente
    processar(c)
    r = revisar(c, contexto(c)[0], **campos)
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == campo


def test_ca55_item_de_outro_cliente_ou_inexistente_e_404_com_corpo_valido(ambiente):
    _, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    corpo = {"acao": "aprovar", "motivo": MOTIVO, "revisao": item["revisao"]}
    for url in (f"/api/clientes/2/contexto/{item['id']}/revisar", "/api/clientes/1/contexto/9999/revisar"):
        r = c.post(url, json=corpo)
        assert r.status_code == 404 and r.get_json()["erro"]["campo"] == "item_id"
    assert contexto(c)[0]["estado"] == "pendente"


def test_ca55_fonte_alterada_durante_a_chamada_preserva_item_ja_revisado(ambiente):
    _, c, e = ambiente
    processar(c)
    revisar(c, contexto(c)[0])
    antes = contexto(c)
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova")))
    original = e.extrair

    def alterar(docs):
        resposta = original(docs)
        c.post("/api/fontes/importar", json=lote(documento(registro_id="nova", versao=2)))
        return resposta
    e.extrair = alterar
    assert processar(c).status_code == 409
    assert contexto(c) == antes


def test_rn32_aprovar_contexto_nao_altera_resumo_nem_alertas_nem_datas(ambiente):
    _, c, e = ambiente
    e.transformar = lambda itens: _item(itens, categoria="data_importante", valor="Aniversário em 12/10")
    antes = detalhe(c)
    processar(c)
    assert revisar(c, contexto(c)[0]).status_code == 200
    depois = detalhe(c)
    assert depois["resumo"] == antes["resumo"] and depois["alertas"] == antes["alertas"]
    assert depois["datas_importantes"] == antes["datas_importantes"]
    assert depois["prioridade"] == antes["prioridade"]


# ====================== Provedor Gemini ======================
def _envelope(texto="{}", fim="STOP", extra=""):
    return json.dumps({"candidates": [{"finishReason": fim, "content": {"parts": [
        {"text": texto + extra}]}}]}).encode()


def test_ca54_corpo_bruto_nao_aparece_na_mensagem_de_resposta_invalida():
    for bruto in (b"nao json com segredo-bruto", _envelope(texto="segredo-bruto")):
        with pytest.raises(ErroContexto) as info:
            GeminiExtractor("chave", transporte=lambda *a, **k: BytesIO(bruto)).extrair([])
        assert "segredo-bruto" not in info.value.mensagem and info.value.status == 502


def test_ca54_resposta_valida_acima_de_1mb_e_recusada():
    grande = _envelope(texto=json.dumps({"itens": []}), extra=" " * 1_000_001)
    with pytest.raises(ErroContexto) as info:
        GeminiExtractor("chave", transporte=lambda *a, **k: BytesIO(grande)).extrair([])
    assert info.value.status == 502 and "limite" in info.value.mensagem


def test_ca54_cota_e_recusa_do_provedor_tem_mensagens_distintas():
    def com_codigo(codigo):
        def transporte(*a, **k):
            raise HTTPError("https://x", codigo, "x", {}, None)
        with pytest.raises(ErroContexto) as info:
            GeminiExtractor("chave", transporte=transporte).extrair([])
        return info.value.mensagem
    cota, recusa = com_codigo(429), com_codigo(403)
    assert "Cota" in cota and "Cota" not in recusa


def test_ca54_documentos_vao_como_dado_do_usuario_e_a_url_e_https_com_o_modelo():
    capturado = {}

    def transporte(req, timeout):
        capturado["url"], capturado["corpo"] = req.full_url, json.loads(req.data)
        capturado["metodo"] = req.get_method()
        return BytesIO(_envelope(texto=json.dumps({"itens": []})))
    GeminiExtractor("chave", modelo="modelo-x", transporte=transporte).extrair([
        {"id": 7, "tipo": "interacao", "canal": "email", "conteudo": "texto da fonte", "ocorrida_em": "x"}])
    assert capturado["url"].startswith("https://") and "models/modelo-x:" in capturado["url"]
    assert capturado["metodo"] == "POST"
    usuario = capturado["corpo"]["contents"][0]
    assert usuario["role"] == "user" and "texto da fonte" in usuario["parts"][0]["text"]
    assert "texto da fonte" not in json.dumps(capturado["corpo"]["systemInstruction"])
