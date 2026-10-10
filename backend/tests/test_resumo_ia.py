import io
import json
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from app.resumo_ia_rules import ErroResumoIA, montar_entrada
from app.ia_openai import OpenAIResumo

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


def conteudo():
    return {'visao_geral': {'texto': 'Perfil moderado cadastrado.', 'fontes': ['fato-0']},
            'pontos_atencao': [], 'antes_contato': []}


class GeradorSimulado:
    modelo = 'modelo-teste'

    def __init__(self):
        self.chamadas = []
        self.ao_gerar = None

    def gerar(self, entrada):
        self.chamadas.append(entrada)
        if self.ao_gerar:
            self.ao_gerar()
        return {'conteudo': conteudo(), 'uso': {'input_tokens': 123, 'output_tokens': 45}}


@pytest.fixture
def ambiente(tmp_path):
    gerador = GeradorSimulado()
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'resumo.db'),
                      'CLOCK': relogio_fixo(AGORA), 'GERADOR_RESUMO': gerador,
                      'OPENAI_API_KEY': '', 'FRONTEND_DIST': str(tmp_path / 'dist')})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app, app.test_client(), gerador


def ana(c):
    return next(i for i in c.get('/api/pulse').get_json()['clients'] if i['id'] == '1')


def gerar(c):
    return c.post('/api/pulse/clientes/1/resumo-ia')


def test_get_sem_chamada_fatos_separados_cache_persistente(ambiente):
    app, c, g = ambiente
    original = ana(c)
    assert original['assistant']['aiSummary']['resumo'] is None and not g.chamadas
    assert len(original['assistant']['summaryItems']) > 1
    assert all('dia(s)' not in t for t in original['assistant']['summaryItems'])
    r = gerar(c)
    assert r.status_code == 200 and not r.get_json()['reutilizado']
    resumo = r.get_json()['resumo']
    assert resumo['visao_geral']['fontes'] == ['cliente #1']
    assert gerar(c).get_json()['reutilizado'] and len(g.chamadas) == 1
    outro = create_app(dict(app.config)).test_client()
    assert ana(outro)['assistant']['aiSummary']['resumo'] == resumo
    assert ana(c)['priority'] == original['priority']
    assert ana(c)['relationshipLabel'] == original['relationshipLabel']


@pytest.mark.parametrize('mudanca', ['contato', 'preferencia', 'alerta', 'data', 'modelo'])
def test_mudancas_invalidam_cache(ambiente, mudanca):
    app, c, g = ambiente
    assert gerar(c).status_code == 200
    if mudanca == 'contato':
        assert c.post('/api/clientes/1/interacoes', json={'canal': 'telefone', 'texto': 'Contato fictício novo'}).status_code == 201
    elif mudanca == 'preferencia':
        with app.app_context():
            get_db().execute('UPDATE cliente SET intervalo_minimo_dias=14 WHERE id=1')
            get_db().commit()
    elif mudanca == 'alerta':
        with app.app_context():
            get_db().execute("UPDATE posicao SET vencimento='2026-12-10' WHERE cliente_id=1")
            get_db().commit()
    elif mudanca == 'data':
        app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1))
    else:
        g.modelo = 'modelo-novo'
    assert ana(c)['assistant']['aiSummary']['resumo'] is None
    assert not gerar(c).get_json()['reutilizado'] and len(g.chamadas) == 2


