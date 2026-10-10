from flask import Blueprint, jsonify

from .db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")


def erro(codigo: str, mensagem: str, status: int, campo: str | None = None):
    return jsonify({"erro": {"codigo": codigo, "campo": campo, "mensagem": mensagem}}), status


def _alertas_pendentes(db, cliente_id: int | None = None):
    sql = "SELECT * FROM alerta WHERE estado = 'pendente'"
    args: tuple = ()
    if cliente_id is not None:
        sql += " AND cliente_id = ?"
        args = (cliente_id,)
    return db.execute(sql, args).fetchall()


@bp.get("/clientes")
def listar_clientes():
    # TODO T02: busca (q), filtro de prioridade e ordenação RN11 (pendência mais próxima, nome).
    from .rules import prioridade_cliente

    db = get_db()
    pendentes: dict[int, list[str]] = {}
    for a in _alertas_pendentes(db):
        pendentes.setdefault(a["cliente_id"], []).append(a["prioridade"])
    itens = [
        {
            "id": c["id"],
            "nome": c["nome"],
            "estado_relacionamento": c["estado_relacionamento"],
            "prioridade": prioridade_cliente(pendentes.get(c["id"], [])),
            "alertas_pendentes": len(pendentes.get(c["id"], [])),
        }
        for c in db.execute("SELECT * FROM cliente ORDER BY nome").fetchall()
    ]
    return jsonify({"clientes": itens})


@bp.get("/clientes/<int:cliente_id>")
def detalhe_cliente(cliente_id: int):
    # TODO T02: resumo factual com fontes (RN08), prioridade e histórico (RN02).
    db = get_db()
    c = db.execute("SELECT * FROM cliente WHERE id = ?", (cliente_id,)).fetchone()
    if c is None:
        return erro("nao_encontrado", "Cliente inexistente.", 404)
    por_cliente = lambda t, ordem: [  # noqa: E731
        dict(r) for r in db.execute(f"SELECT * FROM {t} WHERE cliente_id = ? ORDER BY {ordem}", (cliente_id,))
    ]
    return jsonify(
        {
            "cliente": dict(c) | {"permite_assuntos_pessoais": bool(c["permite_assuntos_pessoais"])},
            "posicoes": por_cliente("posicao", "vencimento"),
            "interacoes": por_cliente("interacao", "data_hora DESC, id DESC"),
            "datas_importantes": por_cliente("data_importante", "mes, dia"),
            "alertas": por_cliente("alerta", "estado, data_referencia"),
        }
    )


def _nao_implementado(tarefa: str):
    return erro("nao_implementado", f"Rota pendente ({tarefa}).", 501)


@bp.post("/clientes/<int:cliente_id>/interacoes")
def registrar_interacao(cliente_id: int):
    return _nao_implementado("T03")


@bp.post("/clientes/<int:cliente_id>/relacionamento")
def alterar_relacionamento(cliente_id: int):
    return _nao_implementado("T05")


@bp.post("/alertas/<int:alerta_id>/tratar")
def tratar_alerta(alerta_id: int):
    return _nao_implementado("T04")
