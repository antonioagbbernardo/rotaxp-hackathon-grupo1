"""Agenda persistida e pauta determinística com fontes e revisão humana."""
import json
from datetime import timedelta
from hashlib import sha256

from flask import current_app

from . import noticias, pulse
from .agenda_rules import ErroAgenda, corpo, inicio, proxima, texto
from .clock import formatar_utc
from .db import get_db
from .seed import ASSESSOR_ID


def _obter(rid):
    if not 1 <= rid <= 2**63 - 1:
        raise ErroAgenda('Reunião inexistente.', 'reuniao_id', 404)
    r = get_db().execute('SELECT r.*,c.nome AS cliente_nome FROM reuniao r JOIN cliente c ON c.id=r.cliente_id WHERE r.id=?', (rid,)).fetchone()
    if r is None:
        raise ErroAgenda('Reunião inexistente.', 'reuniao_id', 404)
    return dict(r)


def _agendada(r):
    if r['estado'] != 'agendada':
        raise ErroAgenda('Esta ação exige uma reunião agendada.', 'estado', 409)


def _snapshot(r):
    c = get_db().execute('SELECT * FROM cliente WHERE id=?', (r['cliente_id'],)).fetchone()
    dados = pulse.montar_cliente(c, incluir_resumo_ia=False)
    itens = lambda registros: [{'texto': f['texto'], 'fontes': [pulse.referencia(f['fonte'])]} for f in registros]
    revisados = [i for i in dados['context']['itens'] if i['estado'] in ('confirmado', 'corrigido')
        and i['tipo'] == 'fato' and i['sujeito'] == 'cliente' and i['evidencia_atual'] and not i['conflitos'] and not i['bloqueado']
        and (i['elegivel_contato'] or i['categoria'] not in ('interesse', 'data_importante', 'preferencia'))]
    contexto = [{'texto': i['valor_revisado'] or i['valor_original'],
        'fontes': [f"documento #{e['documento_id']} · {e['origem']} · {e['registro_id']} v{e['versao']}" for e in i['evidencias']]} for i in revisados]
    combinados = [{'texto': i['proximos_passos'], 'fontes': [f"interacao #{i['id']} · {i['ocorrida_em']}"]}
        for i in dados['interactions'][:3] if i['proximos_passos']]
    pendencias = [{'texto': a['motivo'], 'fontes': [pulse.referencia(a['fonte'])]}
        for a in dados['alerts'] if a['estado'] == 'pendente']
    artigos = [{'texto': a['title'], 'fontes': [f"{a['source']} · publicação {a['publishedAt']} · coleta {a['collectedAt']}"],
        'url': a['url']} for a in dados['news']]
    avisos = json.loads(r['avisos_busca'])
    if dados['context']['fontes_novas']:
        avisos.append(f"{dados['context']['fontes_novas']} fonte(s) nova(s) aguardam análise do contexto.")
    if not dados['newsState']['configurado']:
        avisos.append('Integração de notícias indisponível; a pauta preserva os registros internos.')
    if not contexto:
        avisos.append('Nenhum contexto factual revisado disponível para esta pauta.')
    if not artigos:
        avisos.append('Nenhuma notícia elegível disponível; a pauta usa os registros internos.')
    for assunto in dados['newsState']['assuntos']:
        if assunto['estado'] != 'atualizado':
            avisos.append(f"Notícias de {assunto['nome']}: {assunto['estado']}. Última coleta: {assunto['ultima_coleta'] or 'ausente'}.")
    return {'objetivo': r['objetivo'], 'inicio_em': r['inicio_em'], 'dia': current_app.config['CLOCK'].hoje().isoformat(),
        'revisoes_contexto': [{'id': i['id'], 'revisao': i['revisao']} for i in revisados],
        'versoes_fontes': [{'id': f['id'], 'versao': f['versao']} for f in dados['sourceDocuments'] if f['atual']],
        'secoes': [
            {'titulo': 'Visão geral e relacionamento', 'itens': itens(dados['summaryFacts'])},
            {'titulo': 'Contexto confirmado', 'itens': contexto},
            {'titulo': 'Últimos combinados', 'itens': combinados},
            {'titulo': 'Pendências para revisar', 'itens': pendencias},
            {'titulo': 'Notícias para avaliar', 'itens': artigos},
            {'titulo': 'Perguntas sugeridas', 'itens': [
                {'texto': 'Seus objetivos ou necessidades mudaram desde o último contato?', 'fontes': []},
                {'texto': 'Quais próximos passos você gostaria de combinar?', 'fontes': []}]}],
        'avisos': avisos}


