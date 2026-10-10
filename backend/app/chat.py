"""Conversa OpenAI por cliente; dados declarados são registrados automaticamente."""
import json
import re
import unicodedata
from datetime import timedelta
from uuid import UUID, uuid4

from flask import current_app

from .agenda_rules import ErroAgenda, corpo, texto
from .clock import formatar_utc, parse_instante
from .db import get_db
from .ia_openai import OpenAIChat
from .resumo_ia_rules import montar_entrada


def notas(cid):
    return [dict(r) for r in get_db().execute(
        'SELECT id,cliente_id,turno_id,texto,evidencia,registrada_em FROM nota_assessor WHERE cliente_id=? ORDER BY id DESC LIMIT 30', (cid,))]


def _expor(row):
    nota = get_db().execute('SELECT id FROM nota_assessor WHERE turno_id=?', (row['id'],)).fetchone()
    return {'id': row['id'], 'request_id': row['request_id'], 'pergunta': row['pergunta'],
            'resposta': row['resposta'], 'fontes': json.loads(row['fontes']),
            'nota_sugerida': row['nota_sugerida'], 'nota_id': nota['id'] if nota else None,
            'contexto_sugerido': json.loads(row['contexto_sugerido']),
            'criada_em': row['criada_em'], 'modo': 'openai'}


def consultar(cid):
    rows = get_db().execute("SELECT * FROM chat_turno WHERE cliente_id=? AND estado='concluido' ORDER BY id DESC LIMIT 30", (cid,)).fetchall()
    return {'configurado': bool(current_app.config.get('CHAT_OPENAI') or current_app.config['OPENAI_API_KEY']),
            'modelo': current_app.config['OPENAI_MODEL'], 'mensagens': [_expor(r) for r in reversed(rows)], 'notas': notas(cid)}


def _entrada(cliente):
    from . import reunioes, lembrancas
    entrada = montar_entrada(cliente, current_app.config['CLOCK'].hoje())
    fontes = {f['id']: f for f in entrada['fatos']}
    def adicionar(i, dado, fonte):
        fontes[i] = {'id': i, 'texto': dado, 'fonte': fonte}
    for r in cliente['interactions'][:8]:
        adicionar(f"interacao-{r['id']}", r['texto'] + ' Próximos passos: ' + (r['proximos_passos'] or ''),
                  f"interação #{r['id']} · {r['canal']} · {r['ocorrida_em']}")
    for r in notas(int(cliente['id'])):
        adicionar(f"nota-{r['id']}", r['texto'], f"nota do assessor #{r['id']} · {r['registrada_em']}")
    for n, r in enumerate(cliente['news']):
        adicionar(f'noticia-{n}', r['title'], f"{r['source']} · {r['url']} · {r['publishedAt']}")
    for r in reunioes.listar(int(cliente['id']))['reunioes']:
        adicionar(f"reuniao-{r['id']}", f"{r['objetivo']} · início {r['inicio_em']} · {r['estado']}",
                  f"reunião #{r['id']} · horário/objetivo registrados pelo assessor")
    for r in lembrancas.consultar(int(cliente['id']))['lembrancas']:
        adicionar(f"lembranca-{r['id']}", f"{r['descricao']} · {r['sujeito']} · {r['ocorrencia']} · {r['estado']}",
                  '; '.join(r['fontes']))
    entrada['fatos'] = list(fontes.values())
    entrada['relacionamento_humano'] = cliente['relationshipLabel']
    entrada['humor_inferido'] = cliente.get('mood')
    entrada['noticias_estado'] = cliente['newsState']['assuntos']
    return entrada, fontes