def test_selecao_nao_envia_propostas_bloqueios_terceiros_transcricoes(ambiente):
    _, c, _ = ambiente
    cliente = ana(c)
    base = {'id': 50, 'tipo': 'fato', 'estado': 'confirmado', 'sujeito': 'cliente', 'evidencia_atual': True,
            'conflitos': [], 'bloqueado': False, 'elegivel_contato': True,
            'valor_original': 'Interesse revisado', 'valor_revisado': None,
            'evidencias': [{'documento_id': 2, 'origem': 'demo', 'registro_id': 'x', 'versao': 1}]}
    itens = [base]
    for n, alteracao in enumerate([{'estado': 'pendente'}, {'bloqueado': True}, {'sujeito': 'familiar'},
                                  {'evidencia_atual': False}, {'conflitos': [99]}, {'elegivel_contato': False}, {'tipo': 'hipotese'}]):
        itens.append({**base, **alteracao, 'id': n + 51, 'valor_original': f'EXCLUIR-{n}'})
    cliente['context']['itens'] = itens
    cliente['interactions'][0]['texto'] = 'TRANSCRICAO-SECRETA'
    entrada = montar_entrada(cliente, AGORA.date())
    texto = json.dumps(entrada)
    assert 'Interesse revisado' in texto
    assert 'Relacionamento:' not in texto and 'relacionamento_avaliado_pelo_assessor' not in entrada
    assert 'EXCLUIR' not in texto and 'TRANSCRICAO-SECRETA' not in texto and 'Bruno' not in texto
    cliente['context']['itens'][0]['valor_revisado'] = 'Texto corrigido'
    assert montar_entrada(cliente, AGORA.date()) != entrada


@pytest.mark.parametrize('alteracao', ['fonte', 'vazio', 'texto', 'extra', 'lista'])
def test_saida_invalida_nao_persiste(ambiente, alteracao):
    app, c, g = ambiente
    saida = conteudo()
    if alteracao == 'fonte':
        saida['visao_geral']['fontes'] = ['cliente-999']
    elif alteracao == 'vazio':
        saida['visao_geral']['fontes'] = []
    elif alteracao == 'texto':
        saida['visao_geral']['texto'] = 'x' * 451
    elif alteracao == 'extra':
        saida['prioridade'] = 'baixa'
    else:
        saida['antes_contato'] = [saida['visao_geral']] * 4
    g.gerar = lambda _: {'conteudo': saida, 'uso': {}}
    assert gerar(c).status_code == 502
    assert ana(c)['assistant']['aiSummary']['resumo'] is None
    with app.app_context():
        assert get_db().execute('SELECT resposta FROM resumo_ia').fetchone()['resposta'] is None


def test_mudanca_durante_chamada_nao_persiste_e_permite_retry(ambiente):
    _, c, g = ambiente
    def mudar():
        get_db().execute("UPDATE cliente SET perfil='Conservador' WHERE id=1")
        get_db().commit()
    g.ao_gerar = mudar
    assert gerar(c).status_code == 409
    assert ana(c)['assistant']['aiSummary']['resumo'] is None
    g.ao_gerar = None
    assert gerar(c).status_code == 200


def test_requisicao_concorrente_e_retomada_de_tentativa(ambiente):
    app, c, g = ambiente
    resultados = []
    def concorrente():
        resultados.append(app.test_client().post('/api/pulse/clientes/1/resumo-ia').status_code)
    g.ao_gerar = concorrente
    assert gerar(c).status_code == 200
    assert resultados == [409] and len(g.chamadas) == 1
    with app.app_context():
        get_db().execute("UPDATE resumo_ia SET estado='em_processamento', resposta=NULL")
        get_db().commit()
    assert gerar(c).status_code == 409
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(minutes=3))
    g.ao_gerar = None
    assert gerar(c).status_code == 200


def test_configuracao_entrada_grande_e_corpo_sem_chamada(ambiente):
    app, c, g = ambiente
    assert c.post('/api/pulse/clientes/1/resumo-ia', json={}).status_code == 400
    assert c.post('/api/pulse/clientes/999/resumo-ia').status_code == 404
    with app.app_context():
        get_db().execute("UPDATE cliente SET perfil=? WHERE id=1", ('x' * 20001,))
        get_db().commit()
    assert gerar(c).status_code == 400 and not g.chamadas
    with app.app_context():
        get_db().execute("UPDATE cliente SET perfil='Moderado' WHERE id=1")
        get_db().commit()
    app.config['GERADOR_RESUMO'] = None
    assert gerar(c).status_code == 503
    assert ana(c)['assistant']['summaryItems']


