"""Contexto declarado pelo assessor no chat, validado e salvo automaticamente."""
import json

from flask import current_app

from .contexto_rules import validar_saida
from .seed import ASSESSOR_ID


def validar(propostas, pergunta):
    if not isinstance(propostas, list) or len(propostas) > 10:
        from .agenda_rules import ErroAgenda
        raise ErroAgenda('Contexto sugerido inválido.', 'contexto_sugerido', 502)
    itens = []
    for p in propostas:
        if not isinstance(p, dict) or set(p) != {'categoria', 'assunto', 'sujeito', 'valor', 'trecho'}:
            from .agenda_rules import ErroAgenda
            raise ErroAgenda('Contexto sugerido inválido.', 'contexto_sugerido', 502)
        itens.append({k: p[k] for k in ('categoria', 'assunto', 'sujeito', 'valor')} | {
            'tipo': 'fato', 'evidencias': [{'documento_id': 0, 'campo': None, 'trecho': p['trecho']}]})
    validar_saida({'itens': itens}, [{'id': 0, 'tipo': 'nota_assessor', 'conteudo': pergunta}])
    return propostas


def registrar(db, turno, nota, agora):
    """Recebe a transação da nota: fonte, contexto e revisão são atômicos/idempotentes."""
    cid, rid = turno['cliente_id'], turno['id']
    registro = f'chat-{rid}'
    existente = db.execute('SELECT id FROM documento_fonte WHERE origem=? AND registro_id=?',
        ('chat-assessor', registro)).fetchone()
    if existente:
        return
    did = db.execute('INSERT INTO documento_fonte(origem,registro_id,versao,cliente_referencia,cliente_id,'
        'tipo,conteudo,ocorrida_em,importada_em) VALUES(?,?,1,?,?,?,?,?,?)',
        ('chat-assessor', registro, cid, cid, 'nota_assessor', json.dumps(turno['pergunta'], ensure_ascii=False),
         turno['criada_em'], agora)).lastrowid
    propostas = json.loads(turno['contexto_sugerido'])
    if not propostas:
        return
    pid = db.execute('INSERT INTO processamento_contexto(cliente_id,modelo,prompt_versao,assinatura,documentos,'
        'estado,inicio_em,fim_em) VALUES(?,?,?,?,?,?,?,?)', (cid, current_app.config['OPENAI_MODEL'],
        'contexto-chat-v1', registro, json.dumps([did]), 'concluido', agora, agora)).lastrowid
    for p in propostas:
        anteriores = db.execute("SELECT id,revisao FROM item_contexto WHERE cliente_id=? AND categoria=? "
            "AND assunto=? AND sujeito=? AND estado!='descartado'", (cid, p['categoria'], p['assunto'], p['sujeito'])).fetchall()
        for anterior in anteriores:
            rev = anterior['revisao'] + 1
            db.execute("UPDATE item_contexto SET estado='descartado',revisao=? WHERE id=?", (rev, anterior['id']))
            db.execute('INSERT INTO revisao_contexto(item_id,acao,motivo,assessor_id,revisao,revisada_em) VALUES(?,?,?,?,?,?)',
                (anterior['id'], 'descartar', f'Atualizado pela informação declarada no chat; nota #{nota["id"]}.', ASSESSOR_ID, rev, agora))
        provas = [{'documento_id': did, 'campo': None, 'trecho': p['trecho']}]
        iid = db.execute('INSERT INTO item_contexto(cliente_id,processamento_id,categoria,assunto,sujeito,tipo,'
            'valor_original,evidencias,gerado_em,estado,revisao) VALUES(?,?,?,?,?,?,?,?,?,?,1)',
            (cid, pid, p['categoria'], p['assunto'], p['sujeito'], 'fato', p['valor'],
             json.dumps(provas, ensure_ascii=False), agora, 'confirmado')).lastrowid
        db.execute('INSERT INTO revisao_contexto(item_id,acao,motivo,assessor_id,revisao,revisada_em) VALUES(?,?,?,?,1,?)',
            (iid, 'aprovar', f'Informação declarada diretamente pelo assessor no chat e registrada automaticamente; nota #{nota["id"]}.', ASSESSOR_ID, agora))
