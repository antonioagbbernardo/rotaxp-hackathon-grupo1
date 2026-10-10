from client_autenticado import cliente_autenticado, renovar_acesso
"""CA72–CA78: seleção humana, cache compartilhado, orçamento e falhas."""
import io
import json
from copy import deepcopy
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from test_contexto import ExtratorSimulado

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


def test_alias_da_chave_funciona_com_campo_principal_vazio(tmp_path, monkeypatch):
    import app as modulo
    monkeypatch.delenv('NEWSAPI_API_KEY', raising=False)
    monkeypatch.delenv('NEWSAPI_KEY', raising=False)
    monkeypatch.setattr(modulo, 'dotenv_values', lambda _: {'NEWSAPI_API_KEY': '', 'NEWSAPI_KEY': 'chave-ficticia-alias'})
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'config.db')})
    assert app.config['NEWSAPI_API_KEY'] == 'chave-ficticia-alias'


def artigo(**extras):
    return {'title': 'Notícia fictícia de automobilismo', 'description': 'Trecho fictício para testes.',
            'source': {'name': 'Veículo fictício'}, 'url': 'https://exemplo.test/f1?utm_source=teste#noticia',
            'publishedAt': (AGORA - timedelta(days=1)).isoformat(), **extras}


class ColetorSimulado:
    def __init__(self):
        self.chamadas = []
        self.resultado = {'status': 'ok', 'articles': [artigo()]}
        self.ao_buscar = None

    def buscar(self, consulta, agora):
        self.chamadas.append((deepcopy(consulta), agora))
        if self.ao_buscar:
            self.ao_buscar()
        return deepcopy(self.resultado)


@pytest.fixture
def ambiente(tmp_path):
    coletor = ColetorSimulado()
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'noticias.db'),
                      'CLOCK': relogio_fixo(AGORA), 'COLETOR_NOTICIAS': coletor,
                      'NEWSAPI_API_KEY': 'chave-ficticia', 'NEWSAPI_LIMITE_DIARIO': 20,
                      'EXTRATOR_IA': ExtratorSimulado(), 'OPENAI_API_KEY': '',
                      'GEMINI_API_KEY': '', 'FRONTEND_DIST': str(tmp_path / 'dist')})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    c = cliente_autenticado(app)
    docs = [{'registro_id': f'interesse-{cid}', 'cliente_id': cid, 'versao': 1,
             'tipo': 'formulario', 'ocorrida_em': (AGORA - timedelta(days=25)).isoformat(),
             'conteudo': {'interesse': 'Dados fictícios: acompanho Fórmula 1.'}} for cid in (1, 3)]
    assert c.post('/api/fontes/importar', json={'origem': 'teste-ficticio', 'ficticio': True, 'documentos': docs}).status_code == 200
    for cid in (1, 3):
        assert c.post(f'/api/clientes/{cid}/contexto/processar').status_code == 200
    return app, c, coletor


def item(c, cid=1):
    return c.get(f'/api/clientes/{cid}/contexto').get_json()['itens'][0]


def aprovar(c, cid=1):
    i = item(c, cid)
    assert c.post(f'/api/clientes/{cid}/contexto/{i["id"]}/revisar', json={
        'acao': 'aprovar', 'revisao': i['revisao'], 'motivo': 'Conferido com a fonte fictícia.'}).status_code == 200
    return item(c, cid)


def vincular(c, cid=1, assunto='formula-1'):
    i = aprovar(c, cid)
    r = c.post(f'/api/clientes/{cid}/noticias/vinculos', json={'item_id': i['id'], 'assunto': assunto})
    assert r.status_code == 201
    return i, r.get_json()['vinculo_id']


def consultar(c, cid=1):
    r = c.get(f'/api/clientes/{cid}/noticias')
    assert r.status_code == 200
    return r.get_json()


def atualizar(c, cid=1):
    r = c.post(f'/api/clientes/{cid}/noticias/atualizar')
    assert r.status_code == 200
    return r.get_json()['resultados'][0]


def test_noticias_automaticas_sem_aprovar_ou_associar_e_remocao_persistente(ambiente):
    app, c, g = ambiente
    assert item(c)['estado'] == 'pendente'
    automaticos = consultar(c)['vinculos']
    assert len(automaticos) == 1 and automaticos[0]['automatico']
    assert not g.chamadas
    assert atualizar(c)['estado'] == 'atualizado'
    assert atualizar(c, 3)['estado'] == 'reutilizado' and len(g.chamadas) == 1
    artigo = consultar(c)['artigos'][0]
    assert c.post('/api/clientes/1/noticias/descartar', json={'artigo_id': artigo['id'], 'motivo': 'Não pertinente.'}).status_code == 200
    assert consultar(c)['artigos'] == [] and consultar(c, 3)['artigos']
    with app.app_context():
        assert get_db().execute('SELECT count(*) FROM vinculo_noticia').fetchone()[0] == 0
    assert item(c)['estado'] == 'pendente'


