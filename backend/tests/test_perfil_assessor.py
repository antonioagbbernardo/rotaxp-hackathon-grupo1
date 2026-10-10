"""RF32: persistência, validação atômica e proteção do perfil."""
from datetime import datetime
import sqlite3

import pytest
from app import create_app
from app.clock import TZ, relogio_fixo
from app.db import get_db
from app.seed import seed_db
from client_autenticado import cliente_autenticado

PERFIL = {'name': 'Marina Fictícia', 'role': 'Assessora de investimentos',
          'email': 'marina@example.com', 'phone': '+55 (11) 99999-0000', 'office': 'Escritório fictício'}


@pytest.fixture
def ambiente(tmp_path):
    agora = datetime(2026, 10, 10, 15, tzinfo=TZ)
    config = {'TESTING': True, 'DATABASE': str(tmp_path / 'perfil.db'),
              'CLOCK': relogio_fixo(agora), 'SECRET_KEY': 'perfil-ficticio-testes'}
    app = create_app(config)
    with app.app_context():
        seed_db(agora.date(), agora)
    return app, cliente_autenticado(app), config


def test_persiste_no_reinicio_e_atualiza_painel(ambiente):
    app, c, config = ambiente
    antes = c.get('/api/pulse').get_json()['clients']
    r = c.put('/api/pulse/assessor', json={k: f'  {v}  ' for k, v in PERFIL.items()})
    assert r.status_code == 200 and r.get_json() == PERFIL
    novo = cliente_autenticado(create_app(config))
    assert novo.get('/api/pulse/assessor').get_json() == PERFIL
    painel = novo.get('/api/pulse').get_json()
    assert painel['advisor'] == {'name': PERFIL['name'], 'role': PERFIL['role']}
    assert painel['clients'] == antes


@pytest.mark.parametrize('campo,valor', [('name', ''), ('name', 'x'*121), ('role', ' '),
    ('role', 'x'*81), ('email', 'sem-arroba'), ('email', 'a@dominio'), ('email', 'x'*255),
    ('phone', 'abc'), ('phone', '+' ), ('phone', '1'*31), ('office', 'x'*121),
    ('name', None), ('email', 123)])
def test_invalido_nao_persiste(ambiente, campo, valor):
    _, c, _ = ambiente
    antes = c.get('/api/pulse/assessor').get_json()
    r = c.put('/api/pulse/assessor', json={**PERFIL, campo: valor})
    assert r.status_code == 400
    assert r.get_json()['erro']['campo'] == campo
    assert c.get('/api/pulse/assessor').get_json() == antes


def test_campos_ausentes_extras_e_corpo(ambiente):
    _, c, _ = ambiente
    for dados, campo in [(None, 'corpo'), ([], 'corpo'), ({}, 'name'),
                         ({**PERFIL, 'senha': 'nova'}, 'senha')]:
        r = c.put('/api/pulse/assessor', json=dados)
        assert r.status_code == 400 and r.get_json()['erro']['campo'] == campo
    opcional = {**PERFIL, 'email': '', 'phone': '', 'office': ''}
    assert c.put('/api/pulse/assessor', json=opcional).get_json() == opcional


def test_sessao_csrf_e_assessor_ausente(ambiente):
    app, c, _ = ambiente
    anonimo = app.test_client()
    assert anonimo.get('/api/pulse/assessor').status_code == 401
    assert anonimo.put('/api/pulse/assessor', json=PERFIL).status_code == 401
    assert c.put('/api/pulse/assessor', json=PERFIL, headers={'X-CSRF-Token': ''}).status_code == 403
    vazio = create_app({**app.config, 'DATABASE': app.config['DATABASE'] + '.vazio'})
    assert cliente_autenticado(vazio).get('/api/pulse/assessor').status_code == 404


def test_migracao_preserva_nome_id_e_defaults(tmp_path):
    caminho = str(tmp_path / 'antigo.db')
    with sqlite3.connect(caminho) as db:
        db.execute('CREATE TABLE assessor (id INTEGER PRIMARY KEY, nome TEXT NOT NULL)')
        db.execute("INSERT INTO assessor VALUES (1, 'Nome fictício anterior')")
    app = create_app({'TESTING': True, 'DATABASE': caminho, 'SECRET_KEY': 'teste-migracao'})
    with app.app_context():
        row = get_db().execute('SELECT * FROM assessor').fetchone()
        assert row['id'] == 1 and row['nome'] == 'Nome fictício anterior'
        assert row['cargo'] == 'Assessor de investimentos' and row['email'] == ''
