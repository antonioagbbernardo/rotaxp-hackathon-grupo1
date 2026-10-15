import sqlite3

import click
from flask import Flask, current_app, g

# Dinheiro: TEXT com Decimal (nunca float). Datas: YYYY-MM-DD. Instantes: UTC ISO 8601.
# O alerta NÃO é persistido (calculado sob demanda); só o tratamento (tratamento_alerta).
TABELAS = ("humor_historico", "humor_inferido", "nota_assessor", "chat_turno", "feedback_lembranca", "lembranca_contexto", "pauta_reuniao", "reuniao", "google_agenda_token", "sessao_acesso", "descarte_noticia", "coleta_artigo_noticia", "artigo_noticia", "coleta_noticia", "vinculo_noticia",
           "resumo_ia", "historico_assunto", "preferencia_assunto", "revisao_contexto", "item_contexto", "processamento_contexto",
           "documento_fonte", "tratamento_alerta", "avaliacao_relacionamento", "interacao", "data_importante",
           "posicao", "cliente", "assessor")

SCHEMA = """
CREATE TABLE IF NOT EXISTS humor_historico (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    assinatura TEXT NOT NULL, dados TEXT NOT NULL, ocorrida_em TEXT NOT NULL,
    gerado_em TEXT NOT NULL, UNIQUE(cliente_id,assinatura)
);
CREATE TABLE IF NOT EXISTS humor_inferido (
    cliente_id INTEGER PRIMARY KEY REFERENCES cliente(id), assinatura TEXT NOT NULL,
    estado TEXT NOT NULL, iniciada_em TEXT NOT NULL, dados TEXT,
    revisado_em TEXT, erro TEXT
);
CREATE TABLE IF NOT EXISTS chat_turno (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    request_id TEXT NOT NULL, pergunta TEXT NOT NULL, criada_em TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'processando' CHECK(estado IN ('processando','concluido','falhou')),
    resposta TEXT, fontes TEXT NOT NULL DEFAULT '[]', nota_sugerida TEXT,
    contexto_sugerido TEXT NOT NULL DEFAULT '[]',
    UNIQUE(cliente_id,request_id)
);
CREATE TABLE IF NOT EXISTS nota_assessor (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    turno_id INTEGER NOT NULL UNIQUE REFERENCES chat_turno(id), texto TEXT NOT NULL,
    evidencia TEXT NOT NULL, registrada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lembranca_contexto (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    item_id INTEGER NOT NULL REFERENCES item_contexto(id), revisao INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('aniversario','compromisso')), descricao TEXT NOT NULL,
    data TEXT, dia INTEGER, mes INTEGER, assessor_id INTEGER NOT NULL REFERENCES assessor(id),
    confirmada_em TEXT NOT NULL, versao INTEGER NOT NULL DEFAULT 1, UNIQUE(cliente_id,item_id)
);
CREATE TABLE IF NOT EXISTS feedback_lembranca (
    id INTEGER PRIMARY KEY, lembranca_id INTEGER NOT NULL REFERENCES lembranca_contexto(id),
    revisao INTEGER NOT NULL, versao INTEGER NOT NULL, ocorrencia TEXT NOT NULL,
    acao TEXT NOT NULL CHECK(acao IN ('concluir','descartar','adiar')), motivo TEXT NOT NULL,
    adiado_ate TEXT NOT NULL DEFAULT '', assessor_id INTEGER NOT NULL REFERENCES assessor(id), registrada_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reuniao (
    id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    assessor_id INTEGER NOT NULL REFERENCES assessor(id), objetivo TEXT NOT NULL,
    inicio_em TEXT NOT NULL, criada_em TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'agendada' CHECK(estado IN ('agendada','cancelada','concluida')),
    notas TEXT NOT NULL DEFAULT '', pauta_revisada_id INTEGER, avisos_busca TEXT NOT NULL DEFAULT '[]',
    interacao_id INTEGER UNIQUE REFERENCES interacao(id), google_event_id TEXT,
    google_sync_status TEXT NOT NULL DEFAULT 'nao_conectado', google_sync_error TEXT,
    google_event_url TEXT
);
CREATE INDEX IF NOT EXISTS reuniao_cliente_inicio ON reuniao(cliente_id,inicio_em);
CREATE TABLE IF NOT EXISTS google_agenda_token (
    id INTEGER PRIMARY KEY CHECK(id=1), email TEXT NOT NULL, access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL, expira_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pauta_reuniao (
    id INTEGER PRIMARY KEY, reuniao_id INTEGER NOT NULL REFERENCES reuniao(id),
    assinatura TEXT NOT NULL, dados TEXT NOT NULL, gerada_em TEXT NOT NULL,
    UNIQUE(reuniao_id,assinatura)
);
CREATE TABLE IF NOT EXISTS sessao_acesso (
    token_hash TEXT PRIMARY KEY, expira_em INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS usuario_acesso (
    usuario TEXT PRIMARY KEY, senha_hash TEXT NOT NULL, banco TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS tentativa_login (
    chave TEXT PRIMARY KEY, tentativas INTEGER NOT NULL, expira_em INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS migracao_aplicada (chave TEXT PRIMARY KEY);
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
    nome TEXT NOT NULL,
    cargo TEXT NOT NULL DEFAULT 'Assessor de investimentos',
    email TEXT NOT NULL DEFAULT '',
    telefone TEXT NOT NULL DEFAULT '',
    escritorio TEXT NOT NULL DEFAULT ''
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
    tipo TEXT NOT NULL CHECK (tipo IN ('interacao', 'formulario', 'nota_assessor')),
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
        g.db = sqlite3.connect(g.get('tenant_database', current_app.config["DATABASE"]))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()
    auth = g.pop('auth_db', None)
    if auth is not None:
        auth.close()


def init_db() -> None:
    db = get_db()
    db.executescript(SCHEMA)
    for sql in (
        'CREATE INDEX IF NOT EXISTS interacao_cliente_data ON interacao(cliente_id,ocorrida_em DESC,id DESC)',
        'CREATE INDEX IF NOT EXISTS posicao_cliente ON posicao(cliente_id)',
        'CREATE INDEX IF NOT EXISTS contexto_cliente_assunto ON item_contexto(cliente_id,assunto,sujeito)',
        'CREATE INDEX IF NOT EXISTS revisao_item ON revisao_contexto(item_id,revisao)',
    ):
        db.execute(sql)
    if 'usuario' not in {r['name'] for r in db.execute('PRAGMA table_info(sessao_acesso)')}:
        db.execute('ALTER TABLE sessao_acesso ADD COLUMN usuario TEXT')
        db.execute("UPDATE sessao_acesso SET usuario='__demo__' WHERE usuario IS NULL")
    if 'artigos_rejeitados' not in {r['name'] for r in db.execute('PRAGMA table_info(coleta_noticia)')}:
        db.execute('ALTER TABLE coleta_noticia ADD COLUMN artigos_rejeitados INTEGER NOT NULL DEFAULT 0')
    if 'validada' not in {r['name'] for r in db.execute('PRAGMA table_info(nota_assessor)')}:
        db.execute('ALTER TABLE nota_assessor ADD COLUMN validada INTEGER NOT NULL DEFAULT 0')
    colunas = {linha["name"] for linha in db.execute("PRAGMA table_info(reuniao)")}
    for nome, definicao in (
        ("google_event_id", "TEXT"),
        ("google_sync_status", "TEXT NOT NULL DEFAULT 'nao_conectado'"),
        ("google_sync_error", "TEXT"),
        ("google_event_url", "TEXT"),
    ):
        if nome not in colunas:
            db.execute(f"ALTER TABLE reuniao ADD COLUMN {nome} {definicao}")
    colunas_assessor = {r['name'] for r in db.execute('PRAGMA table_info(assessor)')}
    for campo, padrao in (('cargo', 'Assessor de investimentos'), ('email', ''), ('telefone', ''), ('escritorio', '')):
        if campo not in colunas_assessor:
            db.execute(f"ALTER TABLE assessor ADD COLUMN {campo} TEXT NOT NULL DEFAULT '{padrao}'")
    db.commit()
    if 'contexto_sugerido' not in {r['name'] for r in db.execute('PRAGMA table_info(chat_turno)')}:
        db.execute("ALTER TABLE chat_turno ADD COLUMN contexto_sugerido TEXT NOT NULL DEFAULT '[]'")
        db.commit()
    antigo = db.execute("SELECT sql FROM sqlite_master WHERE name='documento_fonte'").fetchone()['sql']
    if 'nota_assessor' not in antigo:
        # Amplia apenas o CHECK de tipo, preservando IDs, versões e referências.
        inicio = SCHEMA.index('CREATE TABLE IF NOT EXISTS documento_fonte (')
        tabela = SCHEMA[inicio:SCHEMA.index(';', inicio)]
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute(tabela.replace('documento_fonte (', 'documento_fonte_novo (', 1))
            db.execute('INSERT INTO documento_fonte_novo SELECT * FROM documento_fonte')
            db.execute('DROP TABLE documento_fonte')
            db.execute('ALTER TABLE documento_fonte_novo RENAME TO documento_fonte')
            db.execute('CREATE INDEX documento_fonte_cliente ON documento_fonte(cliente_id)')
            db.commit()
        except Exception:
            db.rollback()
            raise
    from .contexto_chat import revalidar_legado
    revalidar_legado(db)


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
