import unicodedata

from flask import Blueprint, current_app, jsonify, request

from . import alertas as alertas_mod
from . import contexto as contexto_ia
from . import pulse
from .contexto_rules import ErroContexto
from .clock import TZ, formatar_utc, parse_instante
from .db import get_db
from .fontes import consultar_fontes, importar_lote
from .fontes_rules import ErroFonte
from .resumo import ROTULO_ESTADO, montar_resumo
from .rules import INTERVALOS_VALIDOS
from .seed import ASSESSOR_ID

bp = Blueprint("api", __name__, url_prefix="/api")

CANAIS = ("whatsapp", "email", "telefone", "presencial")
ESTADOS = ("positivo", "atencao", "negativo")
PRIORIDADES = ("alta", "media", "baixa")


class ErroApi(Exception):
    def __init__(self, codigo: str, mensagem: str, status: int = 400, campo: str | None = None):
        self.codigo, self.mensagem, self.status, self.campo = codigo, mensagem, status, campo


@bp.errorhandler(ErroApi)
def _erro(e: ErroApi):
    return jsonify({"erro": {"codigo": e.codigo, "campo": e.campo, "mensagem": e.mensagem}}), e.status


@bp.errorhandler(ErroFonte)
@bp.errorhandler(ErroContexto)
def _erro_fonte(e: ErroFonte):
    return _erro(e)


@bp.post("/fontes/importar")
def importar_fontes():
    return jsonify(importar_lote(request.get_json(silent=True)))


@bp.get("/fontes/pendencias")
def pendencias_fontes():
    return jsonify({"pendencias": consultar_fontes(pendentes=True)})


@bp.get("/clientes/<int:cliente_id>/fontes")
def fontes_cliente(cliente_id: int):
    _cliente_ou_404(get_db(), cliente_id)
    return jsonify({"fontes": consultar_fontes(cliente_id)})


@bp.get("/clientes/<int:cliente_id>/contexto")
def consultar_contexto(cliente_id):
    _cliente_ou_404(get_db(), cliente_id)
    return jsonify(contexto_ia.consultar(cliente_id))


@bp.post("/clientes/<int:cliente_id>/contexto/processar")
def processar_contexto(cliente_id):
    _cliente_ou_404(get_db(), cliente_id)
    if request.get_data():
        raise ErroApi("entrada_invalida", "Esta rota não recebe corpo; fontes e modelo vêm do backend.", campo="corpo")
    return jsonify(contexto_ia.processar(cliente_id))


@bp.post("/clientes/<int:cliente_id>/contexto/<int:item_id>/revisar")
def revisar_contexto(cliente_id, item_id):
    _cliente_ou_404(get_db(), cliente_id)
    return jsonify(contexto_ia.revisar(cliente_id, item_id, request.get_json(silent=True)))


@bp.post("/clientes/<int:cliente_id>/assuntos/<assunto>")
def alterar_assunto(cliente_id, assunto):
    _cliente_ou_404(get_db(), cliente_id)
    return jsonify(contexto_ia.alterar_assunto(cliente_id, assunto, request.get_json(silent=True)))


@bp.get("/pulse")
def painel_pulse():
    return jsonify(pulse.consultar_painel())


@bp.post("/pulse/clientes/<int:cliente_id>/perguntar")
def perguntar_pulse(cliente_id):
    c = _cliente_ou_404(get_db(), cliente_id)
    corpo = _corpo()
    if set(corpo) != {"pergunta"}:
        raise ErroApi("entrada_invalida", "Informe apenas pergunta.", campo="pergunta")
    pergunta = _texto_obrigatorio(corpo, "pergunta")
    if len(pergunta) > 500:
        raise ErroApi("entrada_invalida", "Pergunta deve ter até 500 caracteres.", campo="pergunta")
    return jsonify(pulse.responder(pulse.montar_cliente(c), pergunta))


