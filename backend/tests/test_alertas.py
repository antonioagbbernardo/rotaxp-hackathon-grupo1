from datetime import date, timedelta

from app.alertas import calcular_alertas, prioridade_do_cliente, proxima_pendencia

HOJE = date(2026, 10, 10)


def pos(i, delta):
    return {"id": i, "cliente_id": 1, "ativo": f"Ativo {i}", "valor": "1.00",
            "vencimento": (HOJE + timedelta(days=delta)).isoformat(), "fonte": "teste"}


def aniv(i, delta, vinculo="familiar"):
    d = HOJE + timedelta(days=delta)
    return {"id": i, "cliente_id": 1, "tipo": "aniversario", "vinculo": vinculo, "descricao": "filha",
            "dia": d.day, "mes": d.month, "fonte": "Registro manual do assessor"}


def calc(posicoes=(), datas=(), tratadas=(), permite=True, intervalo=7, ultimo=None):
    return calcular_alertas(list(posicoes), list(datas), set(tratadas), HOJE, permite, intervalo, ultimo)


def test_ca05_limites_de_vencimento_existencia_rotulo_e_prioridade():
    deltas = [-1, 0, 7, 8, 30, 31]
    alertas = calc([pos(i, d) for i, d in enumerate(deltas, 1)])
    por_delta = {a["entidade_origem_id"]: a for a in alertas}
    assert 6 not in por_delta  # Δ = 31 fica fora
    assert (por_delta[1]["rotulo"], por_delta[1]["prioridade"]) == ("Vencido há 1 dia", "alta")
    assert (por_delta[2]["rotulo"], por_delta[2]["prioridade"]) == ("Vence hoje", "alta")
    assert (por_delta[3]["rotulo"], por_delta[3]["prioridade"]) == ("Vence em 7 dias", "alta")
    assert (por_delta[4]["rotulo"], por_delta[4]["prioridade"]) == ("Vence em 8 dias", "media")
    assert (por_delta[5]["rotulo"], por_delta[5]["prioridade"]) == ("Vence em 30 dias", "media")


def test_ca39_calculo_e_idempotente_sem_duplicar():
    p = [pos(1, 5), pos(2, 20)]
    assert calc(p) == calc(p)
    assert len(calc(p)) == 2


def test_ca08_tratado_permanece_tratado_e_nao_conta_para_prioridade():
    a = calc([pos(1, 5)])[0]
    tratadas = {a["chave_ocorrencia"]}
    novos = calc([pos(1, 5)], tratadas=tratadas)
    assert novos[0]["estado"] == "tratado"
    assert prioridade_do_cliente(novos) == "baixa"
    assert proxima_pendencia(novos) is None


def test_rn14_mesmo_alerta_muda_prioridade_sem_mudar_identidade_ao_aproximar():
    longe = calcular_alertas([pos(1, 20)], [], set(), HOJE, True, 7, None)[0]
    perto = calcular_alertas([pos(1, 20)], [], set(), HOJE + timedelta(days=15), True, 7, None)[0]
    assert longe["chave_ocorrencia"] == perto["chave_ocorrencia"]
    assert (longe["prioridade"], perto["prioridade"]) == ("media", "alta")


def test_rn14_vencimento_corrigido_gera_nova_ocorrencia_e_perde_tratamento():
    antigo = calc([pos(1, 5)])[0]
    corrigido = calc([pos(1, 6)], tratadas={antigo["chave_ocorrencia"]})[0]
    assert corrigido["chave_ocorrencia"] != antigo["chave_ocorrencia"]
    assert corrigido["estado"] == "pendente"


def test_ca34_prioridade_do_cliente_e_a_maior_pendente():
    alertas = calc([pos(1, 20), pos(2, 3)])
    assert prioridade_do_cliente(alertas) == "alta"
    tratadas = {a["chave_ocorrencia"] for a in alertas if a["prioridade"] == "alta"}
    assert prioridade_do_cliente(calc([pos(1, 20), pos(2, 3)], tratadas=tratadas)) == "media"


def test_ca35_aniversario_gera_um_alerta_media_com_permissao():
    alertas = calc(datas=[aniv(1, 3)])
    assert len(alertas) == 1
    assert (alertas[0]["regra"], alertas[0]["prioridade"]) == ("aniversario", "media")


def test_ca07_aniversario_sem_permissao_nao_gera_mas_vencimento_permanece():
    alertas = calc([pos(1, 2)], [aniv(1, 3)], permite=False)
    assert [a["regra"] for a in alertas] == ["vencimento"]


def test_ca07_aniversario_bloqueado_por_intervalo_mas_nao_sem_historico():
    assert calc(datas=[aniv(1, 3)], intervalo=14, ultimo=HOJE - timedelta(days=5)) == []
    assert len(calc(datas=[aniv(1, 3)], intervalo=14, ultimo=None)) == 1


def test_ca35_aniversario_tratado_nao_reaparece_nem_no_proximo_dia_da_mesma_ocorrencia():
    a = calc(datas=[aniv(1, 3)])[0]
    novos = calcular_alertas([], [aniv(1, 3)], {a["chave_ocorrencia"]}, HOJE + timedelta(days=1), True, 7, None)
    assert novos[0]["estado"] == "tratado"
