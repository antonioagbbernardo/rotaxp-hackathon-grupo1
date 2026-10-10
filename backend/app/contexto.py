"""Processamento incremental e supervisão persistida; não executa contatos."""
import hashlib
import json
from datetime import timedelta

from flask import current_app

from .clock import TZ, formatar_utc, parse_instante
from .contexto_rules import ErroContexto, PROMPT_VERSAO, texto, validar_revisao, validar_saida
from .db import get_db
from .fontes import consultar_fontes
from .ia_gemini import GeminiExtractor
from .rules import contato_pessoal_permitido
from .seed import ASSESSOR_ID


def _extrator():
    return current_app.config.get("EXTRATOR_IA") or GeminiExtractor(
        current_app.config.get("GEMINI_API_KEY"), current_app.config["GEMINI_MODEL"])


def _atuais(cid):
    return [d for d in consultar_fontes(cid) if d["atual"]]


def _novos(cid, modelo, fontes):
    processados = set()
    for row in get_db().execute(
        "SELECT documentos FROM processamento_contexto WHERE cliente_id=? AND modelo=? AND prompt_versao=? AND estado='concluido'",
        (cid, modelo, PROMPT_VERSAO)):
        processados.update(json.loads(row["documentos"]))
    return [d for d in fontes if d["tipo"] != 'nota_assessor' and d["id"] not in processados]


def processar(cid):
    db, clock, extrator = get_db(), current_app.config["CLOCK"], _extrator()
    agora = clock.agora()
    db.execute("BEGIN IMMEDIATE")
    try:
        ativo = db.execute("SELECT inicio_em FROM processamento_contexto WHERE cliente_id=? AND estado='em_processamento'",
                           (cid,)).fetchall()
        if any(parse_instante(r["inicio_em"]) > agora - timedelta(minutes=2) for r in ativo):
            raise ErroContexto("Já existe processamento em andamento para este cliente.", "cliente_id", 409)
        fontes = _atuais(cid)
        if not fontes:
            raise ErroContexto("Cliente sem fontes resolvidas para processar.", "fontes")
        novos = _novos(cid, extrator.modelo, fontes)
        if not novos:
            db.commit()
            return {"novos": 0, "documentos_processados": 0, "reutilizado": True}
        if sum(len(json.dumps(d["conteudo"], ensure_ascii=False)) for d in novos) > 40_000:
            raise ErroContexto("Fontes excedem 40 mil caracteres; nenhum conteúdo será truncado.", "fontes")
        ids = sorted(d["id"] for d in novos)
        assinatura = hashlib.sha256(json.dumps(ids).encode()).hexdigest()
        db.execute("UPDATE processamento_contexto SET estado='falhou', fim_em=? WHERE cliente_id=? AND estado='em_processamento'",
                   (formatar_utc(agora), cid))
        db.execute(
            "INSERT INTO processamento_contexto (cliente_id,modelo,prompt_versao,assinatura,documentos,estado,inicio_em)"
            " VALUES (?,?,?,?,?,'em_processamento',?) ON CONFLICT(cliente_id,modelo,prompt_versao,assinatura)"
            " DO UPDATE SET estado='em_processamento',inicio_em=excluded.inicio_em,fim_em=NULL",
            (cid, extrator.modelo, PROMPT_VERSAO, assinatura, json.dumps(ids), formatar_utc(agora)))
        pid = db.execute("SELECT id FROM processamento_contexto WHERE cliente_id=? AND modelo=? AND prompt_versao=? AND assinatura=?",
                         (cid, extrator.modelo, PROMPT_VERSAO, assinatura)).fetchone()[0]
        db.commit()
    except Exception:
        db.rollback()
        raise

    # A chamada externa não segura a transação SQLite.
    try:
        itens = validar_saida(extrator.extrair(novos), novos)
        db.execute("BEGIN IMMEDIATE")
        tentativa = db.execute("SELECT estado,inicio_em FROM processamento_contexto WHERE id=?", (pid,)).fetchone()
        if tentativa["estado"] != "em_processamento" or tentativa["inicio_em"] != formatar_utc(agora):
            raise ErroContexto("Tentativa substituída por outro processamento; recarregue.", "contexto", 409)
        if sorted(d["id"] for d in _atuais(cid)) != sorted(d["id"] for d in fontes):
            raise ErroContexto("Fontes mudaram durante a análise; processe novamente.", "fontes", 409)
        for item in itens:
            db.execute("INSERT INTO item_contexto (cliente_id,processamento_id,categoria,assunto,sujeito,tipo,valor_original,evidencias,gerado_em)"
                       " VALUES (?,?,?,?,?,?,?,?,?)", (cid, pid, item["categoria"], item["assunto"], item["sujeito"], item["tipo"],
                       item["valor"], json.dumps(item["evidencias"], ensure_ascii=False), formatar_utc(clock.agora())))
        db.execute("UPDATE processamento_contexto SET estado='concluido',fim_em=? WHERE id=?",
                   (formatar_utc(clock.agora()), pid))
        db.commit()
    except Exception:
        db.rollback()
        # Não invalida uma tentativa mais recente que retomou este lote.
        db.execute("UPDATE processamento_contexto SET estado='falhou',fim_em=? WHERE id=? AND inicio_em=? AND estado='em_processamento'",
                   (formatar_utc(clock.agora()), pid, formatar_utc(agora)))
        db.commit()
        raise
    return {"novos": len(itens), "documentos_processados": len(novos), "reutilizado": False}


