"""Fluxo mínimo: data/sujeito confirmados, ocorrência e feedback isolado."""
from datetime import datetime, timedelta
import pytest

from app.clock import TZ, relogio_fixo
from app.db import get_db
from client_autenticado import renovar_acesso
from test_contexto import ambiente, processar, contexto, revisar

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


def candidato(ambiente, **extras):
    app, c, extrator = ambiente
    extrator.transformar = lambda itens: [i | {'categoria': 'data_importante', 'assunto': 'aniversario',
        'sujeito': 'familiar', **extras} for i in itens]
    assert processar(c).status_code == 200
    item = contexto(c)[0]
    assert revisar(c, item).status_code == 200
    return contexto(c)[0]


def salvar(c, item, **extras):
    return c.post('/api/clientes/1/lembrancas', json={'item_id': item['id'], 'revisao': item['revisao'],
        'tipo': 'aniversario', 'descricao': 'Aniversário de familiar (fictício)', 'data': '2026-10-13', **extras})


def test_ca91_data_sujeito_fonte_e_idempotencia(ambiente):
    app, c, _ = ambiente
    i = candidato(ambiente)
    a, b = salvar(c, i), salvar(c, i)
    assert a.status_code == 201 and b.status_code == 200
    lista = c.get('/api/clientes/1/lembrancas').get_json()
    assert lista['lembrancas'][0]['sujeito'] == 'familiar'
    assert lista['lembrancas'][0]['fontes'] and lista['lembrancas'][0]['ocorrencia'] == '2026-10-13'
    assert not lista['lembrancas'][0]['pode_contatar']  # contato recente; anotação não autoriza abordagem
    assert c.get('/api/clientes/2/lembrancas').get_json()['lembrancas'] == []
    resposta = c.post('/api/pulse/clientes/1/perguntar', json={'pergunta': 'Quais lembranças?'}).get_json()
    assert 'familiar' in resposta['resposta'] and '2026-10-13' in resposta['resposta'] and resposta['fontes']
    assert salvar(c, i, data='ontem').status_code == 400
    with app.app_context():
        row = get_db().execute('SELECT * FROM lembranca_contexto').fetchone()
        assert row['data'] is None and row['dia'] == 13 and row['mes'] == 10


@pytest.mark.parametrize('extras', [{'sujeito': 'terceiro'}, {'sujeito': 'incerto'}, {'tipo': 'hipotese'}])
def test_ca91_terceiro_ambiguidade_e_hipotese_recusados(ambiente, extras):
    _, c, _ = ambiente
    i = candidato(ambiente, **extras)
    assert salvar(c, i).status_code == 400
    assert c.get('/api/clientes/1/lembrancas').get_json()['candidatos'] == []


def test_ca92_recorrencia_e_compromisso_vencido(ambiente):
    app, c, _ = ambiente
    i = candidato(ambiente)
    salvar(c, i, data='2024-02-29')
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]['ocorrencia'] == '2027-02-28'
    salvar(c, i, tipo='compromisso', data='2026-10-09')
    r = c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]
    assert r['proxima'] and r['ocorrencia'] == '2026-10-09'


def test_ca93_feedback_adiamento_bloqueio_e_revisao(ambiente):
    app, c, _ = ambiente
    i = candidato(ambiente)
    rid = salvar(c, i).get_json()['id']
    caminho = f'/api/clientes/1/lembrancas/{rid}/feedback'
    body = {'acao': 'adiar', 'motivo': 'Retomar no próximo contato.', 'adiado_ate': '2026-10-12'}
    assert c.post(caminho, json=body).status_code == 200
    assert c.post(caminho, json=body).status_code == 200
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM feedback_lembranca').fetchone()[0] == 1
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]['estado'] == 'adiado'
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=2))
    renovar_acesso(c)
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]['estado'] == 'pendente'
    c.post('/api/clientes/1/assuntos/aniversario', json={'bloqueado': True, 'motivo': 'Não abordar.'})
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'] == []
    c.post('/api/clientes/1/assuntos/aniversario', json={'bloqueado': False, 'motivo': 'Reavaliado.'})
    revisar(c, contexto(c)[0], acao='corrigir', valor='Data corrigida pelo assessor.', motivo='Nova confirmação.')
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'] == []


def test_ca93_editar_anotacao_nao_reaplica_feedback_antigo(ambiente):
    _, c, _ = ambiente
    i = candidato(ambiente)
    rid = salvar(c, i).get_json()['id']
    assert c.post(f'/api/clientes/1/lembrancas/{rid}/feedback', json={'acao': 'concluir', 'motivo': 'Acompanhado.'}).status_code == 200
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]['estado'] == 'concluido'
    assert salvar(c, i, descricao='Outra descrição confirmada.').status_code == 200
    assert c.get('/api/clientes/1/lembrancas').get_json()['lembrancas'][0]['estado'] == 'pendente'