def test_get_sem_http_vinculo_explicito_cache_compartilhado_e_reinicio(ambiente):
    app, c, g = ambiente
    assert consultar(c)['artigos'] == [] and not g.chamadas
    i, vid = vincular(c)
    repetido = c.post('/api/clientes/1/noticias/vinculos', json={'item_id': i['id'], 'assunto': 'formula-1'})
    assert repetido.status_code == 200 and repetido.get_json()['vinculo_id'] == vid
    vincular(c, 3)
    antes = c.get('/api/clientes/1').get_json()
    assert atualizar(c)['estado'] == 'atualizado'
    assert atualizar(c, 3)['estado'] == 'reutilizado'
    assert len(g.chamadas) == 1
    resultado = consultar(c)
    a = resultado['artigos'][0]
    assert a['url'] == 'https://exemplo.test/f1' and a['sentiment'] == 'unknown'
    assert a['source'] == 'Veículo fictício' and a['publishedAt'] != a['collectedAt']
    assert 'documento #' in a['whyItMatters'] and 'Dados fictícios' in a['whyItMatters']
    assert resultado['chamadas_hoje'] == 1 and resultado['assuntos'][0]['estado'] == 'atualizado'
    assert c.get('/api/clientes/1').get_json() == antes
    painel = c.get('/api/pulse').get_json()['clients']
    assert next(i for i in painel if i['id'] == '1')['news'] == resultado['artigos']
    assert next(i for i in painel if i['id'] == '2')['news'] == []
    outro = cliente_autenticado(create_app(dict(app.config)))
    assert consultar(outro)['artigos'] == resultado['artigos']
    assert atualizar(outro)['estado'] == 'reutilizado'
    assert not {'nome', 'cliente_id', 'conteudo'} & g.chamadas[0][0].keys()
    assert 'Ana' not in json.dumps(g.chamadas[0][0])


@pytest.mark.parametrize('mudanca', [
    {'estado': 'pendente'}, {'tipo': 'hipotese'}, {'sujeito': 'familiar'}, {'categoria': 'objetivo'},
])
def test_vinculo_recusa_item_nao_elegivel(ambiente, mudanca):
    app, c, _ = ambiente
    i = aprovar(c)
    with app.app_context():
        campo, valor = next(iter(mudanca.items()))
        get_db().execute(f'UPDATE item_contexto SET {campo}=? WHERE id=?', (valor, i['id']))
        get_db().commit()
    r = c.post('/api/clientes/1/noticias/vinculos', json={'item_id': i['id'], 'assunto': 'formula-1'})
    assert r.status_code == 400 and r.get_json()['erro']['campo'] == 'item_id'


@pytest.mark.parametrize('corpo', [None, {}, {'item_id': True, 'assunto': 'formula-1'},
    {'item_id': 1, 'assunto': 'arbitrario'}, {'item_id': 1, 'assunto': ['formula-1']},
    {'item_id': 1, 'assunto': 'formula-1', 'q': 'nome do cliente'}])
def test_vinculo_recusa_entrada_invalida(ambiente, corpo):
    _, c, g = ambiente
    antes = consultar(c)['vinculos']
    assert c.post('/api/clientes/1/noticias/vinculos', json=corpo).status_code == 400
    assert consultar(c)['vinculos'] == antes and not g.chamadas