def consultar(cid):
    db, clock, extrator = get_db(), current_app.config["CLOCK"], _extrator()
    fontes = {d["id"]: d for d in consultar_fontes(cid)}
    bloqueios = {r["assunto"]: bool(r["bloqueado"]) for r in db.execute("SELECT * FROM preferencia_assunto WHERE cliente_id=?", (cid,))}
    itens = [dict(r) for r in db.execute("SELECT i.*,p.modelo FROM item_contexto i JOIN processamento_contexto p ON p.id=i.processamento_id"
                                       " WHERE i.cliente_id=? ORDER BY i.id DESC", (cid,))]
    for item in itens:
        provas = json.loads(item["evidencias"])
        item["evidencia_atual"] = all(fontes.get(e["documento_id"], {}).get("atual", False) for e in provas)
        item["evidencias"] = [e | {k: fontes[e["documento_id"]][k] for k in ("origem", "registro_id", "versao", "ocorrida_em")}
                              for e in provas]
        item["historico_revisoes"] = [dict(r) for r in db.execute("SELECT * FROM revisao_contexto WHERE item_id=? ORDER BY revisao", (item["id"],))]
        item["bloqueado"] = bloqueios.get(item["assunto"], False)
        if item["estado"] == "adiado" and item["adiado_ate"] <= clock.hoje().isoformat():
            item["estado"] = "pendente"
        item["conflitos"] = []
    norm = lambda s: " ".join(s.casefold().split())
    for i in itens:
        if i["estado"] == "descartado" or (not i["evidencia_atual"] and i["estado"] not in ("confirmado", "corrigido")):
            continue
        for j in itens:
            if j["id"] == i["id"] or j["estado"] == "descartado":
                continue
            if not j["evidencia_atual"] and j["estado"] not in ("confirmado", "corrigido"):
                continue
            if all(i[k] == j[k] for k in ("categoria", "assunto", "sujeito")) and norm(i["valor_revisado"] or i["valor_original"]) != norm(j["valor_revisado"] or j["valor_original"]):
                i["conflitos"].append(j["id"])
    cliente = db.execute("SELECT * FROM cliente WHERE id=?", (cid,)).fetchone()
    ultimo = db.execute("SELECT MAX(ocorrida_em) FROM interacao WHERE cliente_id=?", (cid,)).fetchone()[0]
    pessoal = contato_pessoal_permitido(bool(cliente["permite_assuntos_pessoais"]), cliente["intervalo_minimo_dias"],
                                      parse_instante(ultimo).astimezone(TZ).date() if ultimo else None, clock.hoje())
    for i in itens:
        i["elegivel_contato"] = (i["estado"] in ("confirmado", "corrigido") and i["evidencia_atual"]
            and i["sujeito"] == "cliente" and not i["conflitos"] and not i["bloqueado"]
            and (pessoal or i["categoria"] not in ("interesse", "data_importante", "preferencia")))
    return {"itens": itens, "modelo": extrator.modelo,
            "configurado": bool(current_app.config.get("EXTRATOR_IA") or current_app.config.get("GEMINI_API_KEY")),
            "fontes_novas": len(_novos(cid, extrator.modelo, [d for d in fontes.values() if d["atual"]]))}


