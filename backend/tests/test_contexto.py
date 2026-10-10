from copy import deepcopy
from datetime import datetime

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.contexto_rules import ErroContexto
from app.db import get_db
from app.seed import seed_db
from test_fontes import documento, lote

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


class ExtratorSimulado:
    modelo = "modelo-teste"

    def __init__(self):
        self.chamadas = []
        self.transformar = lambda itens: itens

    def extrair(self, documentos):
        self.chamadas.append(deepcopy(documentos))
        itens = []
        for d in documentos:
            campo = next(iter(d["conteudo"])) if d["tipo"] == "formulario" else None
            texto = d["conteudo"][campo] if campo else d["conteudo"]
            itens.append({"categoria": "interesse", "assunto": "formula-1", "sujeito": "cliente",
                          "tipo": "fato", "valor": texto,
                          "evidencias": [{"documento_id": d["id"], "trecho": texto, "campo": campo}]})
        return {"itens": self.transformar(itens)}


@pytest.fixture
def ambiente(tmp_path):
    extrator = ExtratorSimulado()
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "contexto.db"),
                      "CLOCK": relogio_fixo(AGORA), "EXTRATOR_IA": extrator, "GEMINI_API_KEY": ""})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    c = app.test_client()
    assert c.post("/api/fontes/importar", json=lote()).status_code == 200
    return app, c, extrator


def processar(c, cid=1):
    return c.post(f"/api/clientes/{cid}/contexto/processar")


def contexto(c, cid=1):
    r = c.get(f"/api/clientes/{cid}/contexto")
    assert r.status_code == 200
    return r.get_json()["itens"]


def revisar(c, item, **campos):
    return c.post(f"/api/clientes/1/contexto/{item['id']}/revisar",
                  json={"acao": "aprovar", "motivo": "Conferido pelo assessor fictício.",
                        "revisao": item["revisao"], **campos})


def test_ca48_somente_fontes_atuais_cliente_correto_e_sem_alterar_base(ambiente):
    app, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(versao=2), documento(registro_id="outro", cliente_id=2),
                                             documento(registro_id="pendente", cliente_id=None)))
    antes = c.get("/api/clientes/1").get_json()
    assert processar(c).get_json() == {"novos": 1, "documentos_processados": 1, "reutilizado": False}
    assert len(e.chamadas[0]) == 1 and e.chamadas[0][0]["versao"] == 2
    item = contexto(c)[0]
    assert item["estado"] == "pendente" and not item["elegivel_contato"]
    assert item["evidencias"][0]["origem"] == "teste-ficticio"
    assert c.get("/api/clientes/1").get_json() == antes
    assert contexto(c, 2) == []


def test_ca49_cache_novidades_e_correcao_persistem_apos_reinicio(ambiente):
    app, c, e = ambiente
    processar(c)
    item = contexto(c)[0]
    assert revisar(c, item, acao="corrigir", valor="Acompanha corridas ocasionalmente").status_code == 200
    assert processar(c).get_json()["reutilizado"] is True
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova", conteudo="Prefiro acompanhar futebol.")))
    assert processar(c).get_json()["documentos_processados"] == 1
    assert len(e.chamadas) == 2
    nova = create_app({**app.config, "DATABASE": app.config["DATABASE"]}).test_client()
    antigo = next(i for i in contexto(nova) if i["id"] == item["id"])
    assert antigo["estado"] == "corrigido" and antigo["valor_revisado"].startswith("Acompanha")
    assert antigo["valor_original"] == documento()["conteudo"]
    assert antigo["historico_revisoes"][0]["assessor_id"] == 1
    assert antigo["conflitos"] and not antigo["elegivel_contato"]


@pytest.mark.parametrize("mudanca", [
    {"evidencias": [{"documento_id": 999, "trecho": "inventado", "campo": None}]},
    {"evidencias": [{"documento_id": 1, "trecho": "inventado", "campo": None}]},
    {"evidencias": [{"documento_id": 1, "trecho": "Dados", "campo": "aniversario"}]},
    {"categoria": "humor"}, {"sujeito": "todos"}, {"tipo": "confirmado"},
    {"assunto": "Formula 1"}, {"valor": " "}, {"campo_extra": "x"},
])
def test_ca50_saida_invalida_nao_salva_parte_e_permite_retry(ambiente, mudanca):
    _, c, e = ambiente
    e.transformar = lambda itens: [itens[0], itens[0] | mudanca]
    r = processar(c)
    assert r.status_code == 502 and r.get_json()["erro"]["campo"]
    assert contexto(c) == []
    e.transformar = lambda itens: itens
    assert processar(c).status_code == 200