def _clock():
    return current_app.config["CLOCK"]


def _corpo() -> dict:
    corpo = request.get_json(silent=True)
    if not isinstance(corpo, dict):
        raise ErroApi("entrada_invalida", "O corpo deve ser um objeto JSON.")
    return corpo


def _texto_obrigatorio(corpo: dict, campo: str) -> str:
    valor = corpo.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ErroApi("entrada_invalida", f"'{campo}' é obrigatório e não pode ser vazio.", campo=campo)
    return valor.strip()


def _cliente_ou_404(db, cliente_id: int):
    c = db.execute("SELECT * FROM cliente WHERE id = ?", (cliente_id,)).fetchone()
    if c is None:
        raise ErroApi("nao_encontrado", "Cliente inexistente.", 404)
    return c


def _norm(texto: str) -> str:
    sem = unicodedata.normalize("NFD", texto.casefold())
    return "".join(ch for ch in sem if unicodedata.category(ch) != "Mn")


def _local(instante_utc: str):
    from datetime import datetime

    return datetime.fromisoformat(instante_utc).astimezone(TZ).date()


def _contexto(db, c, hoje) -> dict:
    """Tudo que a lista/detalhe precisam, com alertas calculados a cada consulta."""
    cid = c["id"]
    rows = lambda sql, *a: [dict(r) for r in db.execute(sql, a).fetchall()]  # noqa: E731
    posicoes = rows("SELECT * FROM posicao WHERE cliente_id = ? ORDER BY vencimento, id", cid)
    datas = rows("SELECT * FROM data_importante WHERE cliente_id = ? ORDER BY mes, dia, id", cid)
    interacoes = rows(
        "SELECT * FROM interacao WHERE cliente_id = ? ORDER BY ocorrida_em DESC, registrada_em DESC, id DESC", cid)
    avaliacoes = rows(
        "SELECT * FROM avaliacao_relacionamento WHERE cliente_id = ? ORDER BY avaliada_em DESC, id DESC", cid)
    tratadas = {r["chave_ocorrencia"] for r in
                db.execute("SELECT chave_ocorrencia FROM tratamento_alerta WHERE cliente_id = ?", (cid,))}
    ultimo_contato = max((i["ocorrida_em"] for i in interacoes), default=None)
    ultimo_contato_data = _local(ultimo_contato) if ultimo_contato else None
    alertas = alertas_mod.calcular_alertas(
        posicoes, datas, tratadas, hoje,
        bool(c["permite_assuntos_pessoais"]), c["intervalo_minimo_dias"], ultimo_contato_data)
    ultima = interacoes[0] if interacoes else None
    return {
        "posicoes": posicoes, "datas": datas, "interacoes": interacoes, "avaliacoes": avaliacoes,
        "alertas": alertas,
        "prioridade": alertas_mod.prioridade_do_cliente(alertas),
        "proxima_pendencia": alertas_mod.proxima_pendencia(alertas),
        "ultima": ultima,
        "ultima_data": _local(ultima["ocorrida_em"]) if ultima else None,
    }


def _relacionamento(avaliacoes: list[dict]) -> dict | None:
    if not avaliacoes:
        return None
    a = avaliacoes[0]
    return {"estado": a["estado"], "rotulo": ROTULO_ESTADO[a["estado"]], "justificativa": a["justificativa"],
            "assessor_id": a["assessor_id"], "avaliada_em": a["avaliada_em"]}


def _preferencias(c) -> dict:
    return {"canal_preferido": c["canal_preferido"], "intervalo_minimo_dias": c["intervalo_minimo_dias"],
            "permite_assuntos_pessoais": bool(c["permite_assuntos_pessoais"])}


