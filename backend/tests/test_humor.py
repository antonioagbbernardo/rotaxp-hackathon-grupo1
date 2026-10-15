from copy import deepcopy
from datetime import datetime

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from client_autenticado import cliente_autenticado


class HumorFake:
    def __init__(self):
        self.chamadas = []
        self.invalido = False

    def conversar(self, contexto, historico, pergunta, **kwargs):
        self.chamadas.append(deepcopy(contexto))
        f = contexto['fatos'][0]
        return {'sentiment': 'negative', 'motivo': 'O investidor expressou insatisfação no contato.',
            'fontes': [f['id']], 'evidencias': [{'fonte': f['id'],
                'trecho': 'trecho inventado' if self.invalido else f['texto'][:100]}]}


@pytest.fixture
def ambiente(tmp_path):
    fake = HumorFake()
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'humor.db'),
        'HUMOR_OPENAI': fake, 'OPENAI_API_KEY': '',
        'CLOCK': relogio_fixo(datetime(2026, 10, 10, 15, tzinfo=TZ))})
    with app.app_context():
        seed_db(app.config['CLOCK'].hoje(), app.config['CLOCK'].agora())
    return app, cliente_autenticado(app), fake


def cliente(c, cid=1):
    return next(r for r in c.get('/api/pulse').get_json()['clients'] if r['id'] == str(cid))


def test_inferencia_separada_com_evidencia_cache_revisao_e_nova_conversa(ambiente):
    app, c, fake = ambiente
    antes = cliente(c)
    assert antes['sentiment'] == 'unknown'  # Avaliação humana não é humor inferido.
    assert fake.chamadas == []  # GET nunca chama IA.
    a = c.post('/api/pulse/clientes/1/humor')
    assert a.status_code == 200
    humor = a.get_json()
    assert humor['sentiment'] == 'negative' and humor['revisado_em'] is None
    assert c.post('/api/pulse/clientes/1/humor').get_json() == humor
    assert len(fake.chamadas) == 1
    assert set(fake.chamadas[0]) == {'fatos', 'modelo', 'versao'}
    atual = cliente(c)
    assert atual['sentiment'] == 'negative'
    assert atual['priority'] == antes['priority'] and atual['relationshipLabel'] == antes['relationshipLabel']
    assert c.post('/api/pulse/clientes/1/humor/revisar', json={'assinatura': humor['assinatura']}).get_json()['revisado_em']
    c.post('/api/clientes/1/interacoes', json={'canal': 'telefone', 'texto': 'Investidor: estou muito satisfeito com nosso atendimento.'})
    assert cliente(c)['sentiment'] == 'unknown'
    assert c.post('/api/pulse/clientes/1/humor/revisar', json={'assinatura': humor['assinatura']}).status_code == 409
    assert c.post('/api/pulse/clientes/1/humor').status_code == 200
    assert len(fake.chamadas) == 2
    assert cliente(c)['mood']['revisado_em'] is None


def test_evidencia_inventada_sem_fallback_manual_e_retry_limitado(ambiente):
    app, c, fake = ambiente
    fake.invalido = True
    assert c.post('/api/pulse/clientes/1/humor').status_code == 502
    assert cliente(c)['sentiment'] == 'unknown' and cliente(c)['mood']['estado'] == 'falhou'
    assert c.post('/api/pulse/clientes/1/humor').status_code == 409
    assert len(fake.chamadas) == 1
    assert c.post('/api/pulse/clientes/999/humor').status_code == 404
    assert c.post('/api/pulse/clientes/2/humor', json={'estado': 'positive'}).status_code == 400


def test_sem_interacoes_sem_provedor_e_sem_credencial(ambiente):
    app, c, fake = ambiente
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO cliente(nome) VALUES('Cliente sem conversas')")
        cid = db.execute('SELECT max(id) FROM cliente').fetchone()[0]
        db.commit()
    assert c.post(f'/api/pulse/clientes/{cid}/humor').get_json()['estado'] == 'sem_interacoes'
    assert not fake.chamadas
    app.config['HUMOR_OPENAI'] = None
    assert c.post('/api/pulse/clientes/1/humor').status_code == 503
    assert cliente(c)['sentiment'] == 'unknown'


def test_schema_humor_e_prompt_no_transporte(monkeypatch):
    import io
    import json
    import app.ia_openai as modulo
    from app.humor import INSTRUCOES, SCHEMA
    capturado = {}
    saida = {'sentiment': 'unknown', 'motivo': 'Não há expressão de humor.', 'fontes': [], 'evidencias': []}
    def abrir(req, timeout):
        capturado.update(json.loads(req.data))
        return io.BytesIO(json.dumps({'status': 'completed', 'output': [{'type': 'message',
            'content': [{'type': 'output_text', 'text': json.dumps(saida)}]}]}).encode())
    monkeypatch.setattr(modulo, 'urlopen', abrir)
    assert modulo.OpenAIChat('chave-ficticia').conversar({'fatos': [{'id': 'interacao-1'}]}, [],
        'Inferir', instrucoes=INSTRUCOES, schema_saida=SCHEMA) == saida
    assert capturado['input'][0]['content'] == INSTRUCOES
    assert capturado['text']['format']['schema']['properties']['fontes']['items']['enum'] == ['interacao-1']
    assert not capturado['store']


def test_historico_contem_somente_inferencias_validadas_e_preserva_reanalises(ambiente):
    _, c, fake = ambiente
    assert cliente(c)['perception'] == []
    assert c.post('/api/pulse/clientes/1/humor').status_code == 200
    hist = cliente(c)['perception']
    assert len(hist) == 1 and hist[0]['sentiment'] == 'negative'
    assert hist[0]['evidencias']
    c.post('/api/pulse/clientes/1/humor')
    assert cliente(c)['perception'] == hist
    c.post('/api/clientes/1/interacoes', json={'canal':'telefone','texto':'Investidor: estou preocupado.'})
    c.post('/api/pulse/clientes/1/humor')
    assert len(cliente(c)['perception']) == 2


def test_fala_do_assessor_nao_e_evidencia_do_humor_do_investidor(ambiente):
    app, c, fake = ambiente
    with app.app_context():
        db = get_db()
        db.execute('DELETE FROM interacao WHERE cliente_id=5')
        db.commit()
    c.post('/api/clientes/5/interacoes',json={'canal':'telefone',
        'texto':'Investidor: Estou insatisfeito. Assessor: Perfeito, vou verificar.'})
    assert c.post('/api/pulse/clientes/5/humor').status_code == 200
    texto = fake.chamadas[-1]['fatos'][0]['texto']
    assert 'Estou insatisfeito' in texto and 'Perfeito' not in texto


def test_fala_somente_do_assessor_nao_dispara_inferencia(ambiente):
    _, c, fake = ambiente
    c.post('/api/clientes/5/interacoes',json={'canal':'telefone','texto':'Assessor: Excelente, parabéns!'})
    assert c.post('/api/pulse/clientes/5/humor').get_json()['estado'] == 'sem_interacoes'
    assert not fake.chamadas
