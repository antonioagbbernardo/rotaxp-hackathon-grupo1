"""Chat livre, memória por cliente e notas confirmadas sem alterar contatos."""
from copy import deepcopy
from uuid import uuid4
from datetime import datetime

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from client_autenticado import cliente_autenticado


class ChatFake:
    def __init__(self):
        self.chamadas = []
        self.saida = {'resposta': 'Claro! Posso ajudar a preparar a conversa.', 'fontes': [], 'nota_sugerida': None}

    def conversar(self, contexto, historico, pergunta):
        self.chamadas.append(deepcopy((contexto, historico, pergunta)))
        return deepcopy(self.saida)


@pytest.fixture
def ambiente(tmp_path):
    fake = ChatFake()
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'chat.db'), 'CHAT_OPENAI': fake,
        'CLOCK': relogio_fixo(datetime(2026, 10, 10, 15, tzinfo=TZ)), 'OPENAI_API_KEY': ''})
    with app.app_context():
        seed_db(app.config['CLOCK'].hoje(), app.config['CLOCK'].agora())
    return app, cliente_autenticado(app), fake


def perguntar(c, pergunta='Oi, pode me ajudar?', cid=1, request_id=None):
    return c.post(f'/api/pulse/clientes/{cid}/chat', json={'pergunta': pergunta, 'request_id': request_id or str(uuid4())})


def test_chat_memoria_isolamento_reinicio_e_idempotencia(ambiente):
    app, c, fake = ambiente
    request_id = str(uuid4())
    a = perguntar(c, request_id=request_id)
    assert a.status_code == 200 and a.get_json()['modo'] == 'openai'
    assert perguntar(c, request_id=request_id).get_json()['id'] == a.get_json()['id']
    assert len(fake.chamadas) == 1
    perguntar(c, 'E como começo?')
    assert fake.chamadas[-1][1][0]['content'] == 'Oi, pode me ajudar?'
    perguntar(c, 'Olá!', cid=2)
    assert fake.chamadas[-1][1] == []
    novo = create_app(dict(app.config))
    assert len(cliente_autenticado(novo).get('/api/pulse/clientes/1/chat').get_json()['mensagens']) == 2
    assert perguntar(c, 'Outro texto', request_id=request_id).status_code == 409


def test_nota_confirmada_no_contexto_e_pauta_sem_contato_falso(ambiente):
    app, c, fake = ambiente
    antes = c.get('/api/pulse').get_json()['clients']
    cliente = next(r for r in antes if r['id'] == '1')
    fake.saida['nota_sugerida'] = 'O cliente prefere reuniões à tarde.'
    turno = perguntar(c, 'Anote: o cliente prefere reuniões à tarde.').get_json()
    assert turno['nota_id'] is not None
    assert len(c.get('/api/pulse/clientes/1/chat').get_json()['notas']) == 1
    caminho = f"/api/pulse/clientes/1/chat/{turno['id']}/nota"
    assert c.post(caminho).status_code == 200 and c.post(caminho).status_code == 200
    assert c.post(f"/api/pulse/clientes/2/chat/{turno['id']}/nota").status_code == 404
    fake.saida['nota_sugerida'] = None
    perguntar(c, 'Qual horário ele prefere?')
    assert any('reuniões à tarde' in f['texto'] for f in fake.chamadas[-1][0]['fatos'])
    atual = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '1')
    assert atual['lastContactDays'] == cliente['lastContactDays'] and atual['priority'] == cliente['priority']
    rid = c.post('/api/clientes/1/reunioes', json={'objetivo': 'Revisar', 'inicio_em': '2026-10-10T16:00'}).get_json()['id']
    pauta = c.post(f'/api/reunioes/{rid}/preparar').get_json()['pauta']
    assert any('reuniões à tarde' in i['texto'] for s in pauta['secoes'] for i in s['itens'])
    with app.app_context():
        assert get_db().execute('SELECT count(*) FROM nota_assessor').fetchone()[0] == 1


def test_chat_validacao_fontes_e_credencial_sem_fallback(ambiente):
    app, c, fake = ambiente
    assert perguntar(c, cid=999).status_code == 404
    assert perguntar(c, request_id='invalido').status_code == 400
    fake.saida['fontes'] = ['fonte-inventada']
    assert perguntar(c).status_code == 502
    assert c.get('/api/pulse/clientes/1/chat').get_json()['mensagens'] == []
    app.config['CHAT_OPENAI'] = None
    assert not c.get('/api/pulse/clientes/1/chat').get_json()['configurado']
    assert perguntar(c).status_code == 503


