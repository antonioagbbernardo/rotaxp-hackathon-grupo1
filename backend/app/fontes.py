"""Adaptador JSON e persistência transacional de evidências versionadas."""
import json
from pathlib import Path

import click
from flask import current_app

from .clock import formatar_utc
from .db import get_db
from .fontes_rules import ErroFonte, validar_lote
from .seed import ASSESSOR_ID


def importar_lote(corpo) -> dict:
    agora = current_app.config["CLOCK"].agora()
    origem, documentos = validar_lote(corpo, agora)
    db = get_db()
    if not db.execute("SELECT 1 FROM assessor WHERE id = ?", (ASSESSOR_ID,)).fetchone():
        raise ErroFonte("Inicialize a base fictícia com o comando seed antes de importar.", "origem")
    resultado = {"importados": 0, "reutilizados": 0, "pendentes": 0}
    db.execute("BEGIN IMMEDIATE")
    try:
        for indice, doc in enumerate(documentos):
            p = f"documentos[{indice}]."
            anterior = db.execute(
                "SELECT * FROM documento_fonte WHERE origem = ? AND registro_id = ? ORDER BY versao DESC LIMIT 1",
                (origem, doc["registro_id"])).fetchone()
            if anterior:
                for campo in ("tipo", "cliente_referencia"):
                    if anterior[campo] != doc[campo]:
                        api_campo = "cliente_id" if campo == "cliente_referencia" else campo
                        raise ErroFonte("Registro não pode mudar de cliente ou tipo entre versões.", p + api_campo, 409)
            existente = db.execute(
                "SELECT * FROM documento_fonte WHERE origem = ? AND registro_id = ? AND versao = ?",
                (origem, doc["registro_id"], doc["versao"])).fetchone()
            if existente:
                if any(existente[campo] != doc[campo] for campo in doc):
                    raise ErroFonte("Conteúdo diverge da versão já importada. Envie uma nova versão.", p + "versao", 409)
                resultado["reutilizados"] += 1
                resultado["pendentes"] += existente["cliente_id"] is None
                continue
            conhecido = db.execute("SELECT id FROM cliente WHERE id = ?", (doc["cliente_referencia"],)).fetchone()
            cid = anterior["cliente_id"] if anterior else (conhecido["id"] if conhecido else None)
            interacao_id = anterior["interacao_id"] if anterior else None
            if cid is not None and doc["tipo"] == "interacao":
                texto = json.loads(doc["conteudo"])
                if interacao_id is None:
                    cur = db.execute(
                        "INSERT INTO interacao (cliente_id, canal, texto, ocorrida_em, registrada_em, assessor_id)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (cid, doc["canal"], texto, doc["ocorrida_em"], formatar_utc(agora), ASSESSOR_ID))
                    interacao_id = cur.lastrowid
                elif doc["versao"] > anterior["versao"]:
                    db.execute("UPDATE interacao SET canal = ?, texto = ?, ocorrida_em = ? WHERE id = ?",
                               (doc["canal"], texto, doc["ocorrida_em"], interacao_id))
            db.execute(
                "INSERT INTO documento_fonte (origem, registro_id, versao, cliente_referencia, cliente_id, tipo,"
                " canal, conteudo, ocorrida_em, importada_em, interacao_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (origem, doc["registro_id"], doc["versao"], doc["cliente_referencia"], cid, doc["tipo"],
                 doc["canal"], doc["conteudo"], doc["ocorrida_em"], formatar_utc(agora), interacao_id))
            resultado["importados"] += 1
            resultado["pendentes"] += cid is None
        db.commit()
    except Exception:
        db.rollback()
        raise
    return resultado


def consultar_fontes(cliente_id=None, *, pendentes=False) -> list[dict]:
    filtro = "f.cliente_id IS NULL" if pendentes else "f.cliente_id = ?"
    parametros = () if pendentes else (cliente_id,)
    rows = get_db().execute(
        "SELECT f.*, f.versao = (SELECT MAX(v.versao) FROM documento_fonte v"
        " WHERE v.origem = f.origem AND v.registro_id = f.registro_id) AS atual"
        f" FROM documento_fonte f WHERE {filtro}"
        " ORDER BY f.ocorrida_em DESC, f.origem, f.registro_id, f.versao DESC", parametros).fetchall()
    itens = []
    for row in rows:
        item = dict(row)
        item["conteudo"] = json.loads(item["conteudo"])
        item["atual"] = bool(item["atual"])
        itens.append(item)
    return itens


def init_app(app):
    @app.cli.command("importar-fontes")
    @click.argument("arquivo", type=click.Path(exists=True, dir_okay=False, path_type=Path))
    def importar_fontes_command(arquivo):
        """Importa um JSON fictício, sem sobrescrever decisões humanas."""
        try:
            corpo = json.loads(arquivo.read_text(encoding="utf-8"))
            resultado = importar_lote(corpo)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise click.ClickException("Não foi possível ler um arquivo JSON UTF-8 válido.") from exc
        except ErroFonte as exc:
            raise click.ClickException(f"{exc.campo}: {exc.mensagem}") from exc
        click.echo(json.dumps(resultado, ensure_ascii=False))