def test_tentativa_antiga_nao_sobrescreve_a_retomada(ambiente):
    app, c, g = ambiente
    retomada = []
    def retomar():
        app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(minutes=3))
        g.ao_gerar = None
        retomada.append(app.test_client().post('/api/pulse/clientes/1/resumo-ia'))
    g.ao_gerar = retomar
    antiga = gerar(c)
    assert antiga.status_code == 409
    assert retomada[0].status_code == 200 and len(g.chamadas) == 2
    assert ana(c)['assistant']['aiSummary']['resumo'] == retomada[0].get_json()['resumo']


def resposta_openai(saida=None, **alteracoes):
    return {'status': 'completed', 'output': [{'type': 'message', 'content': [
        {'type': 'output_text', 'text': json.dumps(saida or conteudo())}]}],
        'usage': {'input_tokens': 12, 'output_tokens': 34}, **alteracoes}


def test_transporte_responses_schema_store_false_e_limites(monkeypatch):
    pedidos = []
    def abrir(req, timeout):
        pedidos.append((req, timeout))
        return io.BytesIO(json.dumps(resposta_openai()).encode())
    monkeypatch.setattr('app.ia_openai.urlopen', abrir)
    r = OpenAIResumo('segredo-teste', 'gpt-4.1-mini').gerar({'fatos': []})
    req, timeout = pedidos[0]
    corpo = json.loads(req.data)
    assert req.full_url == 'https://api.openai.com/v1/responses'
    assert req.get_header('Authorization') == 'Bearer segredo-teste'
    assert timeout == 30 and corpo['store'] is False and corpo['max_output_tokens'] == 1200
    assert corpo['text']['format']['strict'] is True and 'tools' not in corpo
    assert r['conteudo'] == conteudo() and r['uso']['input_tokens'] == 12


@pytest.mark.parametrize('retorno', [
    resposta_openai(status='incomplete'),
    resposta_openai(output=[{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'recusa'}]}]),
    resposta_openai(output=[]),
    {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'invalido'}]}]},
])
def test_transporte_rejeita_recusa_saida_incompleta_ou_invalida(monkeypatch, retorno):
    monkeypatch.setattr('app.ia_openai.urlopen', lambda *a, **k: io.BytesIO(json.dumps(retorno).encode()))
    with pytest.raises(ErroResumoIA) as erro:
        OpenAIResumo('segredo-teste').gerar({})
    assert erro.value.status == 502


@pytest.mark.parametrize('falha', [HTTPError('url', 401, 'erro', {}, None),
                                  HTTPError('url', 429, 'erro', {}, None), URLError('segredo-teste'), TimeoutError()])
def test_transporte_erros_sem_expor_segredo(monkeypatch, falha):
    def abrir(*a, **k):
        raise falha
    monkeypatch.setattr('app.ia_openai.urlopen', abrir)
    with pytest.raises(ErroResumoIA) as erro:
        OpenAIResumo('segredo-teste').gerar({})
    assert erro.value.status == 503 and 'segredo-teste' not in erro.value.mensagem


def test_transporte_sem_chave_nao_chama_e_saida_grande_recusada(monkeypatch):
    monkeypatch.setattr('app.ia_openai.urlopen', lambda *a, **k: pytest.fail('Não deve chamar sem chave'))
    with pytest.raises(ErroResumoIA):
        OpenAIResumo('').gerar({})
    monkeypatch.setattr('app.ia_openai.urlopen', lambda *a, **k: io.BytesIO(b'x' * 1000001))
    with pytest.raises(ErroResumoIA) as erro:
        OpenAIResumo('teste').gerar({})
    assert erro.value.status == 502
