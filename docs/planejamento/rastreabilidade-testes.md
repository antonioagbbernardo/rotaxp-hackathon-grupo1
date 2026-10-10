# Rastreabilidade: critérios de aceite × testes

Status: levantamento de 10/10/2026 sobre `main` (7456543) e a branch
`test/aceite-congelados` (8dc94e6). Os testes **não citam** IDs `CA` no código;
a ligação abaixo foi feita por leitura do corpo de cada teste.

Verificação: `uv run --locked pytest` em `main` → 47 passaram. Na branch de
aceite → 30 passaram, 1 falhou, 18 com erro (T09 sem implementação).

Legenda de situação: **Coberto** (o teste exercita o critério inteiro),
**Parcial** (falta parte do enunciado), **Sem teste automatizado**,
**Escrito, não passa** (teste existe só na branch e falha por falta de código).

## Base (CA01–CA10, CA34–CA39) — testes em `main`

| CA | Testes (`arquivo::função`) | Situação | Observação |
| --- | --- | --- | --- |
| CA01 | `test_api::test_lista_ordenada_por_prioridade_pendencia_e_nome`, `::test_busca_e_filtro` | Coberto | Inclui filtro inválido → 400 |
| CA02 | `test_api::test_detalhe_somente_dados_do_cliente` | Parcial | Confere `cliente_id` de posições, interações e datas; **não confere preferências** |
| CA03 | `test_api::test_registrar_interacao_persiste_apos_reiniciar_aplicacao` | Coberto | Reinicia a aplicação sobre o mesmo banco |
| CA04 | `test_api::test_interacao_invalida_nao_cria_registro` (5 casos), `::test_interacao_cliente_inexistente_404` | Parcial | Canal, texto, ocorrência futura/ilegível: confere que nada foi gravado. Cliente inexistente: só confere o 404 |
| CA05 | `test_rules::test_classificar_vencimento` (−5, −1, 0, 1, 7, 8, 30), `::test_vencimento_fora_da_janela` (31), `test_alertas::test_limites_de_vencimento_existencia_rotulo_e_prioridade` | Coberto | Existência, rótulo e prioridade nos seis Δ do critério |
| CA06 | — | Sem teste automatizado | Opcional; fica após T06 |
| CA07 | `test_rules::test_contato_pessoal_*`, `test_alertas::test_aniversario_sem_permissao_nao_gera_mas_vencimento_permanece`, `::test_aniversario_bloqueado_por_intervalo_mas_nao_sem_historico`, `test_api::test_preferencias_permissao_pessoal_remove_aniversario` | Coberto | Sem permissão, intervalo, sem histórico e alertas financeiros mantidos |
| CA08 | `test_api::test_tratar_alerta_reduz_pendencias_persiste_e_e_idempotente`, `test_alertas::test_tratado_permanece_tratado_e_nao_conta_para_prioridade` | Coberto | Contagem, persistência após reinício, idempotência e recálculo |
| CA09 | `test_api::test_relacionamento_exige_justificativa_e_nao_altera_prioridade` | Parcial | Cobre a justificativa. **Sentido oposto do enunciado não testado**: alerta financeiro não alterar o relacionamento (o teste verifica relacionamento → prioridade) |
| CA10 | `test_api::test_pagina_base` | Sem teste automatizado | Só GET `/` → 200. Celular sem rolagem horizontal exige navegador; **não verificado** |
| CA34 | `test_alertas::test_prioridade_do_cliente_e_a_maior_pendente`, `test_api::test_prioridade_recalculada_apos_tratar` | Coberto | |
| CA35 | `test_alertas::test_aniversario_gera_um_alerta_media_com_permissao`, `::test_aniversario_tratado_nao_reaparece_nem_no_proximo_dia_da_mesma_ocorrencia`, `test_rules::test_aniversario_virada_de_ano_e_29_de_fevereiro` | Parcial | Um alerta, RN13 e tratado sem reaparecer: cobertos. **"No ano seguinte é nova ocorrência" não tem teste direto** (só a virada de ano da regra) |
| CA36 | `test_api::test_historico_ordenado_por_ocorrencia_nao_por_registro` | Parcial | Prova ordenação por `ocorrida_em`, com canais telefone/presencial. Não usa o cenário "reunião ontem cadastrada hoje" literalmente |
| CA37 | `test_api::test_resumo_com_fontes_e_ausencias` | Coberto | Mensagens de ausência (Eva) e fonte em todo fato (Ana) |
| CA38 | `test_api::test_resultado_independe_do_dia_real`, `::test_seed_nao_sobrescreve_base_populada` | Coberto | Outro dia injetado no `Clock`; seed não sobrescreve |
| CA39 | `test_api::test_atualizar_varias_vezes_nao_duplica_alertas`, `test_alertas::test_calculo_e_idempotente_sem_duplicar` | Coberto | |