@bp.get("/clientes")
def listar_clientes():
    q = _norm(request.args.get("q", "").strip())
    filtro = request.args.get("prioridade")
    if filtro and filtro not in PRIORIDADES:
        raise ErroApi("entrada_invalida", "prioridade deve ser alta, media ou baixa.", campo="prioridade")
    db, hoje = get_db(), _clock().hoje()
    itens = []
    for c in db.execute("SELECT * FROM cliente").fetchall():
        if q and q not in _norm(c["nome"]):
            continue
        ctx = _contexto(db, c, hoje)
        if filtro and ctx["prioridade"] != filtro:
            continue
        rel = _relacionamento(ctx["avaliacoes"])
        itens.append({
            "id": c["id"], "nome": c["nome"], "perfil": c["perfil"],
            "prioridade": ctx["prioridade"],
            "alertas_pendentes": sum(a["estado"] == "pendente" for a in ctx["alertas"]),
            "proxima_pendencia": ctx["proxima_pendencia"],
            "relacionamento": rel,
        })
    itens.sort(key=lambda i: (PRIORIDADES.index(i["prioridade"]), i["proxima_pendencia"] or "9999-12-31",
                              _norm(i["nome"])))
    return jsonify({"clientes": itens})


@bp.get("/clientes/<int:cliente_id>")
def detalhe_cliente(cliente_id: int):
    db, hoje = get_db(), _clock().hoje()
    c = _cliente_ou_404(db, cliente_id)
    ctx = _contexto(db, c, hoje)
    avaliacao_atual = ctx["avaliacoes"][0] if ctx["avaliacoes"] else None
    resumo = montar_resumo(dict(c), ctx["posicoes"], ctx["ultima"], avaliacao_atual, hoje, ctx["ultima_data"])
    return jsonify({
        "cliente": {"id": c["id"], "nome": c["nome"], "perfil": c["perfil"], "preferencias": _preferencias(c)},
        "prioridade": ctx["prioridade"],
        "relacionamento": _relacionamento(ctx["avaliacoes"]),
        "historico_avaliacoes": ctx["avaliacoes"],
        "resumo": resumo,
        "alertas": ctx["alertas"],
        "posicoes": ctx["posicoes"],
        "interacoes": ctx["interacoes"],
        "datas_importantes": ctx["datas"],
    })


