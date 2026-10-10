"""Regras puras (sem I/O). Referência: docs/spec.md RN03, RN04, RN11, RN12."""
from datetime import date

ORDEM = {"alta": 0, "media": 1, "baixa": 2}


def prioridade_vencimento(vencimento: date, hoje: date) -> str | None:
    """RN03/RN04. Vencido ou 0–7 dias: alta; 8–30: média; 31+: sem alerta."""
    dias = (vencimento - hoje).days
    if dias <= 7:
        return "alta"
    if dias <= 30:
        return "media"
    return None


def prioridade_cliente(prioridades_pendentes: list[str]) -> str:
    """RN11. Maior prioridade entre alertas pendentes; sem alertas, baixa."""
    return min(prioridades_pendentes, key=ORDEM.__getitem__, default="baixa")


def proxima_ocorrencia_aniversario(dia: int, mes: int, hoje: date) -> date:
    """Próxima data (hoje inclusive) em que dia/mês ocorre. 29/02 cai em 28/02 fora de bissexto."""
    for ano in (hoje.year, hoje.year + 1):
        try:
            candidata = date(ano, mes, dia)
        except ValueError:
            candidata = date(ano, mes, 28)
        if candidata >= hoje:
            return candidata
    raise AssertionError("inalcançável")


def aniversario_gera_alerta(dia: int, mes: int, hoje: date) -> date | None:
    """RN12. Devolve a data da ocorrência se faltam 0–7 dias; senão None."""
    ocorrencia = proxima_ocorrencia_aniversario(dia, mes, hoje)
    return ocorrencia if (ocorrencia - hoje).days <= 7 else None