def test_ca52_formulario_e_familiar_nao_viram_dado_cliente(ambiente):
    _, c, e = ambiente
    c.post("/api/fontes/importar", json=lote(documento(registro_id="form", tipo="formulario", canal=None,
                                                       conteudo={"familia": "Minha filha faz aniversário em novembro."})))
    e.transformar = lambda itens: [itens[-1] | {"sujeito": "familiar", "categoria": "data_importante"}]
    assert processar(c).status_code == 200
    item = contexto(c)[0]
    assert revisar(c, item).status_code == 200
    assert not contexto(c)[0]["elegivel_contato"]


@pytest.mark.parametrize("acao,extras,estado", [("aprovar", {}, "confirmado"),
    ("corrigir", {"valor": "Corrigido"}, "corrigido"), ("descartar", {}, "descartado"),
    ("adiar", {"adiado_ate": "2026-10-11"}, "adiado")])
def test_ca51_acoes_humanas_e_adiamento(ambiente, acao, extras, estado):
    app, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    assert revisar(c, item, acao=acao, **extras).get_json()["estado"] == estado
    assert contexto(c)[0]["estado"] == estado
    if acao == "adiar":
        app.config["CLOCK"] = relogio_fixo(datetime(2026, 10, 11, 0, tzinfo=TZ))
        assert contexto(c)[0]["estado"] == "pendente"
        assert len(contexto(c)[0]["historico_revisoes"]) == 1


@pytest.mark.parametrize("campos", [{"motivo": " "}, {"revisao": True}, {"acao": "enviar"},
    {"acao": "corrigir", "valor": ""}, {"acao": "adiar", "adiado_ate": "2026-10-10"},
    {"acao": "adiar", "adiado_ate": "amanha"}, {"valor": "sem correcao"}, {"extra": "x"}])
def test_ca55_revisao_invalida_e_concorrencia(ambiente, campos):
    _, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    assert revisar(c, item, **campos).status_code == 400
    assert contexto(c)[0]["revisao"] == 0
    assert revisar(c, item).status_code == 200
    assert revisar(c, item).status_code == 409
    assert c.post(f"/api/clientes/2/contexto/{item['id']}/revisar", json={}).status_code == 404


def test_ca53_bloqueio_preserva_contexto_isola_cliente_e_descarte(ambiente):
    _, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    assert revisar(c, item).status_code == 200
    url = "/api/clientes/1/assuntos/formula-1"
    assert c.post(url, json={"bloqueado": True, "motivo": "Cliente não quer abordar."}).status_code == 200
    assert contexto(c)[0]["bloqueado"] and contexto(c)[0]["estado"] == "confirmado"
    assert c.post("/api/clientes/2/assuntos/formula-1", json={"bloqueado": True, "motivo": "x"}).status_code == 404
    assert c.post(url, json={"bloqueado": False, "motivo": "Cliente autorizou."}).status_code == 200
    assert not contexto(c)[0]["bloqueado"]
    assert revisar(c, contexto(c)[0], acao="descartar").status_code == 200
    assert not contexto(c)[0]["bloqueado"]


def test_ca55_fonte_muda_durante_chamada_e_preserva_revisao(ambiente):
    _, c, e = ambiente
    original = e.extrair
    def alterar(docs):
        resposta = original(docs)
        c.post("/api/fontes/importar", json=lote(documento(versao=2)))
        return resposta
    e.extrair = alterar
    assert processar(c).status_code == 409
    assert contexto(c) == []
    e.extrair = original
    assert processar(c).status_code == 200


def test_ca54_sem_chave_sem_fontes_ou_cliente_inexistente(ambiente):
    app, c, _ = ambiente
    app.config["EXTRATOR_IA"] = None
    assert processar(c).status_code == 503
    assert processar(c, 2).status_code == 400
    assert processar(c, 999).status_code == 404


def test_ca52_nova_versao_sinaliza_conflito_com_correcao_antiga(ambiente):
    _, c, _ = ambiente
    processar(c)
    antigo = contexto(c)[0]
    revisar(c, antigo, acao="corrigir", valor="Assessor conferiu que acompanha F1")
    c.post("/api/fontes/importar", json=lote(documento(versao=2, conteudo="Não acompanho mais F1.")))
    processar(c)
    itens = contexto(c)
    assert len(itens) == 2 and all(i["conflitos"] for i in itens)
    revisado = next(i for i in itens if i["id"] == antigo["id"])
    assert not revisado["evidencia_atual"] and revisado["estado"] == "corrigido"