@bp.post("/clientes/<int:cliente_id>/interacoes")
def registrar_interacao(cliente_id: int):
    db = get_db()
    _cliente_ou_404(db, cliente_id)
    corpo = _corpo()
    canal = corpo.get("canal")
    if canal not in CANAIS:
        raise ErroApi("entrada_invalida", f"canal deve ser um de: {', '.join(CANAIS)}.", campo="canal")
    texto = _texto_obrigatorio(corpo, "texto")
    proximos = corpo.get("proximos_passos")
    if proximos is not None and not isinstance(proximos, str):
        raise ErroApi("entrada_invalida", "proximos_passos deve ser texto.", campo="proximos_passos")
    agora = _clock().agora()
    bruto = corpo.get("ocorrida_em")
    if bruto in (None, ""):
        ocorrida = agora
    else:
        try:
            ocorrida = parse_instante(bruto)
        except (TypeError, ValueError):
            raise ErroApi("entrada_invalida", "ocorrida_em deve ser ISO 8601.", campo="ocorrida_em") from None
        if ocorrida > agora:
            raise ErroApi("entrada_invalida", "ocorrida_em não pode estar no futuro.", campo="ocorrida_em")
    cur = db.execute(
        "INSERT INTO interacao (cliente_id, canal, texto, ocorrida_em, registrada_em, proximos_passos, assessor_id)"
        " VALUES (?,?,?,?,?,?,?)",
        (cliente_id, canal, texto, formatar_utc(ocorrida), formatar_utc(agora), (proximos or "").strip() or None,
         ASSESSOR_ID))
    db.commit()
    row = db.execute("SELECT * FROM interacao WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"interacao": dict(row)}), 201


@bp.post("/clientes/<int:cliente_id>/relacionamento")
def avaliar_relacionamento(cliente_id: int):
    db = get_db()
    _cliente_ou_404(db, cliente_id)
    corpo = _corpo()
    estado = corpo.get("estado")
    if estado not in ESTADOS:
        raise ErroApi("entrada_invalida", f"estado deve ser um de: {', '.join(ESTADOS)}.", campo="estado")
    justificativa = _texto_obrigatorio(corpo, "justificativa")
    cur = db.execute(
        "INSERT INTO avaliacao_relacionamento (cliente_id, estado, justificativa, assessor_id, avaliada_em)"
        " VALUES (?,?,?,?,?)",
        (cliente_id, estado, justificativa, ASSESSOR_ID, formatar_utc(_clock().agora())))
    db.commit()
    row = db.execute("SELECT * FROM avaliacao_relacionamento WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"avaliacao": dict(row)}), 201


@bp.patch("/clientes/<int:cliente_id>/preferencias")
def alterar_preferencias(cliente_id: int):
    db = get_db()
    c = _cliente_ou_404(db, cliente_id)
    corpo = _corpo()
    novo = _preferencias(c)
    if "canal_preferido" in corpo:
        v = corpo["canal_preferido"]
        if v is not None and v not in CANAIS:
            raise ErroApi("entrada_invalida", f"canal_preferido deve ser nulo ou um de: {', '.join(CANAIS)}.",
                          campo="canal_preferido")
        novo["canal_preferido"] = v
    if "intervalo_minimo_dias" in corpo:
        v = corpo["intervalo_minimo_dias"]
        if isinstance(v, bool) or v not in INTERVALOS_VALIDOS:
            raise ErroApi("entrada_invalida", "intervalo_minimo_dias deve ser 7, 14 ou 30.",
                          campo="intervalo_minimo_dias")
        novo["intervalo_minimo_dias"] = v
    if "permite_assuntos_pessoais" in corpo:
        v = corpo["permite_assuntos_pessoais"]
        if not isinstance(v, bool):
            raise ErroApi("entrada_invalida", "permite_assuntos_pessoais deve ser booleano.",
                          campo="permite_assuntos_pessoais")
        novo["permite_assuntos_pessoais"] = v
    db.execute(
        "UPDATE cliente SET canal_preferido = ?, intervalo_minimo_dias = ?, permite_assuntos_pessoais = ? WHERE id = ?",
        (novo["canal_preferido"], novo["intervalo_minimo_dias"], int(novo["permite_assuntos_pessoais"]), cliente_id))
    db.commit()
    return jsonify({"preferencias": novo})


@bp.post("/alertas/tratar")
def tratar_alerta():
    db, hoje = get_db(), _clock().hoje()
    corpo = _corpo()
    cliente_id = corpo.get("cliente_id")
    if isinstance(cliente_id, bool) or not isinstance(cliente_id, int):
        raise ErroApi("entrada_invalida", "cliente_id deve ser inteiro.", campo="cliente_id")
    chave = _texto_obrigatorio(corpo, "chave_ocorrencia")
    c = _cliente_ou_404(db, cliente_id)
    alerta = next((a for a in _contexto(db, c, hoje)["alertas"] if a["chave_ocorrencia"] == chave), None)
    if alerta is None:
        raise ErroApi("nao_encontrado", "Alerta inexistente ou não elegível para este cliente.", 404,
                      campo="chave_ocorrencia")
    if alerta["estado"] == "tratado":  # idempotente: não duplica nem reverte
        return jsonify({"alerta": alerta})
    db.execute(
        "INSERT OR IGNORE INTO tratamento_alerta (chave_ocorrencia, cliente_id, tratado_em, assessor_id)"
        " VALUES (?,?,?,?)", (chave, cliente_id, formatar_utc(_clock().agora()), ASSESSOR_ID))
    db.commit()
    return jsonify({"alerta": alerta | {"estado": "tratado"}}), 201
