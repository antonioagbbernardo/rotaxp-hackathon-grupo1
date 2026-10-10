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
    assert c.get('/api/pulse/clientes/1/chat').get_json()['notas'] == []
    caminho = f"/api/pulse/clientes/1/chat/{turno['id']}/nota"
    assert c.post(caminho).status_code == 200 and c.post(caminho).status_code == 200
    assert c.post(f"/api/pulse/clientes/2/chat/{turno['id']}/nota").status_code == 404
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
