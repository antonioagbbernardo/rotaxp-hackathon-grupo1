"""Alertas calculados sob demanda (RN14/RN15). Só o tratamento é persistido.

Identidade: (cliente_id, regra, entidade_origem_id, ocorrencia). Chaves:
  venc:{posicao_id}:{data_vencimento}   aniv:{data_importante_id}:{data_da_ocorrencia}
"""
from datetime import date

from .rules import (
    aniversario_gera_alerta,
    classificar_vencimento,
    contato_pessoal_permitido,
    prioridade_cliente,
)

ROTULO_PRIORIDADE = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}


def calcular_alertas(
    posicoes: list[dict],
    datas_importantes: list[dict],
    tratadas: set[str],
    hoje: date,
    permite_assuntos_pessoais: bool,
    intervalo_minimo_dias: int,
    ultimo_contato: date | None,
) -> list[dict]:
    """Função pura: devolve todos os alertas elegíveis, pendentes e tratados."""
    alertas: list[dict] = []
    for p in posicoes:
        vencimento = date.fromisoformat(p["vencimento"])
        c = classificar_vencimento(vencimento, hoje)
        if c is None:
            continue
        chave = f"venc:{p['id']}:{p['vencimento']}"
        alertas.append(
            {
                "cliente_id": p["cliente_id"],
                "regra": "vencimento",
                "entidade_origem_id": p["id"],
                "ocorrencia": p["vencimento"],
                "chave_ocorrencia": chave,
                "classificacao": c["classificacao"],
                "rotulo": c["rotulo"],
                "prioridade": c["prioridade"],
                "motivo": f"{p['ativo']}: {c['rotulo'].lower()} ({p['vencimento']})",
                "fonte": {"tipo_fonte": "posicao", "id_fonte": p["id"], "data_referencia": p["vencimento"],
                          "descricao": p["fonte"]},
                "estado": "tratado" if chave in tratadas else "pendente",
            }
        )
    if contato_pessoal_permitido(permite_assuntos_pessoais, intervalo_minimo_dias, ultimo_contato, hoje):
        for d in datas_importantes:
            ocorrencia = aniversario_gera_alerta(d["dia"], d["mes"], hoje)
            if ocorrencia is None:
                continue
            chave = f"aniv:{d['id']}:{ocorrencia.isoformat()}"
            quem = "do cliente" if d["vinculo"] == "cliente" else f"({d['descricao']})"
            alertas.append(
                {
                    "cliente_id": d["cliente_id"],
                    "regra": "aniversario",
                    "entidade_origem_id": d["id"],
                    "ocorrencia": ocorrencia.isoformat(),
                    "chave_ocorrencia": chave,
                    "classificacao": "aniversario",
                    "rotulo": "Aniversário hoje" if ocorrencia == hoje else f"Aniversário em {(ocorrencia - hoje).days} dia(s)",
                    "prioridade": "media",
                    "motivo": f"Aniversário {quem} em {ocorrencia.isoformat()}",
                    "fonte": {"tipo_fonte": "data_importante", "id_fonte": d["id"],
                              "data_referencia": ocorrencia.isoformat(), "descricao": d["fonte"]},
                    "estado": "tratado" if chave in tratadas else "pendente",
                }
            )
    return sorted(alertas, key=lambda a: (a["ocorrencia"], a["regra"], a["entidade_origem_id"]))


def prioridade_do_cliente(alertas: list[dict]) -> str:
    return prioridade_cliente([a["prioridade"] for a in alertas if a["estado"] == "pendente"])


def proxima_pendencia(alertas: list[dict]) -> str | None:
    datas = [a["ocorrencia"] for a in alertas if a["estado"] == "pendente"]
    return min(datas) if datas else None
