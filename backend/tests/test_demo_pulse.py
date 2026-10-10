from app import create_app
from app.clock import relogio_fixo
from app.db import get_db
from app.seed import seed_db
from app.demo_pulse import popular
from test_pulse import AGORA


def test_carga_enriquecida_preserva_base_e_nao_duplica(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'demo.db'), 'CLOCK': relogio_fixo(AGORA), 'OPENAI_API_KEY': '', 'NEWSAPI_API_KEY': ''})
    with app.app_context():
        seed_db(AGORA.date(), AGORA)
        db = get_db()
        original = dict(db.execute('SELECT * FROM interacao WHERE id=1').fetchone())
        assert popular()
        assert db.execute('SELECT COUNT(*) FROM cliente').fetchone()[0] == 10
        assert db.execute("SELECT COUNT(*) FROM documento_fonte WHERE origem='demo-pulse-v2' AND tipo='interacao'").fetchone()[0] == 50
        assert db.execute('SELECT COUNT(*) FROM reuniao').fetchone()[0] == 10
        assert dict(db.execute('SELECT * FROM interacao WHERE id=1').fetchone()) == original
        assert not popular()
        assert db.execute('SELECT COUNT(*) FROM reuniao').fetchone()[0] == 10
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        from app.pulse import consultar_painel
        clientes = consultar_painel()['clients']
        assert len(clientes) == 10
        assert all(c['positions'] and c['interests'] and c['photoUrl'] for c in clientes)
        assert all(c['email'].endswith('@example.com') for c in clientes)
