import sqlite3

import click
from flask import Flask, current_app, g

# Dinheiro: TEXT com Decimal (nunca float). Datas: YYYY-MM-DD. Instantes: UTC ISO 8601.
# O alerta NÃO é persistido (calculado sob demanda); só o tratamento (tratamento_alerta).
TABELAS = ("sessao_acesso", "descarte_noticia", "coleta_artigo_noticia", "artigo_noticia", "coleta_noticia", "vinculo_noticia",
           "resumo_ia", "historico_assunto", "preferencia_assunto", "revisao_contexto", "item_contexto", "processamento_contexto",
           "documento_fonte", "tratamento_alerta", "avaliacao_relacionamento", "interacao", "data_importante",
           "posicao", "cliente", "assessor")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessao_acesso (
    token_hash TEXT PRIMARY KEY, expira_em INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS vinculo_noticia (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    item_id INTEGER NOT NULL REFERENCES item_contexto(id), revisao INTEGER NOT NULL,
    assunto TEXT NOT NULL, assessor_id INTEGER NOT NULL REFERENCES assessor(id), criada_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS vinculo_noticia_cliente ON vinculo_noticia(cliente_id,item_id);
CREATE TABLE IF NOT EXISTS coleta_noticia (
    id INTEGER PRIMARY KEY, assunto TEXT NOT NULL, consulta_versao TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('em_processamento','concluido','falhou')),
    inicio_em TEXT NOT NULL, fim_em TEXT, erro_codigo TEXT, erro_mensagem TEXT
);
CREATE INDEX IF NOT EXISTS coleta_noticia_assunto ON coleta_noticia(assunto,consulta_versao,id);
CREATE TABLE IF NOT EXISTS artigo_noticia (url TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS coleta_artigo_noticia (
    coleta_id INTEGER NOT NULL REFERENCES coleta_noticia(id),
    artigo_id TEXT NOT NULL REFERENCES artigo_noticia(url), dados TEXT NOT NULL,
    PRIMARY KEY (coleta_id,artigo_id)
);
CREATE TABLE IF NOT EXISTS descarte_noticia (
    cliente_id INTEGER NOT NULL REFERENCES cliente(id), artigo_id TEXT NOT NULL REFERENCES artigo_noticia(url),
    motivo TEXT NOT NULL CHECK (length(trim(motivo))>0), assessor_id INTEGER NOT NULL REFERENCES assessor(id),
    descartada_em TEXT NOT NULL, PRIMARY KEY (cliente_id,artigo_id)
);
CREATE TABLE IF NOT EXISTS resumo_ia (
    cliente_id INTEGER PRIMARY KEY REFERENCES cliente(id),
    assinatura TEXT NOT NULL, tentativa TEXT NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('em_processamento','concluido','falhou')),
    inicio_em TEXT NOT NULL, resposta TEXT
);
CREATE TABLE IF NOT EXISTS assessor (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT '',
    canal_preferido TEXT CHECK (canal_preferido IN ('whatsapp','email','telefone','presencial')),
    intervalo_minimo_dias INTEGER NOT NULL DEFAULT 7 CHECK (intervalo_minimo_dias IN (7,14,30)),
    permite_assuntos_pessoais INTEGER NOT NULL DEFAULT 0 CHECK (permite_assuntos_pessoais IN (0,1))
);
CREATE TABLE IF NOT EXISTS avaliacao_relacionamento (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    estado TEXT NOT NULL CHECK (estado IN ('positivo','atencao','negativo')),
    justificativa TEXT NOT NULL CHECK (length(trim(justificativa)) > 0),
    assessor_id INTEGER NOT NULL REFERENCES assessor(id),
    avaliada_em TEXT NOT NULL
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
    ocorrida_em TEXT NOT NULL,
    registrada_em TEXT NOT NULL,
    proximos_passos TEXT,
    assessor_id INTEGER NOT NULL REFERENCES assessor(id)
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
CREATE TABLE IF NOT EXISTS tratamento_alerta (
    chave_ocorrencia TEXT PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    tratado_em TEXT NOT NULL,
    assessor_id INTEGER NOT NULL REFERENCES assessor(id)
);
CREATE TABLE IF NOT EXISTS documento_fonte (
    id INTEGER PRIMARY KEY,
    origem TEXT NOT NULL,
    registro_id TEXT NOT NULL,
    versao INTEGER NOT NULL CHECK (versao > 0),
    cliente_referencia INTEGER,
    cliente_id INTEGER REFERENCES cliente(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('interacao', 'formulario')),
    canal TEXT CHECK (canal IN ('whatsapp', 'email', 'telefone', 'presencial')),
    conteudo TEXT NOT NULL,
    ocorrida_em TEXT NOT NULL,
    importada_em TEXT NOT NULL,
    interacao_id INTEGER REFERENCES interacao(id),
    UNIQUE (origem, registro_id, versao)
);
CREATE INDEX IF NOT EXISTS documento_fonte_cliente ON documento_fonte(cliente_id);
CREATE TABLE IF NOT EXISTS processamento_contexto (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    modelo TEXT NOT NULL, prompt_versao TEXT NOT NULL, assinatura TEXT NOT NULL,
    documentos TEXT NOT NULL, estado TEXT NOT NULL, inicio_em TEXT NOT NULL, fim_em TEXT,
    UNIQUE (cliente_id, modelo, prompt_versao, assinatura)
);
CREATE TABLE IF NOT EXISTS item_contexto (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    processamento_id INTEGER NOT NULL REFERENCES processamento_contexto(id),
    categoria TEXT NOT NULL, assunto TEXT NOT NULL, sujeito TEXT NOT NULL, tipo TEXT NOT NULL,
    valor_original TEXT NOT NULL, evidencias TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendente', valor_revisado TEXT,
    revisao INTEGER NOT NULL DEFAULT 0, adiado_ate TEXT, gerado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revisao_contexto (
    id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL REFERENCES item_contexto(id),
    acao TEXT NOT NULL, motivo TEXT NOT NULL, valor TEXT, adiado_ate TEXT,
    assessor_id INTEGER NOT NULL REFERENCES assessor(id), revisao INTEGER NOT NULL, revisada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preferencia_assunto (
    cliente_id INTEGER NOT NULL REFERENCES cliente(id), assunto TEXT NOT NULL,
    bloqueado INTEGER NOT NULL CHECK (bloqueado IN (0,1)), PRIMARY KEY (cliente_id, assunto)
);
CREATE TABLE IF NOT EXISTS historico_assunto (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id), assunto TEXT NOT NULL,
    bloqueado INTEGER NOT NULL, motivo TEXT NOT NULL, assessor_id INTEGER NOT NULL REFERENCES assessor(id),
    registrada_em TEXT NOT NULL
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


def drop_all() -> None:
    db = get_db()
    for tabela in TABELAS:
        db.execute(f"DROP TABLE IF EXISTS {tabela}")
    db.commit()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        click.echo("Banco inicializado.")
