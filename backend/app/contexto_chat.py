"""Contexto declarado pelo assessor no chat, validado e salvo automaticamente."""
import json
import re
import unicodedata

from flask import current_app

from .contexto_rules import ErroContexto, validar_saida
from .agenda_rules import ErroAgenda
from .seed import ASSESSOR_ID


def _norm(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if unicodedata.category(c) != 'Mn')


def declaracao_permitida(pergunta):
    """Guarda conservadora: conversar/perguntar não autoriza criar fatos."""
    norm = _norm(pergunta)
    return not ('?' in pergunta or re.search(
        r'\b(?:talvez|hipotetic\w*|exemplo|suponha|imagina|possivelmente|poderia|seria)\b', norm)
        or re.match(r'\s*(?:o que|como|qual|quais|quando|onde|por que|sera que|prepare|sugira|explique|me ajude)\b', norm))


def interesses_declarados(pergunta):
    """Reconhece declarações explícitas mesmo quando a IA omite a atualização."""
    if not declaracao_permitida(pergunta):
        return []
    itens = []
    for m in re.finditer(r'\b(?:gosta de|tem interesse em|tem interesse por|acompanha)\s+([^.!?\n]{1,150})', pergunta, re.IGNORECASE):
        prefixo = pergunta[max(0, m.start()-80):m.start()].casefold()
        if re.search(r'\b(?:eu|assessor|assistente)\s*$', prefixo):
            continue
        sujeito = 'familiar' if re.search(r'\b(?:filha|filho|esposa|marido|familia)\b', prefixo) else 'cliente'
        gosto = re.split(r'\s+e\s+(?:prefere|quer|precisa|pretende)\b', m.group(1), flags=re.IGNORECASE)[0].strip()
        slug = ''.join(c for c in unicodedata.normalize('NFD', gosto.casefold()) if unicodedata.category(c) != 'Mn')
        slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')[:80] or 'interesse-declarado'
        negado = bool(re.search(r'\b(?:não|nao)\s*$', prefixo))
        trecho = m.group(0)[:len(m.group(0)) - len(m.group(1))] + gosto
        if negado:
            trecho = pergunta[max(0, m.start()-4):m.start()] + trecho
        valor = trecho.strip()
        itens.append({'categoria': 'interesse', 'assunto': slug, 'sujeito': sujeito, 'valor': valor, 'trecho': trecho})
    return itens[:10]


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
    if not declaracao_permitida(pergunta):
        return []
    seguras = []
    for p in propostas:
        # Conferir a oração inteira impede citar só o fragmento positivo de uma negação.
        inicio = pergunta.find(p['trecho'])
        oracao = re.split(r'[.!?\n]', pergunta[:inicio])[-1] + p['trecho']
        negacao = bool(re.search(r'\b(?:nao|nunca|nem|deixou de|parou de)\b', _norm(oracao)))
        valor_negado = bool(re.search(r'\b(?:nao|nunca|nem|deixou de|parou de)\b', _norm(p['valor'])))
        if negacao != valor_negado:
            continue
        familiar = re.search(r'\b(?:filha|filho|esposa|marido|familia)\b', _norm(oracao))
        proprio_assessor = re.search(r'\b(?:eu|assessor|assistente)\s+(?:gost[oa]|acompanho|acompanha|prefiro|prefere)\b',_norm(oracao))
        if p['sujeito'] == 'cliente' and (familiar or proprio_assessor):
            continue
        seguras.append(p)
    return seguras


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


def revalidar_legado(db):
    """Quarentena auditada dos fatos antigos que eram perguntas/hipóteses/negações invertidas."""
    if db.execute("SELECT 1 FROM migracao_aplicada WHERE chave='contexto-chat-v3'").fetchone():
        return
    from .clock import formatar_utc
    agora=formatar_utc(current_app.config['CLOCK'].agora())
    for turno in db.execute("SELECT * FROM chat_turno WHERE estado='concluido'").fetchall():
        permitida=declaracao_permitida(turno['pergunta'])
        try:
            seguras=validar(json.loads(turno['contexto_sugerido']),turno['pergunta']) if permitida else []
        except (ValueError, TypeError, ErroContexto, ErroAgenda):
            seguras=[]
        db.execute('UPDATE nota_assessor SET validada=?,texto=? WHERE turno_id=?',
                   (int(permitida),turno['pergunta'][:1000],turno['id']))
        fonte=db.execute("SELECT id FROM documento_fonte WHERE origem='chat-assessor' AND registro_id=?",(f"chat-{turno['id']}",)).fetchone()
        if not fonte:
            continue
        for item in db.execute("SELECT i.* FROM item_contexto i JOIN processamento_contexto p ON p.id=i.processamento_id WHERE p.assinatura=?",(f"chat-{turno['id']}",)).fetchall():
            segura = any(all(item[k]==p[k] for k in ('categoria','assunto','sujeito')) and item['valor_original']==p['valor'] for p in seguras)
            ultima=db.execute('SELECT * FROM revisao_contexto WHERE item_id=? ORDER BY revisao DESC,id DESC LIMIT 1',(item['id'],)).fetchone()
            nossa_revisao=ultima and ultima['motivo'].startswith('Revalidação de contexto legado:')
            if item['estado']=='descartado':
                if segura and nossa_revisao:
                    # Corrigir uma quarentena conservadora sem reverter descartes humanos.
                    anterior=db.execute("SELECT acao FROM revisao_contexto WHERE item_id=? AND motivo NOT LIKE 'Revalidação de contexto legado:%' ORDER BY revisao DESC,id DESC LIMIT 1",(item['id'],)).fetchone()
                    if anterior and anterior['acao'] in ('aprovar','corrigir'):
                        db.execute('UPDATE item_contexto SET estado=?,revisao=? WHERE id=?',('corrigido' if anterior['acao']=='corrigir' else 'confirmado',item['revisao']+1,item['id']))
                        db.execute('INSERT INTO revisao_contexto(item_id,acao,motivo,assessor_id,revisao,revisada_em) VALUES(?,?,?,?,?,?)',
                            (item['id'],anterior['acao'],'Revalidação de contexto legado: declaração original preservada.',ASSESSOR_ID,item['revisao']+1,agora))
                continue
            if segura:
                continue
            rev=item['revisao']+1
            db.execute("UPDATE item_contexto SET estado='descartado',revisao=? WHERE id=?",(rev,item['id']))
            db.execute('INSERT INTO revisao_contexto(item_id,acao,motivo,assessor_id,revisao,revisada_em) VALUES(?,?,?,?,?,?)',
                (item['id'],'descartar','Revalidação de contexto legado: declaração não sustentada pela mensagem original.',ASSESSOR_ID,rev,agora))
    db.execute("INSERT OR IGNORE INTO migracao_aplicada VALUES('contexto-chat-v2')")
    db.execute("INSERT INTO migracao_aplicada VALUES('contexto-chat-v3')")
    db.commit()
