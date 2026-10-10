"""Dados fictícios com vencimentos relativos à data de execução (−2, 0, 5, 7, 8, 30, 31 dias)."""
from datetime import date, datetime, timedelta

import click
from flask import Flask

from .clock import formatar_utc
from .db import drop_all, get_db, init_db

AVISO = "Dados fictícios para demonstração"
ASSESSOR_ID = 1


def seed_db(hoje: date, agora: datetime) -> bool:
    """Popula somente base vazia. Devolve False (sem alterar nada) se já houver dados."""
    db = get_db()
    if db.execute("SELECT 1 FROM cliente LIMIT 1").fetchone() or db.execute("SELECT 1 FROM assessor LIMIT 1").fetchone():
        return False
    d = lambda dias: (hoje + timedelta(days=dias)).isoformat()  # noqa: E731
    em = lambda dias: formatar_utc(agora - timedelta(days=dias))  # noqa: E731
    aniv = lambda dias: hoje + timedelta(days=dias)  # noqa: E731

    db.execute("INSERT INTO assessor (id, nome) VALUES (?, ?)", (ASSESSOR_ID, "Assessor Fictício"))
    clientes = [  # id, nome, perfil, canal, intervalo, permite
        (1, "Ana Souza (fictício)", "Moderado; objetivo: aposentadoria", "telefone", 7, 1),
        (2, "Bruno Lima (fictício)", "Conservador", "email", 14, 0),
        (3, "Carla Mendes (fictício)", "Arrojado", "whatsapp", 14, 1),
        (4, "Diego Rocha (fictício)", "Moderado", None, 7, 0),
        (5, "Eva Martins (fictício)", "", None, 30, 1),
    ]
    for c in clientes:
        db.execute(
            "INSERT INTO cliente (id, nome, perfil, canal_preferido, intervalo_minimo_dias, permite_assuntos_pessoais)"
            " VALUES (?,?,?,?,?,?)", c)
    posicoes = [  # cliente, ativo, valor, Δ
        (1, "CDB Banco Exemplo", "50000.00", 5),
        (1, "LCI Banco Exemplo", "30000.00", 31),
        (2, "Debênture Exemplo", "20000.00", -2),
        (2, "Tesouro Exemplo", "10000.00", 0),
        (3, "CRA Exemplo", "80000.00", 7),
        (3, "LCA Exemplo", "15000.00", 8),
        (4, "CDB Exemplo 2", "25000.00", 30),
    ]
    for cid, ativo, valor, delta in posicoes:
        db.execute("INSERT INTO posicao (cliente_id, ativo, valor, vencimento, fonte) VALUES (?,?,?,?,?)",
                   (cid, ativo, valor, d(delta), AVISO))
    datas = [(1, "familiar", "filha", aniv(3)), (2, "cliente", "próprio", aniv(3)), (3, "familiar", "esposa", aniv(5))]
    for cid, vinculo, desc, quando in datas:
        db.execute(
            "INSERT INTO data_importante (cliente_id, tipo, vinculo, descricao, dia, mes) VALUES (?,?,?,?,?,?)",
            (cid, "aniversario", vinculo, desc, quando.day, quando.month))
    interacoes = [  # cliente, canal, texto, dias atrás, próximos passos
        (1, "telefone", "Conversa sobre vencimento do CDB.", 10, "Enviar opções de reinvestimento."),
        (2, "email", "Cliente pediu revisão da carteira.", 4, None),
        (3, "whatsapp", "Alinhamento sobre metas do ano.", 20, "Agendar reunião de revisão."),
    ]
    for cid, canal, texto, dias, passos in interacoes:
        db.execute(
            "INSERT INTO interacao (cliente_id, canal, texto, ocorrida_em, registrada_em, proximos_passos, assessor_id)"
            " VALUES (?,?,?,?,?,?,?)", (cid, canal, texto, em(dias), em(dias), passos, ASSESSOR_ID))
    db.execute(
        "INSERT INTO avaliacao_relacionamento (cliente_id, estado, justificativa, assessor_id, avaliada_em)"
        " VALUES (2, 'atencao', 'Pediu revisão da carteira e há vencimentos pendentes.', ?, ?)",
        (ASSESSOR_ID, em(4)))
    db.commit()
    return True


def init_app(app: Flask) -> None:
    from . import demo_pulse
    demo_pulse.init_app(app)
    @app.cli.command("seed")
    def seed_command():
        """Popula dados fictícios somente se a base estiver vazia."""
        init_db()
        clock = app.config["CLOCK"]
        if seed_db(clock.hoje(), clock.agora()):
            click.echo("Banco populado com dados fictícios.")
        else:
            click.echo("Base já possui dados; nada foi alterado (use reset-demo para reconstruir).")

    @app.cli.command("reset-demo")
    def reset_command():
        """Apaga tudo e reconstrói os dados fictícios da demonstração."""
        drop_all()
        init_db()
        clock = app.config["CLOCK"]
        seed_db(clock.hoje(), clock.agora())
        click.echo("Demonstração reconstruída.")
