from datetime import date

import pytest

from app.rules import (
    aniversario_gera_alerta,
    prioridade_cliente,
    prioridade_vencimento,
    proxima_ocorrencia_aniversario,
)

HOJE = date(2026, 10, 10)


@pytest.mark.parametrize(
    "dias,esperado",
    [(-1, "alta"), (0, "alta"), (7, "alta"), (8, "media"), (30, "media"), (31, None)],
)
def test_prioridade_vencimento_limites(dias, esperado):
    from datetime import timedelta

    assert prioridade_vencimento(HOJE + timedelta(days=dias), HOJE) == esperado


def test_prioridade_cliente_maior_alerta_e_baixa_sem_alertas():
    assert prioridade_cliente([]) == "baixa"
    assert prioridade_cliente(["media", "alta", "media"]) == "alta"


def test_aniversario_janela_de_7_dias():
    assert aniversario_gera_alerta(17, 10, HOJE) == date(2026, 10, 17)
    assert aniversario_gera_alerta(18, 10, HOJE) is None
    assert aniversario_gera_alerta(10, 10, HOJE) == HOJE


def test_aniversario_virada_de_ano_e_29_de_fevereiro():
    assert proxima_ocorrencia_aniversario(2, 1, date(2026, 12, 30)) == date(2027, 1, 2)
    assert proxima_ocorrencia_aniversario(29, 2, date(2026, 12, 30)) == date(2027, 2, 28)