def responder(cliente, entrada):
    b = corpo(entrada, ('pergunta', 'request_id', 'interesse'), ('pergunta',))
    pergunta = texto(b['pergunta'], 'pergunta', 4000)
    interesse = texto(b['interesse'], 'interesse', 500) if 'interesse' in b else None
    if interesse is not None and pergunta != f'Adicionar interesse do cliente: {interesse}':
        raise ErroAgenda('A mensagem deve corresponder ao interesse declarado.', 'interesse')
    try:
        request_id = str(UUID(b.get('request_id', str(uuid4()))))
    except (ValueError, TypeError, AttributeError):
        raise ErroAgenda('Informe um UUID válido.', 'request_id') from None
    db, cid, clock = get_db(), int(cliente['id']), current_app.config['CLOCK']
    db.execute('BEGIN IMMEDIATE')
    try:
        anterior = db.execute('SELECT * FROM chat_turno WHERE cliente_id=? AND request_id=?', (cid, request_id)).fetchone()
        if anterior:
            if anterior['pergunta'] != pergunta:
                raise ErroAgenda('Identificador já usado em outra mensagem.', 'request_id', 409)
            if anterior['estado'] == 'concluido':
                db.commit()
                return _expor(anterior)
            if anterior['estado'] == 'processando' and parse_instante(anterior['criada_em']) > clock.agora() - timedelta(seconds=90):
                raise ErroAgenda('Esta resposta está sendo preparada. Aguarde e tente novamente.', 'request_id', 409)
            rid = anterior['id']
            db.execute("UPDATE chat_turno SET estado='processando',criada_em=? WHERE id=?", (formatar_utc(clock.agora()), rid))
        else:
            rid = db.execute("INSERT INTO chat_turno(cliente_id,request_id,pergunta,criada_em) VALUES (?,?,?,?)",
                (cid, request_id, pergunta, formatar_utc(clock.agora()))).lastrowid
        db.commit()
    except Exception:
        db.rollback(); raise
    try:
        fatos, fontes = _entrada(cliente)
        fontes['mensagem-atual'] = {'id': 'mensagem-atual', 'texto': pergunta,
            'fonte': f'mensagem do assessor no chat #{rid} · informação fornecida pelo assessor'}
        fatos['fatos'] = list(fontes.values())
        historico = db.execute("SELECT pergunta,resposta FROM chat_turno WHERE cliente_id=? AND estado='concluido' ORDER BY id DESC LIMIT 10", (cid,)).fetchall()
        mensagens = []
        for r in reversed(historico):
            mensagens.extend([{'role': 'user', 'content': r['pergunta']}, {'role': 'assistant', 'content': r['resposta']}])
        if interesse is not None:
            # Entrada explícita do assessor: não depende de a IA reconhecer uma frase nominal.
            from .contexto_chat import interesses_declarados
            propostas = interesses_declarados(interesse)
            if not propostas:
                propostas = []
                for termo in re.split(r',|;|\s+e\s+', interesse, flags=re.IGNORECASE)[:10]:
                    termo = termo.strip()
                    if not termo:
                        continue
                    norm = ''.join(c for c in unicodedata.normalize('NFD', termo.casefold()) if unicodedata.category(c) != 'Mn')
                    assunto = re.sub(r'[^a-z0-9]+', '-', norm).strip('-')[:80] or 'interesse-declarado'
                    propostas.append({'categoria': 'interesse', 'assunto': assunto, 'sujeito': 'cliente', 'valor': termo, 'trecho': termo})
            saida = {'resposta': f'Informação registrada: {interesse}.',
                'fontes': ['mensagem-atual'], 'nota_sugerida': interesse, 'contexto_sugerido': propostas}
        else:
            provedor = current_app.config.get('CHAT_OPENAI') or OpenAIChat(current_app.config['OPENAI_API_KEY'], current_app.config['OPENAI_MODEL'])
            saida = provedor.conversar(fatos, mensagens, pergunta)
            if isinstance(saida, dict) and isinstance(saida.get('contexto_sugerido', []), list) and not any(p.get('categoria') == 'interesse' for p in saida.get('contexto_sugerido', []) if isinstance(p, dict)):
                from .contexto_chat import interesses_declarados
                declarados = interesses_declarados(pergunta)
                if declarados:
                    saida['contexto_sugerido'] = (saida.get('contexto_sugerido') or []) + declarados
                    saida['nota_sugerida'] = pergunta[:1000]
        if (not isinstance(saida, dict) or set(saida) not in ({'resposta', 'fontes', 'nota_sugerida'}, {'resposta', 'fontes', 'nota_sugerida', 'contexto_sugerido'})
                or not isinstance(saida['resposta'], str) or not saida['resposta'].strip() or len(saida['resposta']) > 10000
                or not isinstance(saida['fontes'], list) or len(saida['fontes']) > 15
                or any(not isinstance(f, str) or f not in fontes for f in saida['fontes'])
                or (saida['nota_sugerida'] is not None and (not isinstance(saida['nota_sugerida'], str)
                    or not saida['nota_sugerida'].strip() or len(saida['nota_sugerida']) > 1000))):
            raise ErroAgenda('A IA retornou uma resposta inválida. Tente novamente.', 'chat', 502)
        from .contexto_chat import validar
        propostas = validar(saida.get('contexto_sugerido', []), pergunta)
        if propostas and not saida['nota_sugerida']:
            raise ErroAgenda('Contexto novo exige uma nota com a informação declarada.', 'contexto_sugerido', 502)
        referencias = list(dict.fromkeys(fontes[f]['fonte'] for f in saida['fontes']))
        db.execute("UPDATE chat_turno SET estado='concluido',resposta=?,fontes=?,nota_sugerida=?,contexto_sugerido=? WHERE id=?",
            (saida['resposta'].strip(), json.dumps(referencias, ensure_ascii=False), saida['nota_sugerida'], json.dumps(propostas, ensure_ascii=False), rid))
        if saida['nota_sugerida']:
            _salvar_nota(db, db.execute('SELECT * FROM chat_turno WHERE id=?', (rid,)).fetchone(), formatar_utc(clock.agora()))
        db.commit()
    except Exception:
        db.rollback()
        db.execute("UPDATE chat_turno SET estado='falhou' WHERE id=?", (rid,))
        db.commit()
        raise
    return _expor(db.execute('SELECT * FROM chat_turno WHERE id=?', (rid,)).fetchone())


def _salvar_nota(db, turno, agora):
    from .contexto_chat import registrar
    db.execute('INSERT OR IGNORE INTO nota_assessor(cliente_id,turno_id,texto,evidencia,registrada_em) VALUES (?,?,?,?,?)',
        (turno['cliente_id'], turno['id'], turno['nota_sugerida'], turno['pergunta'], agora))
    nota = db.execute('SELECT * FROM nota_assessor WHERE turno_id=?', (turno['id'],)).fetchone()
    registrar(db, turno, nota, agora)


def confirmar_nota(cid, rid):
    if not 1 <= rid <= 2**63 - 1:
        raise ErroAgenda('Mensagem inexistente.', 'turno_id', 404)
    db = get_db()
    r = db.execute("SELECT * FROM chat_turno WHERE id=? AND cliente_id=? AND estado='concluido'", (rid, cid)).fetchone()
    if not r:
        raise ErroAgenda('Mensagem inexistente para este cliente.', 'turno_id', 404)
    if not r['nota_sugerida']:
        raise ErroAgenda('Essa mensagem não contém uma nota para confirmar.', 'turno_id')
    db.execute('BEGIN IMMEDIATE')
    try:
        agora = formatar_utc(current_app.config['CLOCK'].agora())
        _salvar_nota(db, r, agora)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return _expor(r)
