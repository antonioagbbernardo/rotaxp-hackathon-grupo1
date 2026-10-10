"""Verificações mínimas do fluxo completo e das fronteiras de custo."""
from datetime import datetime, timedelta
import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from client_autenticado import cliente_autenticado
from test_noticias import ambiente as noticias_env, aprovar, vincular, atualizar

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


@pytest.fixture
def ambiente(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'agenda.db'),
        'CLOCK': relogio_fixo(AGORA), 'OPENAI_API_KEY': '', 'GEMINI_API_KEY': '', 'NEWSAPI_API_KEY': ''})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app, cliente_autenticado(app)


def criar(c, cid=1, **extras):
    r = c.post(f'/api/clientes/{cid}/reunioes', json={'objetivo': 'Revisão fictícia da carteira',
                'inicio_em': (AGORA + timedelta(hours=2)).isoformat(), **extras})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_ca85_identidade_validacao_e_isolamento(ambiente):
    app, c = ambiente
    rid = criar(c)
    assert c.get('/api/clientes/2/reunioes').get_json()['reunioes'] == []
    assert c.get('/api/reunioes').get_json()['reunioes'][0]['id'] == rid
    resposta = c.post('/api/pulse/clientes/1/perguntar', json={'pergunta': 'Qual a próxima reunião?'}).get_json()
    assert 'Revisão fictícia da carteira' in resposta['resposta'] and resposta['fontes']
    assert 'Nenhuma reunião' in c.post('/api/pulse/clientes/2/perguntar', json={'pergunta': 'Agenda'}).get_json()['resposta']
    for extras, campo in [({'objetivo': ' '}, 'objetivo'), ({'inicio_em': 'ontem'}, 'inicio_em'), ({'extra': True}, 'extra')]:
        r = c.post('/api/clientes/1/reunioes', json={'objetivo': 'Revisar', 'inicio_em': AGORA.isoformat(), **extras})
        assert r.status_code == 400 and r.get_json()['erro']['campo'] == campo
    assert c.post('/api/clientes/999/reunioes', json={}).status_code == 404
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM reuniao').fetchone()[0] == 1


def test_ca86_pauta_fontes_reuso_revisao_e_notas_preservadas(ambiente):
    _, c = ambiente
    rid = criar(c)
    c.patch(f'/api/reunioes/{rid}', json={'notas': 'Perguntar sobre planos de viagem.'})
    a = c.post(f'/api/reunioes/{rid}/preparar').get_json()
    assert a['pauta']['secoes'] and a['pauta']['avisos']
    assert any(i['fontes'] for s in a['pauta']['secoes'] for i in s['itens'])
    b = c.post(f'/api/reunioes/{rid}/preparar').get_json()
    assert a['pauta']['id'] == b['pauta']['id']
    assert c.post(f'/api/reunioes/{rid}/revisar', json={'pauta_id': a['pauta']['id']}).get_json()['revisada']
    c.post('/api/clientes/1/interacoes', json={'canal': 'telefone', 'texto': 'Combinado fictício novo.'})
    atual = c.get(f'/api/reunioes/{rid}').get_json()
    assert atual['pauta_desatualizada'] and not atual['revisada'] and atual['pauta'] is None
    assert atual['notas'] == 'Perguntar sobre planos de viagem.'
    nova = c.post(f'/api/reunioes/{rid}/preparar').get_json()
    assert nova['pauta']['id'] != a['pauta']['id'] and nova['notas'] == atual['notas']


def test_ca87_cancelamento_reagendamento_e_conclusao_unica(ambiente):
    app, c = ambiente
    cancelada = criar(c)
    assert c.patch(f'/api/reunioes/{cancelada}', json={'inicio_em': (AGORA + timedelta(days=2)).isoformat()}).status_code == 200
    assert not c.get(f'/api/reunioes/{cancelada}').get_json()['proxima']
    assert c.post(f'/api/reunioes/{cancelada}/cancelar').get_json()['estado'] == 'cancelada'
    assert c.post(f'/api/reunioes/{cancelada}/preparar').status_code == 409
    rid = criar(c)
    corpo = {'resumo': 'Reunião fictícia realizada; objetivos conferidos.', 'proximos_passos': 'Revisar documentos.'}
    a = c.post(f'/api/reunioes/{rid}/concluir', json=corpo)
    b = c.post(f'/api/reunioes/{rid}/concluir', json=corpo)
    assert a.status_code == 201 and b.status_code == 200
    assert a.get_json()['interacao_id'] == b.get_json()['interacao_id']
    assert c.post(f'/api/reunioes/{rid}/concluir', json={'resumo': 'Mudou'}).status_code == 409
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM interacao WHERE texto=?', (corpo['resumo'],)).fetchone()[0] == 1


def test_ca88_cache_antecipado_compartilhado_entre_reunioes(noticias_env):
    app, c, coletor = noticias_env
    aprovar(c, 1); aprovar(c, 3)
    vincular(c, 1); vincular(c, 3)
    atualizar(c)
    rid = criar(c, 1, inicio_em=(AGORA + timedelta(hours=5)).isoformat())
    outro = criar(c, 3, inicio_em=(AGORA + timedelta(hours=5)).isoformat())
    assert c.post(f'/api/reunioes/{rid}/preparar').status_code == 200 and len(coletor.chamadas) == 1
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(hours=2))
    assert c.post(f'/api/reunioes/{rid}/preparar').status_code == 200 and len(coletor.chamadas) == 2
    assert c.post(f'/api/reunioes/{outro}/preparar').status_code == 200 and len(coletor.chamadas) == 2


def test_ca89_cli_janela_reuso_e_cancelada(ambiente):
    app, c = ambiente
    perto = criar(c, inicio_em=(AGORA + timedelta(hours=24)).isoformat())
    longe = criar(c, inicio_em=(AGORA + timedelta(hours=24, seconds=1)).isoformat())
    cancelada = criar(c)
    c.post(f'/api/reunioes/{cancelada}/cancelar')
    for _ in range(2):
        resultado = app.test_cli_runner().invoke(args=['acompanhar-agenda', '--uma-vez'])
        assert resultado.exit_code == 0, resultado.output
    assert c.get(f'/api/reunioes/{perto}').get_json()['pauta'] is not None
    assert c.get(f'/api/reunioes/{longe}').get_json()['pauta'] is None
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM pauta_reuniao').fetchone()[0] == 1


def test_ca88_cota_nao_apaga_pauta_interna_nem_oculta_falha(noticias_env):
    app, c, coletor = noticias_env
    vincular(c)
    atualizar(c)
    app.config['NEWSAPI_LIMITE_DIARIO'] = 1
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(hours=2))
    rid = criar(c, inicio_em=(AGORA + timedelta(hours=5)).isoformat())
    r = c.post(f'/api/reunioes/{rid}/preparar')
    assert r.status_code == 200 and r.get_json()['pauta']['secoes']
    assert any('Limite diário' in aviso for aviso in r.get_json()['pauta']['avisos'])
    assert len(coletor.chamadas) == 1
    assert c.get(f'/api/reunioes/{rid}').get_json()['pauta']['avisos'] == r.get_json()['pauta']['avisos']
