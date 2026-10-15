from app import create_app
from app.db import get_db
from app.seed import seed_db
from app.demo_pulse import popular
from client_autenticado import cliente_autenticado


def test_lista_paginada_e_detalhe_preservam_prioridade_sem_historicos_no_cartao(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'teste.db')})
    with app.app_context():
        seed_db(app.config['CLOCK'].hoje(),app.config['CLOCK'].agora())
        popular()
    c=cliente_autenticado(app)
    full=c.get('/api/pulse').get_json()
    lista=c.get('/api/pulse?visao=lista&limite=3').get_json()
    assert lista['pagination']=={'page':1,'limit':3,'total':10,'pages':4}
    assert [i['id'] for i in lista['clients']]==[i['id'] for i in full['clients'][:3]]
    for card in lista['clients']:
        assert 'sourceDocuments' not in card and 'interactions' not in card
        detail=c.get('/api/pulse/clientes/'+card['id']).get_json()
        assert card['sentiment']==detail['sentiment'] and card['priority']==detail['priority']
        assert detail['sourceDocuments']
    page2=c.get('/api/pulse?visao=lista&limite=3&pagina=2').get_json()
    assert not {i['id'] for i in lista['clients']} & {i['id'] for i in page2['clients']}
    assert c.get('/api/pulse?visao=lista&pagina=0').status_code==400
    assert c.get('/api/pulse?visao=lista&limite=101').status_code==400


def test_numero_consultas_lista_nao_cresce_por_cliente(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'teste.db')})
    with app.app_context():
        seed_db(app.config['CLOCK'].hoje(),app.config['CLOCK'].agora())
        popular()
        from app.painel_lista import listar
        db=get_db()
        queries=[]
        db.set_trace_callback(queries.append)
        assert len(listar()['clients'])==10
        assert len(queries)<=12
        db.set_trace_callback(None)
