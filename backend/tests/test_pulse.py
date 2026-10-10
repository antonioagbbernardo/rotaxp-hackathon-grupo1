from client_autenticado import cliente_autenticado
from datetime import datetime

import pytest

from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from test_contexto import ExtratorSimulado
from test_fontes import documento, lote

AGORA = datetime(2026, 10, 10, 15, tzinfo=TZ)


@pytest.fixture
def ambiente(tmp_path):
    extrator = ExtratorSimulado()
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "pulse.db"),
                      "CLOCK": relogio_fixo(AGORA), "EXTRATOR_IA": extrator,
                      "FRONTEND_DIST": str(tmp_path / "dist")})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
    return app, cliente_autenticado(app), extrator


def clientes(c):
    r = c.get('/api/pulse')
    assert r.status_code == 200
    return r.get_json()['clients']


def perguntar(c, texto, cid=1):
    return c.post(f'/api/pulse/clientes/{cid}/perguntar', json={'pergunta': texto})


def test_lista_real_ordenada_sem_ia_e_ausencias_explicitas(ambiente):
    _, c, e = ambiente
    dados = c.get('/api/pulse').get_json()
    assert dados['advisor']['name'] == 'Assessor Fictício'
    assert [i['id'] for i in dados['clients']] == [str(i['id']) for i in c.get('/api/clientes').get_json()['clientes']]
    ana = next(i for i in dados['clients'] if i['id'] == '1')
    assert ana['portfolio']['total'] == '80000.00' and ana['portfolio']['allocation'] == []
    assert ana['clientSince'] is None and ana['whatsapp'] == '' and ana['email'] == ''
    assert ana['news'] == [] and ana['sentiment'] == 'unknown'
    assert ana['relationshipLabel'] == 'Não avaliado' and ana['lastContactDays'] == 10
    assert not e.chamadas


def test_total_decimal_exato_e_ausencia_nao_vira_carteira_zero(ambiente):
    app, c, _ = ambiente
    with app.app_context():
        db = get_db()
        db.execute("UPDATE posicao SET valor='9007199254740993.01' WHERE id=1")
        db.commit()
    ana = next(i for i in clientes(c) if i['id'] == '1')
    assert ana['portfolio']['total'] == '9007199254770993.01'
    eva = next(i for i in clientes(c) if i['id'] == '5')
    assert eva['portfolio']['total'] is None and eva['lastContactDays'] is None


def test_propostas_nao_viram_interesse_revisado_e_bloqueio_nao_usa_rascunho(ambiente):
    app, c, e = ambiente
    c.post('/api/fontes/importar', json=lote())
    c.post('/api/clientes/1/contexto/processar')
    ana = next(i for i in clientes(c) if i['id'] == '1')
    assert ana['interests'] == [] and len(ana['context']['itens']) == 1
    item = ana['context']['itens'][0]
    c.post(f"/api/clientes/1/contexto/{item['id']}/revisar", json={'acao': 'aprovar', 'motivo': 'Conferido', 'revisao': 0})
    c.post('/api/clientes/1/assuntos/formula-1', json={'bloqueado': True, 'motivo': 'Não abordar'})
    ana = next(i for i in clientes(c) if i['id'] == '1')
    assert ana['interests'] and ana['context']['itens'][0]['bloqueado']
    assert all('Fórmula' not in i['text'] for i in ana['assistant']['openings'])
    assert len(e.chamadas) == 1


@pytest.mark.parametrize('texto,trecho', [('Qual o perfil?', 'Moderado'), ('Quais os vencimentos?', 'CDB'),
                                       ('Quando foi o último contato?', 'telefone'), ('Quais preferências?', '7')])
def test_pergunta_basica_responde_com_fontes_do_cliente(ambiente, texto, trecho):
    _, c, e = ambiente
    r = perguntar(c, texto)
    assert r.status_code == 200
    dados = r.get_json()
    assert trecho in dados['resposta'] and dados['fontes'] and dados['modo'] == 'consulta_contexto'
    assert 'Bruno' not in dados['resposta'] and not e.chamadas