def test_transporte_chat_responses_sem_chave_no_conteudo(monkeypatch):
    import io
    import json
    import app.ia_openai as modulo
    captured = {}
    def abrir(req, timeout):
        captured.update(json.loads(req.data))
        return io.BytesIO(json.dumps({'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps({'resposta':'Olá!', 'fontes':[], 'nota_sugerida':None})}]}]}).encode())
    monkeypatch.setattr(modulo, 'urlopen', abrir)
    assert modulo.OpenAIChat('chave-ficticia').conversar({'fatos':[]}, [], 'Oi')['resposta'] == 'Olá!'
    assert captured['store'] is False and captured['input'][-1]['content'] == 'Oi'
    assert 'chave-ficticia' not in json.dumps(captured)


def test_interesse_chat_confirmado_alimenta_contexto_noticias_sem_contato(ambiente):
    app, c, fake = ambiente
    antes = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '1')
    pergunta = 'O cliente gosta de Fórmula 1 e prefere reuniões à tarde.'
    fake.saida['nota_sugerida'] = pergunta
    fake.saida['contexto_sugerido'] = [
        {'categoria': 'interesse', 'assunto': 'formula-1', 'sujeito': 'cliente', 'valor': 'Gosta de Fórmula 1.', 'trecho': 'gosta de Fórmula 1'},
        {'categoria': 'preferencia', 'assunto': 'horario-reuniao', 'sujeito': 'cliente', 'valor': 'Prefere reuniões à tarde.', 'trecho': 'prefere reuniões à tarde'}]
    turno = perguntar(c, pergunta).get_json()
    assert len(turno['contexto_sugerido']) == 2 and turno['nota_id'] is not None
    assert len(c.get('/api/clientes/1/contexto').get_json()['itens']) == 2
    caminho = f"/api/pulse/clientes/1/chat/{turno['id']}/nota"
    assert c.post(caminho).status_code == 200 and c.post(caminho).status_code == 200
    atual = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '1')
    assert 'Gosta de Fórmula 1.' in atual['interests']
    assert {a['id'] for a in atual['newsState']['assuntos']} == {'formula-1'}
    assert atual['lastContactDays'] == antes['lastContactDays'] and atual['priority'] == antes['priority']
    assert atual['sentiment'] == antes['sentiment']
    itens = atual['context']['itens']
    assert len(itens) == 2 and all(i['estado'] == 'confirmado' and i['evidencia_atual'] for i in itens)
    assert all(i['evidencias'][0]['origem'] == 'chat-assessor' for i in itens)
    assert c.get('/api/clientes/2/contexto').get_json()['itens'] == []
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM documento_fonte WHERE tipo='nota_assessor'").fetchone()[0] == 1
        assert get_db().execute('SELECT count(*) FROM revisao_contexto').fetchone()[0] == 2
    # Nova informação confirmada substitui a anterior, sem conflito artificial.
    fake.saida['nota_sugerida'] = 'O cliente não acompanha Fórmula 1.'
    fake.saida['contexto_sugerido'] = [{'categoria': 'interesse', 'assunto': 'formula-1', 'sujeito': 'cliente',
        'valor': 'Não acompanha Fórmula 1.', 'trecho': 'não acompanha Fórmula 1'}]
    t = perguntar(c, fake.saida['nota_sugerida']).get_json()
    assert c.post(f"/api/pulse/clientes/1/chat/{t['id']}/nota").status_code == 200
    atual = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '1')
    assert {a['id'] for a in atual['newsState']['assuntos']} == {'mercado'}
    assert all(not i['conflitos'] for i in atual['context']['itens'] if i['estado'] == 'confirmado')


def test_contexto_chat_recusa_trecho_inventado_e_nao_presume_gosto_do_cliente(ambiente):
    app, c, fake = ambiente
    fake.saida['nota_sugerida'] = 'A filha gosta de Palmeiras.'
    fake.saida['contexto_sugerido'] = [{'categoria': 'interesse', 'assunto': 'palmeiras', 'sujeito': 'familiar',
        'valor': 'A filha gosta de Palmeiras.', 'trecho': 'trecho inventado'}]
    assert perguntar(c, 'A filha gosta de Palmeiras.').status_code == 502
    assert not c.get('/api/clientes/1/contexto').get_json()['itens']
    fake.saida['contexto_sugerido'][0]['trecho'] = 'A filha gosta de Palmeiras.'
    turno = perguntar(c, 'A filha gosta de Palmeiras.').get_json()
    assert c.post(f"/api/pulse/clientes/1/chat/{turno['id']}/nota").status_code == 200
    atual = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '1')
    assert atual['interests'] == [] and {a['id'] for a in atual['newsState']['assuntos']} == {'mercado'}