@pytest.mark.parametrize('mudanca', ['preferencia', 'contato', 'bloqueio', 'revisao', 'fonte', 'conflito'])
def test_releitura_oculta_vinculo_e_noticia_inelegiveis(ambiente, mudanca):
    app, c, _ = ambiente
    i, _ = vincular(c)
    assert atualizar(c)['estado'] == 'atualizado'
    if mudanca == 'preferencia':
        c.patch('/api/clientes/1/preferencias', json={'permite_assuntos_pessoais': False})
    elif mudanca == 'contato':
        c.post('/api/clientes/1/interacoes', json={'canal': 'telefone', 'texto': 'Contato fictício realizado agora.'})
    elif mudanca == 'bloqueio':
        c.post('/api/clientes/1/assuntos/formula-1', json={'bloqueado': True, 'motivo': 'Não abordar esse assunto.'})
    elif mudanca == 'revisao':
        c.post(f'/api/clientes/1/contexto/{i["id"]}/revisar', json={'acao': 'corrigir', 'revisao': 1,
            'motivo': 'Atualização conferida.', 'valor': 'Prefere outro esporte.'})
    else:
        with app.app_context():
            db = get_db()
            if mudanca == 'fonte':
                d = db.execute('SELECT * FROM documento_fonte WHERE cliente_id=1').fetchone()
                db.execute('INSERT INTO documento_fonte (origem,registro_id,versao,cliente_referencia,cliente_id,tipo,conteudo,ocorrida_em,importada_em) VALUES (?,?,?,?,?,?,?,?,?)',
                           (d['origem'], d['registro_id'], 2, 1, 1, 'formulario', d['conteudo'], d['ocorrida_em'], d['importada_em']))
            else:
                db.execute('INSERT INTO item_contexto (cliente_id,processamento_id,categoria,assunto,sujeito,tipo,valor_original,evidencias,gerado_em) SELECT cliente_id,processamento_id,categoria,assunto,sujeito,tipo,?,evidencias,gerado_em FROM item_contexto WHERE id=?',
                           ('Não acompanha mais.', i['id']))
            db.commit()
    if mudanca in ('preferencia', 'contato'):
        # Preparação automática de notícias não é autorização para contato pessoal.
        assert consultar(c)['artigos'] and consultar(c)['vinculos']
        assert c.post('/api/clientes/1/noticias/atualizar').status_code == 200
        return
    assert consultar(c)['artigos'] == [] and consultar(c)['vinculos'] == []
    assert c.post('/api/clientes/1/noticias/atualizar').status_code == 400


def test_item_alheio_rotas_cliente_inexistente_e_corpo_indevido(ambiente):
    _, c, _ = ambiente
    i = aprovar(c, 3)
    assert c.post('/api/clientes/1/noticias/vinculos', json={'item_id': i['id'], 'assunto': 'formula-1'}).status_code == 404
    assert c.get('/api/clientes/999/noticias').status_code == 404
    assert c.post('/api/clientes/999/noticias/atualizar').status_code == 404
    assert c.post('/api/clientes/1/noticias/atualizar', json={}).status_code == 400


def test_vazio_e_sucesso_cli_reutiliza_e_novo_dia_coleta(ambiente):
    app, c, g = ambiente
    vincular(c)
    g.resultado['articles'] = []
    assert atualizar(c)['estado'] == 'atualizado'
    assert consultar(c)['assuntos'][0]['estado'] == 'atualizado' and consultar(c)['artigos'] == []
    r = app.test_cli_runner().invoke(args=['coletar-noticias'])
    assert r.exit_code == 0 and len(g.chamadas) == 1
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1))
    renovar_acesso(c)
    assert consultar(c)['assuntos'][0]['estado'] == 'desatualizado'
    assert atualizar(c)['estado'] == 'atualizado' and len(g.chamadas) == 2


def test_deduplicacao_limite_janela_e_artigos_removidos(ambiente):
    _, c, g = ambiente
    vincular(c)
    g.resultado['articles'] = [artigo(), artigo(url='https://exemplo.test/f1?utm_medium=email'),
        artigo(title='[Removed]', url='https://exemplo.test/removido'),
        artigo(url='https://exemplo.test/velho', publishedAt=(AGORA - timedelta(days=8)).isoformat()),
        *[artigo(url=f'https://exemplo.test/{n}') for n in range(4)]]
    assert atualizar(c)['estado'] == 'atualizado'
    saida = consultar(c)['artigos']
    assert len(saida) == 3 and len({a['url'] for a in saida}) == 3
    assert not any('/velho' in a['url'] or '/removido' in a['url'] for a in saida)


@pytest.mark.parametrize('invalido', [
    artigo(url='javascript:alert(1)'), artigo(url='https://segredo@exemplo.test/x'),
    artigo(url='https://exemplo.test:nao-porta/x'), artigo(publishedAt='data inválida'),
    artigo(publishedAt=(AGORA + timedelta(hours=1)).isoformat()), artigo(source=None),
])
def test_saida_invalida_nao_persiste_parcial(ambiente, invalido):
    app, c, g = ambiente
    vincular(c)
    g.resultado['articles'] = [artigo(), invalido]
    r = atualizar(c)
    assert r['estado'] == 'erro' and r['erro']['status'] == 502
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM artigo_noticia').fetchone()[0] == 0
    assert consultar(c)['artigos'] == []


