"""Sincronização de reuniões com Google Agenda usando respostas HTTP simuladas."""
from datetime import datetime, timedelta
import sqlite3
from urllib.parse import parse_qs, urlparse

import pytest

from app import create_app
from app import google_agenda
from app.clock import TZ, formatar_utc, relogio_fixo
from app.db import get_db, init_db
from app.seed import seed_db
from client_autenticado import cliente_autenticado

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)
REDIRECT_URI = 'http://localhost:5001/api/integracoes/google-agenda/retorno'


@pytest.fixture
def ambiente(tmp_path):
    app = create_app({
        'TESTING': True,
        'DATABASE': str(tmp_path / 'google-agenda.db'),
        'CLOCK': relogio_fixo(AGORA),
        'OPENAI_API_KEY': '',
        'GEMINI_API_KEY': '',
        'NEWSAPI_API_KEY': '',
        'GOOGLE_CALENDAR_CLIENT_ID': 'cliente-teste',
        'GOOGLE_CALENDAR_CLIENT_SECRET': 'segredo-teste',
        'GOOGLE_CALENDAR_REDIRECT_URI': REDIRECT_URI,
    })
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app, cliente_autenticado(app)


def conectar_token(app):
    with app.app_context():
        get_db().execute(
            'INSERT INTO google_agenda_token(id,email,access_token,refresh_token,expira_em) VALUES (1,?,?,?,?)',
            ('assessor@example.test', google_agenda._cifrar('access-falso'),
             google_agenda._cifrar('refresh-falso'), formatar_utc(AGORA + timedelta(hours=1))),
        )
        get_db().commit()


def criar(c):
    resposta = c.post('/api/clientes/1/reunioes', json={
        'objetivo': 'Revisar objetivos fictícios',
        'inicio_em': (AGORA + timedelta(hours=2)).isoformat(),
    })
    assert resposta.status_code == 201, resposta.get_json()
    return resposta.get_json()


def test_oauth_valida_state_cifra_tokens_e_nao_retorna_credenciais(ambiente, monkeypatch):
    app, c = ambiente
    chamadas = []

    def solicitar(metodo, url, dados=None, access_token=None, formulario=False):
        chamadas.append((metodo, url, dados, formulario))
        if url == google_agenda.TOKEN_URL:
            return {'access_token': 'access-secreto-falso', 'refresh_token': 'refresh-secreto-falso', 'expires_in': 3600}
        assert url == google_agenda.USERINFO_URL
        assert access_token == 'access-secreto-falso'
        return {'email': 'assessor@example.test'}

    monkeypatch.setattr(google_agenda, '_solicitar', solicitar)
    inicio = c.post('/api/integracoes/google-agenda/conectar')
    assert inicio.status_code == 200
    parametros = parse_qs(urlparse(inicio.get_json()['url']).query)
    assert parametros['redirect_uri'] == [REDIRECT_URI]
    assert 'calendar.events' in parametros['scope'][0]
    retorno = c.get(f'/api/integracoes/google-agenda/retorno?code=falso&state={parametros["state"][0]}')
    assert retorno.status_code == 302 and 'google_agenda=conectado' in retorno.location
    estado = c.get('/api/integracoes/google-agenda').get_json()
    assert estado == {'configurado': True, 'conectado': True, 'email': 'assessor@example.test'}
    with app.app_context():
        token = get_db().execute('SELECT access_token,refresh_token FROM google_agenda_token').fetchone()
        assert 'access-secreto-falso' not in token['access_token']
        assert 'refresh-secreto-falso' not in token['refresh_token']
    assert chamadas[0][3] is True

    inicio = c.post('/api/integracoes/google-agenda/conectar')
    state = parse_qs(urlparse(inicio.get_json()['url']).query)['state'][0]
    invalido = c.get(f'/api/integracoes/google-agenda/retorno?code=falso&state={state}incorreto')
    assert invalido.status_code == 302 and 'google_agenda=erro' in invalido.location
    assert len(chamadas) == 2


def test_status_google_exige_sessao_e_erro_de_configuracao_e_explicito(tmp_path):
    app = create_app({
        'TESTING': True,
        'DATABASE': str(tmp_path / 'sem-configuracao.db'),
        'CLOCK': relogio_fixo(AGORA),
        'SECRET_KEY': 'segredo-de-teste-com-comprimento-suficiente',
    })
    anonimo = app.test_client()
    assert anonimo.get('/api/integracoes/google-agenda').status_code == 401
    c = cliente_autenticado(app)
    estado = c.get('/api/integracoes/google-agenda').get_json()
    assert estado == {'configurado': False, 'conectado': False, 'email': None}
    erro = c.post('/api/integracoes/google-agenda/conectar')
    assert erro.status_code == 503 and erro.get_json()['erro']['campo'] == 'google_agenda'


