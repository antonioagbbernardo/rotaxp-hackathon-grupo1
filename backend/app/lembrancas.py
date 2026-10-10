"""Anotações de datas confirmadas, derivadas do contexto revisado e revogáveis."""
from datetime import date
import re

from flask import current_app

from . import contexto
from .agenda_rules import ErroAgenda, corpo, texto
from .clock import TZ, formatar_utc, parse_instante
from .db import get_db
from .rules import contato_pessoal_permitido, proxima_ocorrencia_aniversario
from .seed import ASSESSOR_ID


def _data(valor, campo='data'):
    try:
        if not isinstance(valor, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', valor):
            raise ValueError()
        return date.fromisoformat(valor)
    except ValueError:
        raise ErroAgenda('Informe uma data válida em YYYY-MM-DD.', campo) from None


def _candidatos(cid):
    c = get_db().execute('SELECT * FROM cliente WHERE id=?', (cid,)).fetchone()
    itens = contexto.consultar(cid)['itens']
    if not c['permite_assuntos_pessoais']:
        return {}
    return {i['id']: i for i in itens if i['categoria'] in ('data_importante', 'compromisso')
        and i['tipo'] == 'fato' and i['estado'] in ('confirmado', 'corrigido')
        and i['sujeito'] in ('cliente', 'familiar') and i['evidencia_atual'] and not i['conflitos'] and not i['bloqueado']}


def _fontes(i):
    return [f"documento #{e['documento_id']} · {e['origem']} · {e['registro_id']} v{e['versao']}" for e in i['evidencias']]


def _contato(cid):
    db, clock = get_db(), current_app.config['CLOCK']
    c = db.execute('SELECT * FROM cliente WHERE id=?', (cid,)).fetchone()
    ultimo = db.execute('SELECT ocorrida_em FROM interacao WHERE cliente_id=? ORDER BY ocorrida_em DESC,registrada_em DESC,id DESC LIMIT 1', (cid,)).fetchone()
    dia = parse_instante(ultimo['ocorrida_em']).astimezone(TZ).date() if ultimo else None
    return contato_pessoal_permitido(bool(c['permite_assuntos_pessoais']), c['intervalo_minimo_dias'], dia, clock.hoje())


def _expor(r, i, pode_contatar):
    hoje = current_app.config['CLOCK'].hoje()
    ocorrencia = proxima_ocorrencia_aniversario(r['dia'], r['mes'], hoje) if r['tipo'] == 'aniversario' else date.fromisoformat(r['data'])
    feedback = get_db().execute('SELECT * FROM feedback_lembranca WHERE lembranca_id=? AND revisao=? AND versao=? AND ocorrencia=? ORDER BY id DESC LIMIT 1',
        (r['id'], r['revisao'], r['versao'], ocorrencia.isoformat())).fetchone()
    estado, adiamento = 'pendente', None
    if feedback:
        if feedback['acao'] == 'adiar':
            adiamento = feedback['adiado_ate']
            if date.fromisoformat(adiamento) > hoje:
                estado = 'adiado'
        else:
            estado = 'concluido' if feedback['acao'] == 'concluir' else 'descartado'
    return {**dict(r), 'sujeito': i['sujeito'], 'fontes': _fontes(i), 'ocorrencia': ocorrencia.isoformat(),
        'estado': estado, 'adiado_ate': adiamento, 'proxima': estado == 'pendente' and (ocorrencia - hoje).days <= 7,
        'pode_contatar': pode_contatar, 'motivo_feedback': feedback['motivo'] if feedback else None}


def consultar(cid):
    candidatos = _candidatos(cid)
    contato = _contato(cid)
    rows = get_db().execute('SELECT * FROM lembranca_contexto WHERE cliente_id=? ORDER BY id', (cid,)).fetchall()
    lembrancas = [_expor(r, candidatos[r['item_id']], contato) for r in rows
        if r['item_id'] in candidatos and r['revisao'] == candidatos[r['item_id']]['revisao']]
    lembrancas.sort(key=lambda r: (r['ocorrencia'], r['id']))
    return {'candidatos': [{'id': i['id'], 'revisao': i['revisao'], 'valor': i['valor_revisado'] or i['valor_original'],
        'sujeito': i['sujeito'], 'fontes': _fontes(i)} for i in candidatos.values()], 'lembrancas': lembrancas}


def salvar(cid, entrada):
    b = corpo(entrada, ('item_id', 'revisao', 'tipo', 'descricao', 'data'), ('item_id', 'revisao', 'tipo', 'descricao', 'data'))
    for k in ('item_id', 'revisao'):
        if type(b[k]) is not int or not (1 if k == 'item_id' else 0) <= b[k] <= 2**63 - 1:
            raise ErroAgenda('Informe um inteiro válido.', k)
    if b['tipo'] not in ('aniversario', 'compromisso'):
        raise ErroAgenda('Escolha aniversário ou compromisso.', 'tipo')
    descricao, dia = texto(b['descricao'], 'descricao'), _data(b['data'])
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        if not db.execute('SELECT 1 FROM item_contexto WHERE id=? AND cliente_id=?', (b['item_id'], cid)).fetchone():
            raise ErroAgenda('Item inexistente para este cliente.', 'item_id', 404)
        item = _candidatos(cid).get(b['item_id'])
        if not item:
            raise ErroAgenda('Confira revisão, sujeito, evidência, bloqueio e permissão pessoal.', 'item_id')
        if item['revisao'] != b['revisao']:
            raise ErroAgenda('Item mudou; confirme a nova revisão.', 'revisao', 409)
        existente = db.execute('SELECT * FROM lembranca_contexto WHERE cliente_id=? AND item_id=?', (cid, b['item_id'])).fetchone()
        valores = (b['revisao'], b['tipo'], descricao, dia.isoformat() if b['tipo'] == 'compromisso' else None,
                   dia.day if b['tipo'] == 'aniversario' else None, dia.month if b['tipo'] == 'aniversario' else None)
        anterior = tuple(existente[k] for k in ('revisao', 'tipo', 'descricao', 'data', 'dia', 'mes')) if existente else None
        versao = existente['versao'] + int(valores != anterior) if existente else 1
        db.execute('INSERT INTO lembranca_contexto(cliente_id,item_id,revisao,tipo,descricao,data,dia,mes,assessor_id,confirmada_em,versao) VALUES (?,?,?,?,?,?,?,?,?,?,?) '
            'ON CONFLICT(cliente_id,item_id) DO UPDATE SET revisao=excluded.revisao,tipo=excluded.tipo,descricao=excluded.descricao,data=excluded.data,dia=excluded.dia,mes=excluded.mes,confirmada_em=excluded.confirmada_em,versao=excluded.versao',
            (cid, b['item_id'], b['revisao'], b['tipo'], descricao, dia.isoformat() if b['tipo'] == 'compromisso' else None,
             dia.day if b['tipo'] == 'aniversario' else None, dia.month if b['tipo'] == 'aniversario' else None,
             ASSESSOR_ID, formatar_utc(current_app.config['CLOCK'].agora()), versao))
        rid = db.execute('SELECT id FROM lembranca_contexto WHERE cliente_id=? AND item_id=?', (cid, b['item_id'])).fetchone()['id']
        db.commit()
    except Exception:
        db.rollback(); raise
    return {'id': rid}, 200 if existente else 201


def feedback(cid, rid, entrada):
    b = corpo(entrada, ('acao', 'motivo', 'adiado_ate'), ('acao', 'motivo'))
    if b['acao'] not in ('concluir', 'descartar', 'adiar'):
        raise ErroAgenda('Ação inválida.', 'acao')
    motivo = texto(b['motivo'], 'motivo', 1000)
    adiamento = ''
    if b['acao'] == 'adiar':
        data = _data(b.get('adiado_ate'), 'adiado_ate')
        if data <= current_app.config['CLOCK'].hoje():
            raise ErroAgenda('Adiamento exige data futura.', 'adiado_ate')
        adiamento = data.isoformat()
    elif 'adiado_ate' in b:
        raise ErroAgenda('Somente adiar aceita esta data.', 'adiado_ate')
    if not 1 <= rid <= 2**63 - 1:
        raise ErroAgenda('Lembrança inexistente.', 'lembranca_id', 404)
    db = get_db()
    db.execute('BEGIN IMMEDIATE')
    try:
        r = db.execute('SELECT * FROM lembranca_contexto WHERE id=? AND cliente_id=?', (rid, cid)).fetchone()
        if not r:
            raise ErroAgenda('Lembrança inexistente para este cliente.', 'lembranca_id', 404)
        item = _candidatos(cid).get(r['item_id'])
        if not item or item['revisao'] != r['revisao']:
            raise ErroAgenda('Lembrança precisa de nova confirmação.', 'item_id', 409)
        ocorrencia = _expor(r, item, _contato(cid))['ocorrencia']
        ultimo = db.execute('SELECT * FROM feedback_lembranca WHERE lembranca_id=? AND revisao=? AND versao=? AND ocorrencia=? ORDER BY id DESC LIMIT 1',
            (rid, r['revisao'], r['versao'], ocorrencia)).fetchone()
        if not ultimo or (ultimo['acao'], ultimo['motivo'], ultimo['adiado_ate']) != (b['acao'], motivo, adiamento):
            db.execute('INSERT INTO feedback_lembranca(lembranca_id,revisao,versao,ocorrencia,acao,motivo,adiado_ate,assessor_id,registrada_em) VALUES (?,?,?,?,?,?,?,?,?)',
                (rid, r['revisao'], r['versao'], ocorrencia, b['acao'], motivo, adiamento, ASSESSOR_ID, formatar_utc(current_app.config['CLOCK'].agora())))
        db.commit()
    except Exception:
        db.rollback(); raise
    return {'registrado': True}
