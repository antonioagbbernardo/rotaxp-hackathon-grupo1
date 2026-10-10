# Rastreabilidade: critérios de aceite × testes

Status: levantamento de 10/10/2026 na branch `test/cobertura-ca-base`, sobre
`main` (7456543). Os testes não citam IDs `CA` no código; a ligação abaixo vem
da leitura do corpo de cada teste. Novos testes: `backend/tests/test_cobertura_ca.py`.

Verificação (execução real): `uv run --locked pytest` → **94 passaram**.

## Como foi avaliado

- Revisão de fidelidade à spec por dois revisores independentes (Opus e Fable),
  que não escreveram os testes e não viram o raciocínio do autor.
- Teste de mutação por dois revisores (Opus: 56 mutantes; Fable: 61 mutantes) sobre
  a aplicação, com a suíte inteira por mutante.
- Resultado inicial: 44/56 e 47/61 mutantes mortos (≈ 78%). Os sobreviventes
  apontaram testes fracos (abaixo), corrigidos nesta branch.
- Depois das correções, os 28 mutantes que haviam sobrevivido ou eram os mais
  frágeis (fuso, `date.today()`, intervalo de contato, desempate de RN02, fonte do
  resumo, relacionamento × prioridade, busca com acento, seed) foram reaplicados:
  **28/28 mortos**. Isso é evidência de sensibilidade dos testes, não prova de
  ausência de defeitos.
- Painel GPT não foi usado: o runtime não está instalado neste notebook.

Legenda: **Coberto**, **Parcial**, **Sem teste automatizado**,
**Escrito, não passa** (só na branch `test/aceite-congelados`).

## Base (CA01–CA10, CA12, CA34–CA39)

| CA | Testes principais | Situação |
| --- | --- | --- |
| CA01 | `test_api::test_busca_e_filtro`, `test_cobertura_ca::test_ca01_*` | Coberto: prefixo, sobrenome, acento, caixa, sem resultado, faixas e busca combinada com filtro |
| CA02 | `test_cobertura_ca::test_ca02_detalhe_traz_exatamente_os_dados_e_preferencias_do_cliente` | Coberto: ids conferidos contra o banco e preferências do seed |
| CA03 | `test_api::test_registrar_interacao_persiste_apos_reiniciar_aplicacao`, `test_cobertura_ca::test_ca03_*` | Coberto, inclusive instantes automáticos |
| CA04 | `test_api::test_interacao_invalida_nao_cria_registro`, `test_cobertura_ca::test_ca04_*` | Coberto: erro identifica o campo e nada é criado; cliente inexistente → 404 sem registro |
| CA05 | `test_rules::test_classificar_vencimento`, `test_alertas::test_limites_*`, `test_cobertura_ca::test_ca05_*` | Coberto, incluindo vencido há 31 e 400 dias. Ver decisão sobre singular abaixo |
| CA06 | — | Sem teste automatizado (opcional, T08) |
| CA07 | `test_rules`, `test_alertas`, `test_cobertura_ca::test_ca07_*` | Coberto de ponta a ponta: contato de hoje, limite 7/6 dias, ocorrência × registro, intervalo das preferências, fuso perto da meia-noite |
| CA08 | `test_api::test_tratar_alerta_*`, `test_cobertura_ca::test_ca08_*` | Coberto, com contagens absolutas do seed |
| CA09 | `test_api::test_relacionamento_exige_justificativa_*`, `test_cobertura_ca::test_ca09_*` | Coberto nos dois sentidos (alerta não altera relacionamento; relacionamento não altera prioridade, RN11) |
| CA10 | `test_api::test_pagina_base` (só GET `/` → 200) | **Sem teste automatizado; não verificado em celular** |
| CA12 | `test_cobertura_ca::test_ca12_*` | Coberto: prioridade, filtros e contagem absoluta (3 → 2) |
| CA34 | `test_alertas::test_prioridade_do_cliente_e_a_maior_pendente`, `test_api::test_prioridade_recalculada_apos_tratar` | Coberto |
| CA35 | `test_alertas`, `test_cobertura_ca::test_ca35_*` | Coberto: um alerta, RN13, tratado no mesmo ano e nova ocorrência no ano seguinte |
| CA36 | `test_cobertura_ca::test_ca36_*`, `::test_rn02_*` | Coberto; desempate por registro isolado do id |
| CA37 | `test_api::test_resumo_com_fontes_e_ausencias`, `test_cobertura_ca::test_ca37_*` | Coberto: fonte existe e pertence ao cliente; ausência não vira fato; próximos passos e relacionamento |
| CA38 | `test_api::test_resultado_independe_do_dia_real`, `test_cobertura_ca::test_ca38_*` | Coberto: outro dia, fuso e seed sobre todas as tabelas. Não há teste do comando CLI `flask seed` |
| CA39 | `test_cobertura_ca::test_ca39_*`, `test_alertas::test_calculo_e_idempotente_sem_duplicar` | Coberto: contagens e chaves únicas |
| RN11 | `test_cobertura_ca::test_rn11_*` | Coberto, incluindo desempate por nome |

## T09 (CA26–CA33): testes só em `test/aceite-congelados`

Dependem de código que não existe em `main` (`cliente.ref_externa`,
`/api/fontes/sincronizar`, `.../contexto`, `.../decisao`). Na branch: 30
passaram, 1 falhou, 18 com erro. Nenhum CA26–CA33 está verificado.

## Sem teste e sem implementação

| CA | Tema | Tarefa |
| --- | --- | --- |
| CA11 | Resumo mostra nova conversa importada como fonte | T09 |
| CA13 | Evento repetido mantém um alerta | T08/CA06 |
| CA15 | Falha ao salvar preserva o texto (interface) | Verificação manual/E2E |
| CA16–CA25 | NewsAPI, reuniões, keynotes | T08 (sem contrato de rotas) |

## Decisões pendentes da equipe (não resolvidas por teste)

1. **Singular em rótulos:** a spec escreve "Vencido há N dias"; a implementação
   gera "Vencido há 1 dia" / "Vence em 1 dia". Os testes assumem o singular.
2. **RN08:** `data_referencia` é `None` nos fatos de perfil e de contagem de
   posições. A spec lista o campo em toda fonte; decidir se `None` é aceitável.
3. **Canal padrão:** RN13 diz que o canal preferido é o padrão ao registrar
   interação, mas a API exige `canal`. Sem teste, aguardando decisão.

## Pendências

1. CA10 e CA15 em navegador (celular).
2. Testar o comando `flask seed` via `test_cli_runner` (CA38).
3. Antes de mergear `test/aceite-congelados`, conferir os 17 testes removidos no
   commit "reduz a suíte ao essencial".
4. Marcar os testes com o ID do CA para a rastreabilidade não depender de leitura.
