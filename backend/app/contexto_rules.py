"""Validação pura de propostas e decisões humanas (RN24–RN32)."""
import re
from datetime import date

CATEGORIAS = ("objetivo", "interesse", "preferencia", "data_importante", "compromisso", "ponto_atencao")
SUJEITOS = ("cliente", "familiar", "terceiro", "incerto")
PROMPT_VERSAO = "contexto-v1"


class ErroContexto(Exception):
    def __init__(self, mensagem, campo="contexto", status=400, codigo=None):
        self.mensagem, self.campo, self.status = mensagem, campo, status
        self.codigo = codigo or ("saida_ia_invalida" if status == 502 else "contexto_invalido")


def texto(valor, campo, limite=500, status=400):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite:
        raise ErroContexto(f"Texto obrigatório, com até {limite} caracteres.", campo, status)
    return valor.strip()


def validar_saida(resposta, documentos):
    def erro(campo):
        raise ErroContexto("Proposta da IA inválida ou sem evidência literal na fonte.", campo, 502)
    if not isinstance(resposta, dict) or set(resposta) != {"itens"}:
        erro("itens")
    itens = resposta["itens"]
    if not isinstance(itens, list) or len(itens) > 30:
        erro("itens")
    fontes = {d["id"]: d for d in documentos}
    for n, item in enumerate(itens):
        p = f"itens[{n}]"
        if not isinstance(item, dict) or set(item) != {"categoria", "assunto", "sujeito", "tipo", "valor", "evidencias"}:
            erro(p)
        for campo, opcoes in (("categoria", CATEGORIAS), ("sujeito", SUJEITOS), ("tipo", ("fato", "hipotese"))):
            if item[campo] not in opcoes:
                erro(p + "." + campo)
        if not isinstance(item["assunto"], str) or not re.fullmatch(r"[a-z0-9-]{1,80}", item["assunto"]):
            erro(p + ".assunto")
        texto(item["valor"], p + ".valor", status=502)
        evidencias = item["evidencias"]
        if not isinstance(evidencias, list) or not 1 <= len(evidencias) <= 5:
            erro(p + ".evidencias")
        for e in evidencias:
            if not isinstance(e, dict) or set(e) != {"documento_id", "trecho", "campo"}:
                erro(p + ".evidencias")
            if type(e["documento_id"]) is not int or e["documento_id"] not in fontes:
                erro(p + ".evidencias.documento_id")
            d = fontes[e["documento_id"]]
            if not isinstance(e["trecho"], str) or not e["trecho"].strip():
                erro(p + ".evidencias.trecho")
            if d["tipo"] == "formulario":
                if not isinstance(e["campo"], str) or e["campo"] not in d["conteudo"]:
                    erro(p + ".evidencias.campo")
                original = d["conteudo"][e["campo"]]
            else:
                if e["campo"] is not None:
                    erro(p + ".evidencias.campo")
                original = d["conteudo"]
            if e["trecho"] not in original:
                erro(p + ".evidencias.trecho")
    return itens


def validar_revisao(corpo, hoje):
    if not isinstance(corpo, dict):
        raise ErroContexto("Envie um objeto JSON.")
    acao = corpo.get("acao")
    if acao not in ("aprovar", "corrigir", "descartar", "adiar"):
        raise ErroContexto("Ação de revisão inválida.", "acao")
    esperados = {"acao", "motivo", "revisao"}
    if acao == "corrigir":
        esperados.add("valor")
    if acao == "adiar":
        esperados.add("adiado_ate")
    if set(corpo) != esperados:
        raise ErroContexto("Campos incompatíveis com a ação de revisão.", "acao")
    texto(corpo["motivo"], "motivo", 1000)
    if type(corpo["revisao"]) is not int or corpo["revisao"] < 0:
        raise ErroContexto("Revisão deve ser um inteiro não negativo.", "revisao")
    if acao == "corrigir":
        texto(corpo["valor"], "valor")
    if acao == "adiar":
        try:
            valor = corpo["adiado_ate"]
            if not isinstance(valor, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor) or date.fromisoformat(valor) <= hoje:
                raise ValueError()
        except (ValueError, TypeError):
            raise ErroContexto("Adiamento exige uma data futura em YYYY-MM-DD.", "adiado_ate") from None
    return corpo


SCHEMA_SAIDA = {
    "type": "object", "additionalProperties": False, "required": ["itens"],
    "properties": {"itens": {"type": "array", "description": "De zero a 30 propostas.", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["categoria", "assunto", "sujeito", "tipo", "valor", "evidencias"],
        "properties": {
            "categoria": {"type": "string", "enum": list(CATEGORIAS)},
            "assunto": {"type": "string", "description": "Slug estável minúsculo de 1 a 80 caracteres a-z, 0-9 ou hífen."},
            "sujeito": {"type": "string", "enum": list(SUJEITOS)},
            "tipo": {"type": "string", "enum": ["fato", "hipotese"]},
            "valor": {"type": "string", "description": "Texto não vazio de até 500 caracteres."},
            "evidencias": {"type": "array", "description": "De uma a cinco evidências literais.", "items": {
                "type": "object", "additionalProperties": False,
                "required": ["documento_id", "trecho", "campo"], "properties": {
                    "documento_id": {"type": "integer"}, "trecho": {"type": "string"},
                    "campo": {"type": ["string", "null"]}}}}}}}}
}