def _assinatura(dados):
    return sha256(json.dumps(dados, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _expor(r):
    assinatura = _assinatura(_snapshot(r))
    ultima = get_db().execute('SELECT * FROM pauta_reuniao WHERE reuniao_id=? ORDER BY id DESC LIMIT 1', (r['id'],)).fetchone()
    atual = get_db().execute('SELECT * FROM pauta_reuniao WHERE reuniao_id=? AND assinatura=?', (r['id'], assinatura)).fetchone()
    pauta = None
    if atual:
        pauta = {'id': atual['id'], 'gerada_em': atual['gerada_em'], **json.loads(atual['dados'])}
    resultado = get_db().execute('SELECT texto,proximos_passos,ocorrida_em FROM interacao WHERE id=?', (r['interacao_id'],)).fetchone() if r['interacao_id'] else None
    return {**r, 'proxima': r['estado'] == 'agendada' and proxima(r['inicio_em'], current_app.config['CLOCK'].agora()),
        'pauta': pauta, 'pauta_desatualizada': bool(ultima and not atual),
        'revisada': bool(atual and r['pauta_revisada_id'] == atual['id']), 'resultado': dict(resultado) if resultado else None}


def listar(cid=None):
    sql = 'SELECT id FROM reuniao' + (' WHERE cliente_id=?' if cid is not None else '') + ' ORDER BY inicio_em,id LIMIT 100'
    return {'reunioes': [_expor(_obter(r['id'])) for r in get_db().execute(sql, (cid,) if cid is not None else ()).fetchall()]}


def consultar(rid):
    return _expor(_obter(rid))


def criar(cid, entrada):
    b = corpo(entrada, ('objetivo', 'inicio_em'), ('objetivo', 'inicio_em'))
    objetivo, horario = texto(b['objetivo'], 'objetivo'), inicio(b['inicio_em'])
    db = get_db()
    cur = db.execute('INSERT INTO reuniao(cliente_id,assessor_id,objetivo,inicio_em,criada_em) VALUES (?,?,?,?,?)',
        (cid, ASSESSOR_ID, objetivo, horario, formatar_utc(current_app.config['CLOCK'].agora())))
    db.commit()
    return consultar(cur.lastrowid)


def editar(rid, entrada):
    b = corpo(entrada, ('objetivo', 'inicio_em', 'notas'))
    if not b:
        raise ErroAgenda('Informe ao menos um campo.', 'corpo')
    campos = {}
    for k, v in b.items():
        campos[k] = inicio(v) if k == 'inicio_em' else texto(v, k, 4000 if k == 'notas' else 500, vazio=k == 'notas')
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = _obter(rid)
        if any(k != 'notas' for k in campos):
            _agendada(r)
            campos['pauta_revisada_id'] = None
        db.execute('UPDATE reuniao SET ' + ','.join(f'{k}=?' for k in campos) + ' WHERE id=?', (*campos.values(), rid))
        db.commit()
    except Exception:
        db.rollback(); raise
    return consultar(rid)


def cancelar(rid):
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = _obter(rid)
        if r['estado'] != 'cancelada':
            _agendada(r)
            db.execute("UPDATE reuniao SET estado='cancelada' WHERE id=?", (rid,))
        db.commit()
    except Exception:
        db.rollback(); raise
    return consultar(rid)


def preparar(rid):
    r = _obter(rid)
    _agendada(r)
    avisos = []
    if proxima(r['inicio_em'], current_app.config['CLOCK'].agora()) and noticias.consultar(r['cliente_id'])['vinculos']:
        try:
            resultados = noticias.atualizar(r['cliente_id'], max_idade=timedelta(hours=2))['resultados']
            avisos = [f"Atualização antecipada de notícias não concluída: {v['erro']['mensagem']}" for v in resultados if v['estado'] == 'erro']
        except noticias.ErroNoticias as exc:
            avisos = [f'Atualização de notícias não concluída: {exc.mensagem}']
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = _obter(rid)
        _agendada(r)
        r['avisos_busca'] = json.dumps(avisos, ensure_ascii=False)
        db.execute('UPDATE reuniao SET avisos_busca=? WHERE id=?', (r['avisos_busca'], rid))
        dados = _snapshot(r)
        assinatura = _assinatura(dados)
        db.execute('INSERT OR IGNORE INTO pauta_reuniao(reuniao_id,assinatura,dados,gerada_em) VALUES (?,?,?,?)',
            (rid, assinatura, json.dumps(dados, ensure_ascii=False), formatar_utc(current_app.config['CLOCK'].agora())))
        db.commit()
    except Exception:
        db.rollback(); raise
    return consultar(rid)


def revisar(rid, entrada):
    b = corpo(entrada, ('pauta_id',), ('pauta_id',))
    if type(b['pauta_id']) is not int or not 1 <= b['pauta_id'] <= 2**63 - 1:
        raise ErroAgenda('Informe a versão da pauta.', 'pauta_id')
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = _obter(rid)
        _agendada(r)
        atual = _expor(r)['pauta']
        if not atual or atual['id'] != b['pauta_id']:
            raise ErroAgenda('Dados mudaram; prepare e confira a nova pauta.', 'pauta_id', 409)
        db.execute('UPDATE reuniao SET pauta_revisada_id=? WHERE id=?', (atual['id'], rid))
        db.commit()
    except Exception:
        db.rollback(); raise
    return consultar(rid)


def concluir(rid, entrada):
    b = corpo(entrada, ('resumo', 'proximos_passos'), ('resumo',))
    resumo = texto(b['resumo'], 'resumo', 4000)
    passos = texto(b.get('proximos_passos', ''), 'proximos_passos', 1000, vazio=True)
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = _obter(rid)
        status = 201
        if r['estado'] == 'concluida':
            anterior = db.execute('SELECT texto,proximos_passos FROM interacao WHERE id=?', (r['interacao_id'],)).fetchone()
            if (anterior['texto'], anterior['proximos_passos'] or '') != (resumo, passos):
                raise ErroAgenda('Reunião já concluída com outro resultado.', 'resumo', 409)
            status = 200
        else:
            _agendada(r)
            agora = formatar_utc(current_app.config['CLOCK'].agora())
            cur = db.execute("INSERT INTO interacao(cliente_id,canal,texto,ocorrida_em,registrada_em,proximos_passos,assessor_id) VALUES (?,'presencial',?,?,?,?,?)",
                (r['cliente_id'], resumo, agora, agora, passos, ASSESSOR_ID))
            db.execute("UPDATE reuniao SET estado='concluida',interacao_id=? WHERE id=?", (cur.lastrowid, rid))
        db.commit()
    except Exception:
        db.rollback(); raise
    return consultar(rid), status