def revisar(cid, item_id, corpo):
    db, clock = get_db(), current_app.config["CLOCK"]
    db.execute("BEGIN IMMEDIATE")
    try:
        item = db.execute("SELECT * FROM item_contexto WHERE id=? AND cliente_id=?", (item_id, cid)).fetchone()
        if not item:
            raise ErroContexto("Item inexistente para este cliente.", "item_id", 404)
        r = validar_revisao(corpo, clock.hoje())
        if item["revisao"] != r["revisao"]:
            raise ErroContexto("Item já revisado; recarregue antes de decidir novamente.", "revisao", 409)
        estado = {"aprovar": "confirmado", "corrigir": "corrigido", "descartar": "descartado", "adiar": "adiado"}[r["acao"]]
        rev = item["revisao"] + 1
        # Só corrigir substitui valor humano; outras ações preservam a correção.
        valor = texto(r["valor"], "valor") if r["acao"] == "corrigir" else item["valor_revisado"]
        db.execute("UPDATE item_contexto SET estado=?,valor_revisado=?,revisao=?,adiado_ate=? WHERE id=?",
                   (estado, valor, rev, r.get("adiado_ate"), item_id))
        db.execute("INSERT INTO revisao_contexto (item_id,acao,motivo,valor,adiado_ate,assessor_id,revisao,revisada_em) VALUES (?,?,?,?,?,?,?,?)",
                   (item_id, r["acao"], r["motivo"].strip(), r.get("valor"), r.get("adiado_ate"), ASSESSOR_ID, rev, formatar_utc(clock.agora())))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"item_id": item_id, "revisao": rev, "estado": estado}


def alterar_assunto(cid, assunto, corpo):
    db = get_db()
    if not db.execute("SELECT 1 FROM item_contexto WHERE cliente_id=? AND assunto=?", (cid, assunto)).fetchone():
        raise ErroContexto("Assunto inexistente para este cliente.", "assunto", 404)
    if not isinstance(corpo, dict) or set(corpo) != {"bloqueado", "motivo"} or type(corpo["bloqueado"]) is not bool:
        raise ErroContexto("Informe bloqueado booleano e motivo.", "bloqueado")
    motivo = texto(corpo["motivo"], "motivo", 1000)
    with db:
        db.execute("INSERT INTO preferencia_assunto VALUES (?,?,?) ON CONFLICT(cliente_id,assunto) DO UPDATE SET bloqueado=excluded.bloqueado",
                   (cid, assunto, int(corpo["bloqueado"])))
        db.execute("INSERT INTO historico_assunto (cliente_id,assunto,bloqueado,motivo,assessor_id,registrada_em) VALUES (?,?,?,?,?,?)",
                   (cid, assunto, int(corpo["bloqueado"]), motivo, ASSESSOR_ID, formatar_utc(current_app.config["CLOCK"].agora())))
    return {"assunto": assunto, "bloqueado": corpo["bloqueado"]}
