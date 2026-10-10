"""Resumo factual por template (RN08). Sem IA. Cada fato tem fonte identificável;
ausência de registro vira mensagem de ausência, nunca conclusão sobre o cliente."""
from datetime import date

ROTULO_ESTADO = {"positivo": "Positivo", "atencao": "Atenção", "negativo": "Negativo"}
ROTULO_CANAL = {"whatsapp": "WhatsApp", "email": "E-mail", "telefone": "Telefone", "presencial": "Presencial"}


def fonte(tipo: str, id_fonte, data_referencia: str | None) -> dict:
    return {"tipo_fonte": tipo, "id_fonte": id_fonte, "data_referencia": data_referencia}


def montar_resumo(cliente: dict, posicoes: list[dict], ultima_interacao: dict | None,
                  avaliacao: dict | None, hoje: date, ocorrida_em_local: date | None) -> dict:
    fatos: list[dict] = []
    ausencias: list[str] = []

    if cliente["perfil"]:
        fatos.append({"texto": f"Perfil: {cliente['perfil']}", "fonte": fonte("cliente", cliente["id"], None)})
    else:
        ausencias.append("Perfil não informado")

    if posicoes:
        n = len(posicoes)
        fatos.append({"texto": f"{n} posição cadastrada" if n == 1 else f"{n} posições cadastradas",
                      "fonte": fonte("posicao", [p["id"] for p in posicoes], None)})
        for p in posicoes:
            delta = (date.fromisoformat(p["vencimento"]) - hoje).days
            if delta < 0:
                quando = f"venceu há {-delta} dia(s)"
            elif delta == 0:
                quando = "vence hoje"
            else:
                quando = f"vence em {delta} dia(s)"
            fatos.append({"texto": f"{p['ativo']} {quando}",
                          "fonte": fonte("posicao", p["id"], p["vencimento"])})
    else:
        ausencias.append("Nenhuma posição cadastrada")

    if ultima_interacao and ocorrida_em_local:
        dias = (hoje - ocorrida_em_local).days
        canal = ROTULO_CANAL.get(ultima_interacao["canal"], ultima_interacao["canal"])
        fatos.append({"texto": f"Último contato há {dias} dia(s) ({canal})",
                      "fonte": fonte("interacao", ultima_interacao["id"], ocorrida_em_local.isoformat())})
        if ultima_interacao.get("proximos_passos"):
            fatos.append({"texto": f"Próximos passos: {ultima_interacao['proximos_passos']}",
                          "fonte": fonte("interacao", ultima_interacao["id"], ocorrida_em_local.isoformat())})
    else:
        ausencias.append("Nenhuma interação registrada")

    if avaliacao:
        fatos.append({"texto": f"Relacionamento: {ROTULO_ESTADO[avaliacao['estado']]}",
                      "fonte": fonte("avaliacao_relacionamento", avaliacao["id"], avaliacao["avaliada_em"][:10])})
    else:
        ausencias.append("Não avaliado")

    return {"fatos": fatos, "ausencias": ausencias}
