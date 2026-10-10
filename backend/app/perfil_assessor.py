"""Consulta e atualização do assessor único, sem alterar acesso ou clientes."""
from .agenda_rules import ErroAgenda
from .db import get_db
from .perfil_assessor_rules import validar_perfil
from .seed import ASSESSOR_ID


def consultar():
    row = get_db().execute('SELECT * FROM assessor WHERE id=?', (ASSESSOR_ID,)).fetchone()
    if row is None:
        raise ErroAgenda('Assessor não cadastrado. Inicialize a base fictícia.', 'assessor', 404)
    return {'name': row['nome'], 'role': row['cargo'], 'email': row['email'],
            'phone': row['telefone'], 'office': row['escritorio']}


def salvar(dados):
    perfil = validar_perfil(dados)
    consultar()
    db = get_db()
    with db:
        db.execute('UPDATE assessor SET nome=?, cargo=?, email=?, telefone=?, escritorio=? WHERE id=?',
                   (perfil['name'], perfil['role'], perfil['email'], perfil['phone'], perfil['office'], ASSESSOR_ID))
    return perfil