def test_pergunta_sem_dado_ou_fora_de_escopo_nao_inventa(ambiente):
    _, c, _ = ambiente
    for texto in ('Qual notícia saiu hoje?', 'Qual o telefone?', 'Quem ganhou a corrida?'):
        r = perguntar(c, texto)
        assert r.status_code == 200 and r.get_json()['fontes'] == []
    assert perguntar(c, 'Qual o perfil?', cid=999).status_code == 404


def test_preferencia_e_ultimo_contato_com_nome_do_canal_nao_viram_ausencia(ambiente):
    _, c, e = ambiente
    assert 'Canal preferido: telefone' in perguntar(c, 'Prefere WhatsApp ou telefone?').get_json()['resposta']
    assert 'Último contato: telefone' in perguntar(c, 'Qual o último contato por telefone?').get_json()['resposta']
    assert not e.chamadas


def test_revisao_atualiza_cartao_sem_mudar_data_do_ultimo_contato(ambiente):
    _, c, _ = ambiente
    c.post('/api/fontes/importar', json=lote())
    c.post('/api/clientes/1/contexto/processar')
    ana = next(i for i in clientes(c) if i['id'] == '1')
    item = ana['context']['itens'][0]
    c.application.config['CLOCK'] = relogio_fixo(AGORA.replace(hour=16))
    c.post(f"/api/clientes/1/contexto/{item['id']}/revisar", json={'acao': 'aprovar', 'motivo': 'Conferido', 'revisao': 0})
    depois = next(i for i in clientes(c) if i['id'] == '1')
    assert depois['updatedMinutesAgo'] == 0
    assert depois['lastContactDays'] == ana['lastContactDays']


@pytest.mark.parametrize('corpo', [{}, {'pergunta': ''}, {'pergunta': 'x' * 501}, {'pergunta': 'perfil', 'modelo': 'outro'}, []])
def test_pergunta_invalida(ambiente, corpo):
    _, c, _ = ambiente
    assert c.post('/api/pulse/clientes/1/perguntar', json=corpo).status_code == 400


def test_tratamento_alerta_atualiza_visao_e_relacionamento_nao_altera_prioridade(ambiente):
    _, c, _ = ambiente
    ana = next(i for i in clientes(c) if i['id'] == '1')
    assert ana['priority'] == 'alta'
    c.post('/api/clientes/1/relacionamento', json={'estado': 'positivo', 'justificativa': 'Conferido'})
    depois = next(i for i in clientes(c) if i['id'] == '1')
    assert depois['priority'] == 'alta' and depois['relationshipLabel'] == 'Positivo'
    a = next(a for a in ana['alerts'] if a['regra'] == 'vencimento')
    c.post('/api/alertas/tratar', json={'cliente_id': 1, 'chave_ocorrencia': a['chave_ocorrencia']})
    assert next(i for i in clientes(c) if i['id'] == '1')['priority'] == 'media'


def test_build_servido_pelo_flask_e_legacy_preservado(ambiente, tmp_path):
    _, c, _ = ambiente
    dist = tmp_path / 'dist'
    (dist / 'assets').mkdir(parents=True)
    (dist / 'index.html').write_text('<html>XP Pulse integrado</html>')
    (dist / 'assets' / 'teste.js').write_text('const pulse = true;')
    (dist / 'favicon.svg').write_text('<svg></svg>')
    assert b'XP Pulse integrado' in c.get('/').data
    assert c.get('/assets/teste.js').status_code == 200
    assert c.get('/favicon.svg').status_code == 200
    assert c.get('/legacy').status_code == 200
    assert c.get('/api/rota-inexistente').status_code == 404
    assert c.get('/assets/../index.html').status_code == 404


def test_base_vazia_nao_faz_fallback_mock(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'vazia.db')})
    assert clientes(cliente_autenticado(app)) == []