def test_migra_reunioes_existentes_sem_perder_registros(tmp_path):
    caminho = tmp_path / 'base-antiga.db'
    with sqlite3.connect(caminho) as db:
        db.execute("""CREATE TABLE reuniao (
            id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL, assessor_id INTEGER NOT NULL,
            objetivo TEXT NOT NULL, inicio_em TEXT NOT NULL, criada_em TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'agendada', notas TEXT NOT NULL DEFAULT '',
            pauta_revisada_id INTEGER, avisos_busca TEXT NOT NULL DEFAULT '[]', interacao_id INTEGER
        )""")
        db.execute("INSERT INTO reuniao(id,cliente_id,assessor_id,objetivo,inicio_em,criada_em) VALUES (1,1,1,'Reunião antiga','2026-10-10T18:00:00+00:00','2026-10-10T15:00:00+00:00')")
    app = create_app({'TESTING': True, 'DATABASE': str(caminho), 'SECRET_KEY': 'segredo-de-teste-com-comprimento-suficiente'})
    with app.app_context():
        colunas = {linha['name'] for linha in get_db().execute('PRAGMA table_info(reuniao)')}
        registro = get_db().execute('SELECT objetivo,google_sync_status FROM reuniao WHERE id=1').fetchone()
        init_db()
    assert {'google_event_id', 'google_sync_status', 'google_sync_error', 'google_event_url'} <= colunas
    assert tuple(registro) == ('Reunião antiga', 'nao_conectado')


def test_cria_reagenda_e_cancela_evento_de_uma_hora(ambiente, monkeypatch):
    app, c = ambiente
    conectar_token(app)
    eventos = {}
    chamadas = []

    def solicitar(metodo, url, dados=None, access_token=None, formulario=False):
        chamadas.append((metodo, url, dados))
        if url == google_agenda.TOKEN_URL:
            raise AssertionError('Token ainda válido; não deve renovar.')
        if metodo == 'GET':
            if url not in eventos:
                raise google_agenda.ErroGoogleAgenda('Não encontrado.', 404)
            return eventos[url]
        if metodo == 'POST':
            evento = {**dados, 'htmlLink': 'https://calendar.google.test/evento'}
            eventos[f'{google_agenda.API_URL}/{dados["id"]}'] = evento
            return evento
        if metodo == 'PATCH':
            eventos[url].update(dados)
            return eventos[url]
        if metodo == 'DELETE':
            eventos.pop(url, None)
            return {}
        raise AssertionError(metodo)

    monkeypatch.setattr(google_agenda, '_solicitar', solicitar)
    reuniao = criar(c)
    rid = reuniao['id']
    assert 'google_event_id' not in reuniao
    assert reuniao['google_agenda']['estado'] == 'sincronizado'
    evento = next(iter(eventos.values()))
    assert evento['summary'] == 'Reunião com Ana Souza (fictício)'
    assert evento['description'] == 'Revisar objetivos fictícios'
    assert evento['start'] == {'dateTime': '2026-10-10T17:00:00-03:00', 'timeZone': 'America/Sao_Paulo'}
    assert evento['end'] == {'dateTime': '2026-10-10T18:00:00-03:00', 'timeZone': 'America/Sao_Paulo'}
    assert reuniao['google_agenda']['evento_url'] == 'https://calendar.google.test/evento'

    antes = len(chamadas)
    c.get(f'/api/reunioes/{rid}')
    assert len(chamadas) == antes
    notas = c.patch(f'/api/reunioes/{rid}', json={'notas': 'Nota local'})
    assert notas.get_json()['google_agenda']['estado'] == 'sincronizado'
    assert len(chamadas) == antes
    reagendada = c.patch(f'/api/reunioes/{rid}', json={
        'objetivo': 'Novo objetivo',
        'inicio_em': (AGORA + timedelta(hours=3)).isoformat(),
    }).get_json()
    assert reagendada['google_agenda']['estado'] == 'sincronizado'
    assert len([chamada for chamada in chamadas if chamada[0] == 'POST']) == 1
    assert next(iter(eventos.values()))['description'] == 'Novo objetivo'

    cancelada = c.post(f'/api/reunioes/{rid}/cancelar').get_json()
    assert cancelada['google_agenda']['estado'] == 'sincronizado'
    assert cancelada['google_agenda']['evento_url'] is None
    assert not eventos


def test_falha_google_preserva_reuniao_e_retry_nao_duplica(ambiente, monkeypatch):
    app, c = ambiente
    conectar_token(app)
    eventos = {}
    inserir = 0
    falhar_leitura = True

    def solicitar(metodo, url, dados=None, access_token=None, formulario=False):
        nonlocal inserir, falhar_leitura
        if metodo == 'GET':
            if falhar_leitura:
                falhar_leitura = False
                raise google_agenda.ErroGoogleAgenda('Serviço temporariamente indisponível.', 503)
            if url not in eventos:
                raise google_agenda.ErroGoogleAgenda('Não encontrado.', 404)
            return eventos[url]
        if metodo == 'POST':
            inserir += 1
            evento = {**dados, 'htmlLink': 'https://calendar.google.test/retry'}
            eventos[f'{google_agenda.API_URL}/{dados["id"]}'] = evento
            return evento
        if metodo == 'PATCH':
            eventos[url].update(dados)
            return eventos[url]
        raise AssertionError(metodo)

    monkeypatch.setattr(google_agenda, '_solicitar', solicitar)
    reuniao = criar(c)
    rid = reuniao['id']
    assert reuniao['id'] is not None
    assert reuniao['google_agenda']['estado'] == 'falhou'
    assert reuniao['google_agenda']['erro'] == 'Serviço temporariamente indisponível.'
    assert c.get(f'/api/reunioes/{rid}').get_json()['objetivo'] == 'Revisar objetivos fictícios'

    sincronizada = c.post(f'/api/reunioes/{rid}/sincronizar-google-agenda').get_json()
    assert sincronizada['google_agenda']['estado'] == 'sincronizado'
    assert c.post(f'/api/reunioes/{rid}/sincronizar-google-agenda').get_json()['google_agenda']['estado'] == 'sincronizado'
    assert inserir == 1
