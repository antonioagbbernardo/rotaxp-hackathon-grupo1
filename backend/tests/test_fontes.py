import json
from datetime import datetime
from pathlib import Path

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db

AGORA = datetime(2026, 10, 10, 15, 0, tzinfo=TZ)


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "fontes.db"),
                      "CLOCK": relogio_fixo(AGORA)})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def documento(**campos):
    return {"registro_id": "conversa-01", "versao": 1, "cliente_id": 1,
            "tipo": "interacao", "canal": "whatsapp",
            "ocorrida_em": "2026-10-09T10:00:00-03:00",
            "conteudo": "Dados fictícios: acompanho Fórmula 1.", **campos}


def lote(*documentos):
    return {"origem": "teste-ficticio", "ficticio": True,
            "documentos": list(documentos) or [documento()]}


def importar(client, corpo):
    return client.post("/api/fontes/importar", json=corpo)


def fontes(client, cid=1):
    r = client.get(f"/api/clientes/{cid}/fontes")
    assert r.status_code == 200
    return r.get_json()["fontes"]


def test_importa_formulario_e_conversa_sem_alterar_decisoes_humanas(client):
    antes = client.get("/api/clientes/1").get_json()
    form = documento(registro_id="formulario-01", tipo="formulario",
                     conteudo={"aniversario": "12/10", "canal_preferido": "email"})
    form.pop("canal")
    r = importar(client, lote(form, documento()))
    assert r.status_code == 200
    assert r.get_json() == {"importados": 2, "reutilizados": 0, "pendentes": 0}
    docs = fontes(client)
    assert {d["tipo"] for d in docs} == {"formulario", "interacao"}
    assert all(d["atual"] and d["origem"] == "teste-ficticio" for d in docs)
    assert all(d["ocorrida_em"].endswith("+00:00") for d in docs)
    depois = client.get("/api/clientes/1").get_json()
    assert depois["cliente"] == antes["cliente"]
    assert depois["datas_importantes"] == antes["datas_importantes"]
    assert depois["historico_avaliacoes"] == antes["historico_avaliacoes"]
    assert len(depois["interacoes"]) == len(antes["interacoes"]) + 1
    assert set(i["id"] for i in antes["interacoes"]).issubset(i["id"] for i in depois["interacoes"])


def test_reimportacao_idempotente_apos_reinicio(app, client):
    assert importar(client, lote()).status_code == 200
    antes = client.get("/api/clientes/1").get_json()["interacoes"]
    nova = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"],
                       "CLOCK": relogio_fixo(AGORA)}).test_client()
    r = importar(nova, lote())
    assert r.status_code == 200
    assert r.get_json() == {"importados": 0, "reutilizados": 1, "pendentes": 0}
    assert nova.get("/api/clientes/1").get_json()["interacoes"] == antes
    assert len(fontes(nova)) == 1


@pytest.mark.parametrize("cid", [None, 999])
def test_identidade_nao_resolvida_fica_pendente_sem_interacao(client, cid):
    antes = client.get("/api/clientes/1").get_json()
    r = importar(client, lote(documento(cliente_id=cid, conteudo="Sou Ana Souza, dados fictícios.")))
    assert r.status_code == 200 and r.get_json()["pendentes"] == 1
    p = client.get("/api/fontes/pendencias")
    assert p.status_code == 200
    assert p.get_json()["pendencias"][0]["cliente_id"] is None
    assert p.get_json()["pendencias"][0]["interacao_id"] is None
    assert fontes(client) == []
    assert client.get("/api/clientes/1").get_json() == antes
    assert importar(client, lote(documento(cliente_id=cid, conteudo="Sou Ana Souza, dados fictícios."))).get_json()["reutilizados"] == 1


def test_fontes_isoladas_por_cliente(client):
    assert importar(client, lote(documento(), documento(registro_id="outra", cliente_id=2))).status_code == 200
    assert {f["cliente_id"] for f in fontes(client)} == {1}
    assert {f["cliente_id"] for f in fontes(client, 2)} == {2}
    assert client.get("/api/clientes/999/fontes").status_code == 404


def test_nova_versao_preserva_evidencia_sem_duplicar_interacao(client):
    importar(client, lote())
    id_interacao = fontes(client)[0]["interacao_id"]
    original = next(i for i in client.get("/api/clientes/1").get_json()["interacoes"] if i["id"] == id_interacao)
    r = importar(client, lote(documento(versao=2, conteudo="Correção fictícia: não acompanho Fórmula 1.")))
    assert r.status_code == 200
    docs = fontes(client)
    assert {d["versao"] for d in docs} == {1, 2}
    assert {d["interacao_id"] for d in docs} == {id_interacao}
    assert [d["versao"] for d in docs if d["atual"]] == [2]
    assert next(d for d in docs if d["versao"] == 1)["conteudo"] == documento()["conteudo"]
    atual = next(i for i in client.get("/api/clientes/1").get_json()["interacoes"] if i["id"] == id_interacao)
    assert atual["texto"].startswith("Correção fictícia")
    assert atual["registrada_em"] == original["registrada_em"]