def test_erro_preserva_cache_intervalo_e_recuperacao(ambiente):
    from app.noticias_rules import ErroNoticias
    app, c, g = ambiente
    vincular(c)
    atualizar(c)
    original = consultar(c)['artigos']
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1))
    renovar_acesso(c)
    def falhar():
        raise ErroNoticias('Provedor indisponível.', status=503, codigo='provedor_indisponivel')
    g.ao_buscar = falhar
    assert atualizar(c)['erro']['status'] == 503
    atual = consultar(c)
    assert atual['artigos'][0]['collectedAt'] == original[0]['collectedAt']
    assert atual['assuntos'][0]['estado'] == 'falhou'
    assert atualizar(c)['erro']['status'] == 409 and len(g.chamadas) == 2
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1, minutes=15))
    g.ao_buscar = None
    assert atualizar(c)['estado'] == 'atualizado' and len(g.chamadas) == 3


def test_cota_conta_falha_bloqueia_outro_assunto_e_reseta_no_dia_local(ambiente):
    from app.noticias_rules import ErroNoticias
    app, c, g = ambiente
    app.config['NEWSAPI_LIMITE_DIARIO'] = 1
    vincular(c)
    vincular(c, 3, 'palmeiras')
    def falhar():
        raise ErroNoticias('Falha fictícia.', status=503)
    g.ao_buscar = falhar
    atualizar(c)
    assert atualizar(c, 3)['erro']['codigo'] == 'cota_local'
    assert len(g.chamadas) == 1 and consultar(c)['chamadas_hoje'] == 1
    app.config['CLOCK'] = relogio_fixo(datetime(2026, 10, 11, 0, tzinfo=TZ))
    renovar_acesso(c)
    g.ao_buscar = None
    assert atualizar(c, 3)['estado'] == 'atualizado' and len(g.chamadas) == 2
    assert consultar(c)['chamadas_hoje'] == 1


@pytest.mark.parametrize('codigo', ['cota_externa', 'limite_provedor'])
def test_erro_global_impede_http_em_outro_assunto(ambiente, codigo):
    from app.noticias_rules import ErroNoticias
    app, c, g = ambiente
    vincular(c)
    vincular(c, 3, 'palmeiras')
    def falhar():
        raise ErroNoticias('Limite do provedor.', status=503, codigo=codigo)
    g.ao_buscar = falhar
    assert atualizar(c)['estado'] == 'erro'
    assert atualizar(c, 3)['erro']['codigo'] == codigo and len(g.chamadas) == 1


def test_concorrencia_e_tentativa_antiga_nao_sobrescrevem(ambiente):
    app, c, g = ambiente
    vincular(c)
    outro = cliente_autenticado(app)
    def concorrente():
        g.ao_buscar = None
        assert atualizar(outro)['erro']['status'] == 409
    g.ao_buscar = concorrente
    assert atualizar(c)['estado'] == 'atualizado' and len(g.chamadas) == 1
    app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1))
    renovar_acesso(c)
    renovar_acesso(outro)
    antiga = artigo(title='ANTIGA', url='https://exemplo.test/antiga')
    g.resultado['articles'] = [antiga]
    def retomar():
        g.ao_buscar = None
        app.config['CLOCK'] = relogio_fixo(AGORA + timedelta(days=1, minutes=2))
        g.resultado['articles'] = [artigo(title='NOVA', url='https://exemplo.test/nova')]
        assert atualizar(outro)['estado'] == 'atualizado'
        # O coletor original devolve a saída antiga após a nova tentativa concluir.
        g.resultado['articles'] = [antiga]
    g.ao_buscar = retomar
    assert atualizar(c)['erro']['status'] == 409
    assert consultar(c)['artigos'][0]['title'] == 'NOVA'
    assert len(g.chamadas) == 3


def test_feedback_motivo_isolamento_idempotencia_persistencia(ambiente):
    app, c, _ = ambiente
    vincular(c)
    vincular(c, 3)
    atualizar(c)
    antes = c.get('/api/clientes/1').get_json()
    a = consultar(c)['artigos'][0]['id']
    assert c.post('/api/clientes/1/noticias/descartar', json={'artigo_id': a, 'motivo': ' '}).status_code == 400
    corpo = {'artigo_id': a, 'motivo': 'Não é pertinente para este atendimento fictício.'}
    assert c.post('/api/clientes/2/noticias/descartar', json=corpo).status_code == 404
    assert c.post('/api/clientes/1/noticias/descartar', json=corpo).status_code == 200
    assert c.post('/api/clientes/1/noticias/descartar', json=corpo).status_code == 200
    assert consultar(c)['artigos'] == [] and consultar(c, 3)['artigos']
    assert len(consultar(c)['vinculos']) == 1 and c.get('/api/clientes/1').get_json() == antes
    outro = cliente_autenticado(create_app(dict(app.config)))
    assert consultar(outro)['artigos'] == []
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM descarte_noticia').fetchone()[0] == 1


