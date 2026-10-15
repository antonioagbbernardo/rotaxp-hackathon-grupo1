from datetime import timedelta
from app import create_app
from app.db import get_db
from app.autenticacao import criar_acesso
from test_autenticacao import entrar


def test_contas_tem_bancos_isolados_e_demo_fica_desativada(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'controle.db')})
    demo=app.test_client()
    assert entrar(demo).status_code==200
    with app.app_context():
        criar_acesso('ana','senha-longa-ana-123','Assessora Ana')
        criar_acesso('bia','senha-longa-bia-123','Assessora Bia')
    assert demo.get('/api/clientes').status_code==401
    a,b=app.test_client(),app.test_client()
    assert entrar(a).status_code == 401
    ta=entrar(a,'ana','senha-longa-ana-123').get_json()['csrf_token']
    tb=entrar(b,'bia','senha-longa-bia-123').get_json()['csrf_token']
    assert a.get('/api/pulse/assessor').get_json()['name']=='Assessora Ana'
    assert b.get('/api/pulse/assessor').get_json()['name']=='Assessora Bia'
    # Mesmo ID em bases diferentes não pode vazar via detalhe, chat ou agenda.
    with a.session_transaction() as sess:
        assert 'senha' not in dict(sess) and 'database' not in dict(sess)
    with app.app_context():
        from app.autenticacao import banco_usuario
        from flask import g
        g.tenant_database=banco_usuario('ana')
        get_db().execute("INSERT INTO cliente(id,nome) VALUES(1,'Cliente da Ana')")
        get_db().commit()
    assert len(a.get('/api/clientes').get_json()['clientes'])==1
    assert b.get('/api/clientes').get_json()['clientes']==[]
    for path in ('/api/clientes/1','/api/pulse/clientes/1/chat','/api/clientes/1/reunioes'):
        assert b.get(path).status_code==404
    assert b.post('/api/clientes/1/interacoes',json={'canal':'telefone','texto':'Invadir'},headers={'X-CSRF-Token':tb}).status_code==404
    assert a.post('/api/clientes/1/interacoes',json={'canal':'telefone','texto':'Contato da Ana'},headers={'X-CSRF-Token':ta}).status_code==201
    assert b.get('/api/reunioes').get_json()=={'reunioes':[]}
    novo=create_app(dict(app.config))
    outro=novo.test_client()
    assert entrar(outro,'ana','senha-longa-ana-123').status_code==200
    assert outro.get('/api/clientes').get_json()['clientes'][0]['nome']=='Cliente da Ana'


def test_login_limita_tentativas_com_persistencia_e_expiracao(tmp_path):
    from app.clock import relogio_fixo,TZ
    from datetime import datetime
    agora=datetime(2026,10,15,12,tzinfo=TZ)
    config={'TESTING':True,'DATABASE':str(tmp_path/'controle.db'),'CLOCK':relogio_fixo(agora)}
    app=create_app(config)
    c=app.test_client()
    for _ in range(5):
        assert entrar(c,'admin','errada').status_code==401
    r=entrar(c)
    assert r.status_code==429 and int(r.headers['Retry-After'])>0
    novo=create_app(config)
    assert entrar(novo.test_client()).status_code==429
    novo.config['CLOCK']=relogio_fixo(agora+timedelta(minutes=16))
    assert entrar(novo.test_client()).status_code==200


def test_demo_pode_ser_desativada_sem_credencial_embutida(tmp_path):
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'controle.db'),'PULSE_DEMO_LOGIN':False})
    assert entrar(app.test_client()).status_code==401


def test_worker_processa_cada_assessor_na_sua_base(tmp_path,monkeypatch):
    from app import agendador
    app=create_app({'TESTING':True,'DATABASE':str(tmp_path/'controle.db')})
    with app.app_context():
        criar_acesso('ana','senha-longa-ana-123','Ana')
        criar_acesso('bia','senha-longa-bia-123','Bia')
        monkeypatch.setattr(agendador,'executar_ciclo',lambda: {'nome':get_db().execute('SELECT nome FROM assessor WHERE id=1').fetchone()['nome']})
        resultado=agendador.executar_instalacao()
    assert resultado=={'assessores':[{'usuario':'ana','resultado':{'nome':'Ana'}},{'usuario':'bia','resultado':{'nome':'Bia'}}]}