def test_versao_antiga_chegando_depois_nao_reverte_historico(client):
    importar(client, lote(documento(versao=2, conteudo="Texto atual fictício")))
    assert importar(client, lote()).status_code == 200
    docs = fontes(client)
    assert [d["versao"] for d in docs if d["atual"]] == [2]
    i = next(i for i in client.get("/api/clientes/1").get_json()["interacoes"] if i["id"] == docs[0]["interacao_id"])
    assert i["texto"] == "Texto atual fictício"


@pytest.mark.parametrize("campos", [{"conteudo": "mudou sem versão"}, {"cliente_id": 2, "versao": 2},
                                   {"tipo": "formulario", "canal": None, "conteudo": {"a": "b"}, "versao": 2}])
def test_conflito_nao_grava_parte_do_lote(client, campos):
    importar(client, lote())
    antes = client.get("/api/clientes/1").get_json()["interacoes"]
    r = importar(client, lote(documento(registro_id="nao-deve-gravar"), documento(**campos)))
    assert r.status_code == 409
    assert r.get_json()["erro"]["campo"].startswith("documentos[1]")
    assert len(fontes(client)) == 1
    assert client.get("/api/clientes/1").get_json()["interacoes"] == antes


@pytest.mark.parametrize("campos,campo", [
    ({"canal": "sms"}, "canal"), ({"conteudo": " "}, "conteudo"),
    ({"conteudo": {}}, "conteudo"), ({"versao": True}, "versao"),
    ({"versao": 0}, "versao"), ({"versao": 1.5}, "versao"),
    ({"versao": 2 ** 63}, "versao"),
    ({"cliente_id": "Ana"}, "cliente_id"), ({"cliente_id": True}, "cliente_id"),
    ({"cliente_id": 2 ** 63}, "cliente_id"),
    ({"ocorrida_em": "amanhã"}, "ocorrida_em"),
    ({"ocorrida_em": "2026-10-11T10:00:00-03:00"}, "ocorrida_em"),
    ({"tipo": "desconhecido"}, "tipo"), ({"nome": "Ana"}, "nome"),
    ({"registro_id": ""}, "registro_id"),
])
def test_documento_invalido_nao_persiste_lote(client, campos, campo):
    r = importar(client, lote(documento(registro_id="valido"), documento(**campos)))
    assert r.status_code == 400
    assert r.get_json()["erro"]["campo"] == f"documentos[1].{campo}"
    assert fontes(client) == []


@pytest.mark.parametrize("corpo,campo", [
    ({"origem": "teste", "ficticio": False, "documentos": [documento()]}, "ficticio"),
    ({"origem": "", "ficticio": True, "documentos": [documento()]}, "origem"),
    ({"origem": "teste", "ficticio": True, "documentos": []}, "documentos"),
    ({"origem": "teste", "ficticio": True, "documentos": [documento()] * 101}, "documentos"),
])
def test_lote_invalido(client, corpo, campo):
    r = importar(client, corpo)
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == campo


def test_formulario_recusa_resposta_nao_textual(client):
    doc = documento(tipo="formulario", conteudo={"idade": 30})
    doc.pop("canal")
    r = importar(client, lote(doc))
    assert r.status_code == 400 and r.get_json()["erro"]["campo"] == "documentos[0].conteudo"


def test_mock_e_cli_com_tres_clientes_e_pendencias(app, client):
    arquivo = Path(__file__).resolve().parents[1] / "dados" / "fonte-demo.json"
    dados = json.loads(arquivo.read_text())
    assert dados["ficticio"] is True
    resultado = app.test_cli_runner().invoke(args=["importar-fontes", str(arquivo)])
    assert resultado.exit_code == 0, resultado.output
    assert all(fontes(client, cid) for cid in (1, 2, 3))
    assert len(client.get("/api/fontes/pendencias").get_json()["pendencias"]) == 2
    segundo = app.test_cli_runner().invoke(args=["importar-fontes", str(arquivo)])
    assert segundo.exit_code == 0 and '"importados": 0' in segundo.output


def test_reset_demo_remove_fontes_sem_quebrar_chaves_estrangeiras(app):
    importar(app.test_client(), lote())
    resultado = app.test_cli_runner().invoke(args=["reset-demo"])
    assert resultado.exit_code == 0, resultado.output
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM documento_fonte").fetchone()[0] == 0


def test_cli_json_invalido_nao_grava(app, tmp_path):
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text("{JSON inválido")
    resultado = app.test_cli_runner().invoke(args=["importar-fontes", str(arquivo)])
    assert resultado.exit_code != 0 and "JSON UTF-8 válido" in resultado.output
    assert fontes(app.test_client()) == []


def test_base_vazia_exige_seed_sem_erro_de_banco(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "vazia.db"),
                      "CLOCK": relogio_fixo(AGORA)})
    r = importar(app.test_client(), lote())
    assert r.status_code == 400 and "seed" in r.get_json()["erro"]["mensagem"]