def test_rn27_processamento_concorrente_e_retomada_abandonada(ambiente):
    app, c, e = ambiente
    original = e.extrair
    def concorrente(docs):
        assert processar(c).status_code == 409
        return original(docs)
    e.extrair = concorrente
    assert processar(c).status_code == 200
    c.post("/api/fontes/importar", json=lote(documento(registro_id="outra")))
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO processamento_contexto (cliente_id,modelo,prompt_versao,assinatura,documentos,estado,inicio_em)"
                   " VALUES (1,'teste','v0','abandonado','[]','em_processamento','2026-10-10T17:57:00+00:00')")
        db.commit()
    assert processar(c).status_code == 200


def test_ca54_falha_provedor_preserva_contexto_e_tentativa_nova(ambiente):
    _, c, e = ambiente
    processar(c)
    antes = contexto(c)
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova")))
    original = e.extrair
    def falhar(docs):
        raise ErroContexto("Cota indisponível.", "provedor", 503)
    e.extrair = falhar
    assert processar(c).status_code == 503
    assert contexto(c) == antes
    e.extrair = original
    assert processar(c).status_code == 200


def test_ca50_limite_sem_truncamento_e_corpo_nao_autorizado(ambiente):
    _, c, e = ambiente
    assert c.post("/api/clientes/1/contexto/processar", json={"modelo": "outro"}).status_code == 400
    c.post("/api/fontes/importar", json=lote(documento(registro_id="longa", conteudo="x" * 40_001)))
    assert processar(c).status_code == 400
    assert not e.chamadas and contexto(c) == []


def test_ca53_bloqueio_auditado_e_reset_isolado(ambiente):
    app, c, _ = ambiente
    processar(c)
    url = "/api/clientes/1/assuntos/formula-1"
    c.post(url, json={"bloqueado": True, "motivo": "Bloquear"})
    c.post(url, json={"bloqueado": False, "motivo": "Permitir"})
    with app.app_context():
        rows = get_db().execute("SELECT * FROM historico_assunto ORDER BY id").fetchall()
        assert [r["bloqueado"] for r in rows] == [1, 0]
        assert all(r["assessor_id"] == 1 for r in rows)
    resultado = app.test_cli_runner().invoke(args=["reset-demo"])
    assert resultado.exit_code == 0, resultado.output
    assert contexto(c) == []


def test_rn31_elegibilidade_exige_revisao_permissao_intervalo_e_assunto_livre(ambiente):
    app, c, _ = ambiente
    processar(c)
    item = contexto(c)[0]
    assert not item["elegivel_contato"]
    revisar(c, item)
    assert not contexto(c)[0]["elegivel_contato"]  # Último contato ontem.
    app.config["CLOCK"] = relogio_fixo(datetime(2026, 10, 16, 15, tzinfo=TZ))
    assert contexto(c)[0]["elegivel_contato"]  # Limite inclusivo de sete dias.
    c.patch("/api/clientes/1/preferencias", json={"permite_assuntos_pessoais": False})
    assert not contexto(c)[0]["elegivel_contato"]
    c.patch("/api/clientes/1/preferencias", json={"permite_assuntos_pessoais": True})
    c.post("/api/clientes/1/assuntos/formula-1", json={"bloqueado": True, "motivo": "Não abordar"})
    assert not contexto(c)[0]["elegivel_contato"]
    c.post("/api/clientes/1/assuntos/formula-1", json={"bloqueado": False, "motivo": "Permitir"})
    assert contexto(c)[0]["elegivel_contato"]


def test_ca48_evidencia_nao_pode_reutilizar_documento_fora_do_lote_novo(ambiente):
    _, c, e = ambiente
    processar(c)
    antes = contexto(c)
    prova_antiga = {k: antes[0]["evidencias"][0][k] for k in ("documento_id", "trecho", "campo")}
    c.post("/api/fontes/importar", json=lote(documento(registro_id="nova")))
    e.transformar = lambda itens: [itens[0] | {"evidencias": [prova_antiga]}]
    assert processar(c).status_code == 502
    assert contexto(c) == antes
