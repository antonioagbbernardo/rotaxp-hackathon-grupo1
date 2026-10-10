from datetime import date, timedelta

import pytest

from app.rules import (
    aniversario_gera_alerta,
    classificar_vencimento,
    contato_pessoal_permitido,
    prioridade_cliente,
    proxima_ocorrencia_aniversario,
)

HOJE = date(2026, 10, 10)


@pytest.mark.parametrize(
    "delta,classificacao,prioridade,rotulo",
    [
        (-1, "vencido", "alta", "Vencido há 1 dia"),
        (-5, "vencido", "alta", "Vencido há 5 dias"),
        (0, "vence_hoje", "alta", "Vence hoje"),
        (1, "vencimento_proximo", "alta", "Vence em 1 dia"),
        (7, "vencimento_proximo", "alta", "Vence em 7 dias"),
        (8, "vencimento_futuro", "media", "Vence em 8 dias"),
        (30, "vencimento_futuro", "media", "Vence em 30 dias"),
    ],
)
def test_classificar_vencimento(delta, classificacao, prioridade, rotulo):
    r = classificar_vencimento(HOJE + timedelta(days=delta), HOJE)
    assert (r["classificacao"], r["prioridade"], r["rotulo"]) == (classificacao, prioridade, rotulo)


def test_vencimento_fora_da_janela():
    assert classificar_vencimento(HOJE + timedelta(days=31), HOJE) is None


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


def test_contato_pessoal_exige_permissao():
    assert not contato_pessoal_permitido(False, 7, None, HOJE)


def test_contato_pessoal_respeita_intervalo_e_sem_historico_nao_bloqueia():
    assert contato_pessoal_permitido(True, 14, None, HOJE)
    assert not contato_pessoal_permitido(True, 14, HOJE - timedelta(days=13), HOJE)
    assert contato_pessoal_permitido(True, 14, HOJE - timedelta(days=14), HOJE)