## T09 (CA26–CA33) — testes só em `test/aceite-congelados`

Todos dependem de `cliente.ref_externa`, `POST /api/fontes/sincronizar`,
`GET .../contexto` e `POST .../decisao`, que **não existem em `main`**.
Arquivo: `backend/tests/aceite/test_t09_contexto.py` (+ `conftest.py`, `fakes.py`).

| CA | Testes | Situação |
| --- | --- | --- |
| CA26 | `test_sincronizar_importa_e_reimportar_nao_duplica`, `test_nova_versao_do_mesmo_registro_e_importada_sem_duplicar_o_anterior`, `test_registro_sem_vinculo_seguro_fica_pendente` | Escrito, não passa |
| CA27 | `test_cada_item_aponta_para_evidencia_real_do_proprio_cliente`, `test_item_com_evidencia_de_outro_cliente_ou_trecho_inexistente_e_rejeitado`, `test_inferencia_aparece_como_hipotese_nao_confirmada` | Escrito, não passa |
| CA28 | `test_conflito_entre_formulario_e_conversa_e_sinalizado` | Escrito, não passa |
| CA29 | `test_data_de_familiar_nao_vira_aniversario_do_cliente_nem_lembrete_confirmado` | Escrito, não passa |
| CA30 | `test_decisao_persiste_apos_reiniciar_e_nao_envia_mensagem` (aprovar, descartar, adiar), `test_edicao_preserva_valor_original_e_exige_valor`, `test_decisao_invalida_nao_altera_nada` | Escrito, não passa |
| CA31 | `test_irrelevante_nesta_ocasiao_mantem_interesse_e_nao_repete_sugestao` | Escrito, não passa |
| CA32 | `test_bloquear_assunto_afeta_apenas_o_cliente_escolhido`, `test_ausencia_de_resposta_nao_e_aprovacao_nem_rejeicao` | Escrito, não passa |
| CA33 | `test_reprocessar_preserva_correcao_e_evidencia_conflitante_pede_revisao` | Escrito, não passa |
| (CA14/RN13) | `test_preferencia_somente_financeiro_exclui_sugestoes_pessoais` | Escrito, não passa |
| (contrato 503) | `test_fonte_indisponivel_mantem_contexto_e_sinaliza` | Escrito, não passa |

## Critérios sem teste e sem implementação

| CA | Tema | Tarefa |
| --- | --- | --- |
| CA11 | Resumo mostra nova conversa como fonte | T09 |
| CA12 | Tratar a última pendência alta recalcula filtros e contagens | Base (comportamento existe; sem teste com esse enunciado) |
| CA13 | Evento repetido mantém um alerta | T08/CA06 |
| CA14 | Preferência financeira retira sugestões pessoais | Base (alertas: coberto por CA07) e T09 (contexto: teste na branch) |
| CA15 | Falha ao salvar preserva o texto na tela | Interface (verificação manual) |
| CA16–CA25 | NewsAPI, reuniões, keynotes | T08 |

## Pendências para fechar a tabela

1. CA10 e CA15: verificação manual no navegador (celular).
2. Acrescentar teste direto para CA09 (alerta financeiro não altera relacionamento) e CA35 (ano seguinte).
3. Mergear a branch de aceite só depois de conferir os 17 testes removidos
   no commit "reduz a suíte ao essencial" (47 em `main` contra 30 na branch).
4. Nomear os testes ou marcá-los com o ID do CA (`@pytest.mark.ca("CA05")`)
   para a rastreabilidade deixar de depender de leitura.