def test_migracao_preserva_fontes_antigas_e_amplia_tipo_nota(tmp_path):
    import sqlite3
    from app.db import SCHEMA
    caminho = tmp_path / 'antiga.db'
    antigo = SCHEMA.replace("'interacao', 'formulario', 'nota_assessor'", "'interacao', 'formulario'").replace("    contexto_sugerido TEXT NOT NULL DEFAULT '[]',\n", '')
    with sqlite3.connect(caminho) as db:
        db.executescript(antigo)
        db.execute("INSERT INTO assessor VALUES(1,'Assessor fictício')")
        db.execute("INSERT INTO cliente(id,nome) VALUES(1,'Cliente fictício')")
        db.execute("INSERT INTO documento_fonte(id,origem,registro_id,versao,cliente_id,tipo,conteudo,ocorrida_em,importada_em) VALUES(7,'demo','original',1,1,'formulario','{}','2026-10-10T12:00:00+00:00','2026-10-10T12:00:00+00:00')")
    app = create_app({'TESTING': True, 'DATABASE': str(caminho)})
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT registro_id FROM documento_fonte WHERE id=7').fetchone()[0] == 'original'
        assert 'contexto_sugerido' in {r['name'] for r in db.execute('PRAGMA table_info(chat_turno)')}
        db.execute("INSERT INTO documento_fonte(origem,registro_id,versao,cliente_id,tipo,conteudo,ocorrida_em,importada_em) VALUES('chat-assessor','chat-1',1,1,'nota_assessor','\"informação declarada\"','2026-10-10T12:00:00+00:00','2026-10-10T12:00:00+00:00')")
        assert not db.execute('PRAGMA foreign_key_check').fetchall()


def test_gravacao_automatica_atomica_e_retry_sem_duplicar(ambiente, monkeypatch):
    from app import contexto_chat
    from app.agenda_rules import ErroAgenda
    app, c, fake = ambiente
    fake.saida['nota_sugerida'] = 'Cliente gosta de Palmeiras.'
    fake.saida['contexto_sugerido'] = [{'categoria': 'interesse', 'assunto': 'palmeiras', 'sujeito': 'cliente',
        'valor': 'Gosta de Palmeiras.', 'trecho': 'gosta de Palmeiras'}]
    original = contexto_chat.registrar
    def falhar(*args):
        raise ErroAgenda('Falha de gravação simulada.', 'contexto', 503)
    monkeypatch.setattr(contexto_chat, 'registrar', falhar)
    rid = str(uuid4())
    assert perguntar(c, 'Cliente gosta de Palmeiras.', request_id=rid).status_code == 503
    assert c.get('/api/pulse/clientes/1/chat').get_json()['notas'] == []
    assert c.get('/api/pulse/clientes/1/chat').get_json()['mensagens'] == []
    monkeypatch.setattr(contexto_chat, 'registrar', original)
    turno = perguntar(c, 'Cliente gosta de Palmeiras.', request_id=rid).get_json()
    assert turno['nota_id'] is not None
    assert perguntar(c, 'Cliente gosta de Palmeiras.', request_id=rid).get_json()['nota_id'] == turno['nota_id']
    assert len(c.get('/api/pulse/clientes/1/chat').get_json()['notas']) == 1
    assert len(c.get('/api/clientes/1/contexto').get_json()['itens']) == 1


def test_futebol_digitado_em_noticias_salva_sem_ia_e_seleciona_assunto(ambiente):
    app, c, fake = ambiente
    rid = str(uuid4())
    corpo = {'pergunta': 'Adicionar interesse do cliente: futebol', 'interesse': 'futebol', 'request_id': rid}
    r = c.post('/api/pulse/clientes/2/chat', json=corpo)
    assert r.status_code == 200 and r.get_json()['nota_id']
    assert fake.chamadas == []
    cliente = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '2')
    assert 'futebol' in cliente['interests']
    assert {a['id'] for a in cliente['newsState']['assuntos']} == {'futebol'}
    assert c.post('/api/pulse/clientes/2/chat', json=corpo).get_json()['nota_id'] == r.get_json()['nota_id']


def test_declaracao_gosta_de_cafe_salva_mesmo_se_ia_omite_nota(ambiente):
    app, c, fake = ambiente
    turno = perguntar(c, 'O BRUNO GOSTA DE CAFE', cid=2).get_json()
    assert turno['nota_id'] and turno['contexto_sugerido'][0]['categoria'] == 'interesse'
    cliente = next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == '2')
    assert {a['id'] for a in cliente['newsState']['assuntos']} == {'cafe'}
    fake.saida = {'resposta': 'Não tenho essa informação.', 'fontes': [], 'nota_sugerida': None}
    assert perguntar(c, 'Ele gosta de café?', cid=2).get_json()['nota_id'] is None