def test_sem_chave_nao_conta_tentativa_e_limite_invalido(ambiente):
    app, c, g = ambiente
    vincular(c)
    app.config.update(COLETOR_NOTICIAS=None, NEWSAPI_API_KEY='')
    assert atualizar(c)['erro']['codigo'] == 'noticias_nao_configuradas'
    assert consultar(c)['chamadas_hoje'] == 0 and not g.chamadas
    app.config.update(COLETOR_NOTICIAS=g, NEWSAPI_LIMITE_DIARIO=101)
    assert atualizar(c)['erro']['codigo'] == 'configuracao_invalida' and not g.chamadas


def test_pergunta_noticias_le_cache_com_fontes_e_respeita_bloqueio(ambiente):
    _, c, g = ambiente
    vincular(c)
    atualizar(c)
    r = c.post('/api/pulse/clientes/1/perguntar', json={'pergunta': 'Quais notícias estão disponíveis?'})
    saida = r.get_json()
    assert 'Notícia fictícia' in saida['resposta'] and 'publicada' in saida['resposta']
    assert any('https://exemplo.test/f1' in f for f in saida['fontes'])
    assert len(g.chamadas) == 1
    c.post('/api/clientes/1/assuntos/formula-1', json={'bloqueado': True, 'motivo': 'Não abordar.'})
    r = c.post('/api/pulse/clientes/1/perguntar', json={'pergunta': 'Quais notícias?'})
    assert not r.get_json()['fontes'] and 'Não há notícias' in r.get_json()['resposta']


def test_transportadora_envia_apenas_consulta_e_cabecalho(monkeypatch):
    from app.newsapi import NewsAPI
    from app.noticias_rules import CATALOGO
    def abrir(req, timeout):
        assert req.get_header('X-api-key') == 'segredo-ficticio' and timeout == 15
        q = parse_qs(urlsplit(req.full_url).query)
        assert q['language'] == ['pt'] and q['pageSize'] == ['10'] and q['page'] == ['1']
        assert 'apiKey' not in q and q['q'] == [CATALOGO['formula-1']['q']]
        assert q['from'] == [(AGORA - timedelta(days=7)).isoformat()]
        return io.BytesIO(json.dumps({'status': 'ok', 'articles': []}).encode())
    monkeypatch.setattr('app.newsapi.abrir', abrir)
    assert NewsAPI('segredo-ficticio').buscar(CATALOGO['formula-1'], AGORA)['articles'] == []


@pytest.mark.parametrize('falha,codigo,status', [
    (HTTPError('https://newsapi.org', 401, 'segredo-bruto', {}, io.BytesIO(b'{"message":"segredo"}')), 'credencial_recusada', 503),
    (HTTPError('https://newsapi.org', 429, 'segredo-bruto', {}, io.BytesIO(b'{"code":"rateLimited"}')), 'limite_provedor', 503),
    (HTTPError('https://newsapi.org', 429, 'segredo-bruto', {}, io.BytesIO(b'{"code":"apiKeyExhausted"}')), 'cota_externa', 503),
    (URLError('segredo-bruto'), 'provedor_indisponivel', 503),
    (TimeoutError('segredo-bruto'), 'provedor_indisponivel', 503),
    (b'html invalido segredo-bruto', 'saida_noticias_invalida', 502),
])
def test_transporte_falhas_sem_vazar_corpo(monkeypatch, falha, codigo, status):
    from app.newsapi import NewsAPI
    from app.noticias_rules import CATALOGO, ErroNoticias
    def abrir(*args, **kwargs):
        if isinstance(falha, Exception):
            raise falha
        return io.BytesIO(falha)
    monkeypatch.setattr('app.newsapi.abrir', abrir)
    with pytest.raises(ErroNoticias) as e:
        NewsAPI('segredo-ficticio').buscar(CATALOGO['formula-1'], AGORA)
    assert e.value.codigo == codigo and e.value.status == status
    assert 'segredo' not in e.value.mensagem
