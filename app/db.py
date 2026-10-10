import sqlite3

import click
from flask import Flask, current_app, g

# Dinheiro: TEXT com Decimal (nunca float). Datas: YYYY-MM-DD. Instantes: ISO 8601 com offset.
SCHEMA = """
CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT '',
    permite_assuntos_pessoais INTEGER NOT NULL DEFAULT 0,
    estado_relacionamento TEXT CHECK (estado_relacionamento IN ('positivo','atencao','negativo')),
    justificativa TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS posicao (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    ativo TEXT NOT NULL,
    valor TEXT NOT NULL,
    vencimento TEXT NOT NULL,
    fonte TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interacao (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    canal TEXT NOT NULL CHECK (canal IN ('whatsapp','email','telefone','presencial')),
    texto TEXT NOT NULL CHECK (length(trim(texto)) > 0),
    data_hora TEXT NOT NULL,
    proximos_passos TEXT
);
CREATE TABLE IF NOT EXISTS data_importante (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('aniversario')),
    vinculo TEXT NOT NULL CHECK (vinculo IN ('cliente','familiar')),
    descricao TEXT NOT NULL DEFAULT '',
    dia INTEGER NOT NULL CHECK (dia BETWEEN 1 AND 31),
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    fonte TEXT NOT NULL DEFAULT 'Registro manual do assessor'
);
CREATE TABLE IF NOT EXISTS alerta (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('vencimento','vencido','aniversario')),
    prioridade TEXT NOT NULL CHECK (prioridade IN ('alta','media','baixa')),
    motivo TEXT NOT NULL,
    fonte TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendente' CHECK (estado IN ('pendente','tratado')),
    chave_ocorrencia TEXT NOT NULL,
    data_referencia TEXT NOT NULL,
    UNIQUE (cliente_id, chave_ocorrencia)
);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    get_db().executescript(SCHEMA)


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        click.echo("Banco inicializado.")
