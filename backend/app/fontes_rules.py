"""Validação pura do contrato de fontes; não lê banco nem relógio global."""
import json
from datetime import datetime

from .clock import formatar_utc, parse_instante

CANAIS = ("whatsapp", "email", "telefone", "presencial")


class ErroFonte(Exception):
    def __init__(self, mensagem: str, campo: str, status: int = 400):
        self.mensagem, self.campo, self.status = mensagem, campo, status
        self.codigo = "conflito_fonte" if status == 409 else "entrada_invalida"


def _texto(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ErroFonte("Informe um texto não vazio.", campo)
    return valor.strip()


def _campos(objeto, permitidos, prefixo=""):
    for campo in objeto:
        if campo not in permitidos:
            raise ErroFonte("Campo desconhecido no contrato de fonte.", prefixo + campo)


def validar_lote(corpo, agora: datetime) -> tuple[str, list[dict]]:
    if not isinstance(corpo, dict):
        raise ErroFonte("O lote deve ser um objeto JSON.", "documentos")
    _campos(corpo, {"origem", "ficticio", "documentos"})
    origem = _texto(corpo.get("origem"), "origem")
    if corpo.get("ficticio") is not True:
        raise ErroFonte("A demo aceita somente fontes marcadas como fictícias.", "ficticio")
    documentos = corpo.get("documentos")
    if not isinstance(documentos, list) or not 1 <= len(documentos) <= 100:
        raise ErroFonte("Envie de 1 a 100 documentos por lote.", "documentos")
    normalizados = []
    for indice, doc in enumerate(documentos):
        p = f"documentos[{indice}]."
        if not isinstance(doc, dict):
            raise ErroFonte("Documento deve ser um objeto JSON.", p.rstrip("."))
        _campos(doc, {"registro_id", "versao", "cliente_id", "tipo", "canal", "ocorrida_em", "conteudo"}, p)
        registro = _texto(doc.get("registro_id"), p + "registro_id")
        versao, cid = doc.get("versao"), doc.get("cliente_id")
        if type(versao) is not int or not 1 <= versao <= 2 ** 63 - 1:
            raise ErroFonte("Versão deve ser um inteiro positivo de até 64 bits com sinal.", p + "versao")
        if cid is not None and (type(cid) is not int or not 1 <= cid <= 2 ** 63 - 1):
            raise ErroFonte("Cliente deve ser um ID inteiro positivo de até 64 bits com sinal ou null.", p + "cliente_id")
        tipo, canal, conteudo = doc.get("tipo"), doc.get("canal"), doc.get("conteudo")
        if tipo not in ("interacao", "formulario"):
            raise ErroFonte("Tipo deve ser interacao ou formulario.", p + "tipo")
        if tipo == "interacao":
            if canal not in CANAIS:
                raise ErroFonte("Canal de interação inválido.", p + "canal")
            _texto(conteudo, p + "conteudo")  # validar sem alterar a evidência original
        else:
            if canal is not None:
                raise ErroFonte("Formulário não deve informar canal.", p + "canal")
            if not isinstance(conteudo, dict) or not conteudo or any(
                not isinstance(k, str) or not k.strip() or not isinstance(v, str)
                for k, v in conteudo.items()
            ):
                raise ErroFonte("Formulário exige um objeto de respostas textuais.", p + "conteudo")
        try:
            ocorrida = parse_instante(doc.get("ocorrida_em"))
        except (ValueError, TypeError, OverflowError):
            raise ErroFonte("Informe ocorrência ISO 8601.", p + "ocorrida_em") from None
        if ocorrida > agora:
            raise ErroFonte("Ocorrência não pode estar no futuro.", p + "ocorrida_em")
        normalizados.append({"registro_id": registro, "versao": versao,
                             "cliente_referencia": cid, "tipo": tipo, "canal": canal,
                             "ocorrida_em": formatar_utc(ocorrida),
                             "conteudo": json.dumps(conteudo, ensure_ascii=False, sort_keys=True)})
    return origem, normalizados
