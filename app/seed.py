"""Dados fictícios com datas relativas a 'hoje' (demo e testes não envelhecem)."""
from datetime import date, timedelta

import click
from flask import Flask

from .db import get_db, init_db

AVISO = "Dados fictícios para demonstração"


def seed_db(hoje: date) -> None:
    db = get_db()
    d = lambda dias: (hoje + timedelta(days=dias)).isoformat()  # noqa: E731
    aniv = hoje + timedelta(days=3)
    clientes = [
        ("Ana Souza (fictício)", "Moderado; objetivo: aposentadoria", 1, "positivo", "Satisfeita com a carteira."),
        ("Bruno Lima (fictício)", "Conservador", 0, "atencao", "Pediu revisão da carteira."),
        ("Carla Mendes (fictício)", "Arrojado", 1, None, ""),
    ]
    for nome, perfil, permite, estado, just in clientes:
        db.execute(
            "INSERT INTO cliente (nome, perfil, permite_assuntos_pessoais, estado_relacionamento, justificativa)"
            " VALUES (?,?,?,?,?)",
            (nome, perfil, permite, estado, just),
        )
    posicoes = [
        (1, "CDB Banco Exemplo", "50000.00", d(5)),
        (1, "LCI Banco Exemplo", "30000.00", d(45)),
        (2, "Debênture Exemplo", "20000.00", d(-2)),
        (2, "Tesouro Exemplo", "10000.00", d(20)),
        (3, "CRA Exemplo", "80000.00", d(120)),
    ]
    for cid, ativo, valor, venc in posicoes:
        db.execute(
            "INSERT INTO posicao (cliente_id, ativo, valor, vencimento, fonte) VALUES (?,?,?,?,?)",
            (cid, ativo, valor, venc, AVISO),
        )
    db.execute(
        "INSERT INTO data_importante (cliente_id, tipo, vinculo, descricao, dia, mes) VALUES (1,'aniversario','familiar','filha',?,?)",
        (aniv.day, aniv.month),
    )
    db.execute(
        "INSERT INTO data_importante (cliente_id, tipo, vinculo, descricao, dia, mes) VALUES (2,'aniversario','cliente','próprio',?,?)",
        (aniv.day, aniv.month),
    )
    db.execute(
        "INSERT INTO interacao (cliente_id, canal, texto, data_hora, proximos_passos) VALUES (1,'telefone',?,?,?)",
        ("Conversa sobre vencimento do CDB.", f"{d(-3)}T10:00:00-03:00", "Enviar opções de reinvestimento."),
    )
    db.commit()


def init_app(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Recria o banco com dados fictícios."""
        db = get_db()
        for tabela in ("alerta", "interacao", "data_importante", "posicao", "cliente"):
            db.execute(f"DROP TABLE IF EXISTS {tabela}")
        db.commit()
        init_db()
        seed_db(app.config["HOJE"]())
        click.echo("Banco populado com dados fictícios.")
