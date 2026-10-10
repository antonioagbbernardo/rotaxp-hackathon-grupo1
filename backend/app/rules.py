"""Regras puras (sem I/O). Referência: docs/planejamento/spec.md RN03, RN04, RN11, RN12, RN13."""
from datetime import date

ORDEM = {"alta": 0, "media": 1, "baixa": 2}
INTERVALOS_VALIDOS = (7, 14, 30)


def _dias(n: int) -> str:
    return f"{n} dia" if n == 1 else f"{n} dias"


def classificar_vencimento(vencimento: date, hoje: date) -> dict | None:
    """RN03/RN04. Δ = vencimento − hoje. Devolve None quando fora da janela (Δ ≥ 31)."""
    delta = (vencimento - hoje).days
    if delta < 0:
        return {"classificacao": "vencido", "prioridade": "alta", "rotulo": f"Vencido há {_dias(-delta)}", "delta": delta}
    if delta == 0:
        return {"classificacao": "vence_hoje", "prioridade": "alta", "rotulo": "Vence hoje", "delta": delta}
    if delta <= 7:
        return {"classificacao": "vencimento_proximo", "prioridade": "alta", "rotulo": f"Vence em {_dias(delta)}", "delta": delta}
    if delta <= 30:
        return {"classificacao": "vencimento_futuro", "prioridade": "media", "rotulo": f"Vence em {_dias(delta)}", "delta": delta}
    return None


def prioridade_cliente(prioridades_pendentes: list[str]) -> str:
    """RN11. Maior prioridade entre alertas pendentes; sem alertas, baixa."""
    return min(prioridades_pendentes, key=ORDEM.__getitem__, default="baixa")


def proxima_ocorrencia_aniversario(dia: int, mes: int, hoje: date) -> date:
    """Próxima data (hoje inclusive) do dia/mês. 29/02 vira 28/02 fora de ano bissexto."""
    for ano in (hoje.year, hoje.year + 1):
        try:
            candidata = date(ano, mes, dia)
        except ValueError:
            candidata = date(ano, mes, 28)
        if candidata >= hoje:
            return candidata
    raise AssertionError("inalcançável")


def aniversario_gera_alerta(dia: int, mes: int, hoje: date) -> date | None:
    """RN12. Data da ocorrência se faltam 0–7 dias; senão None."""
    ocorrencia = proxima_ocorrencia_aniversario(dia, mes, hoje)
    return ocorrencia if (ocorrencia - hoje).days <= 7 else None


def contato_pessoal_permitido(
    permite_assuntos_pessoais: bool, intervalo_minimo_dias: int, ultimo_contato: date | None, hoje: date
) -> bool:
    """RN13. Permissão explícita e intervalo mínimo desde o último contato realizado.
    Sem histórico, o intervalo não bloqueia."""
    if not permite_assuntos_pessoais:
        return False
    if ultimo_contato is None:
        return True
    return (hoje - ultimo_contato).days >= intervalo_minimo_dias
