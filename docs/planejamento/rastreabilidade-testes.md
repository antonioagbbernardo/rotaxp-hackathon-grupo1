# Rastreabilidade: critérios de aceite × testes

Status: levantamento de 10/10/2026 na branch `test/cobertura-ca-base`, com a
`main` de 75d7898 (inclui T09). Os testes não citam IDs `CA` no código; a ligação abaixo vem
da leitura do corpo de cada teste. Novos testes: `backend/tests/test_cobertura_ca.py`.

Verificação (execução real): `uv run --locked pytest` → **172 passaram** (125 da `main` + 47 de `test_cobertura_ca.py`).

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
| CA01 | `test_api::test_ca01_busca_e_filtro`, `test_cobertura_ca::test_ca01_*` | Coberto: prefixo, sobrenome, acento, caixa, sem resultado, faixas e busca combinada com filtro |
| CA02 | `test_cobertura_ca::test_ca02_detalhe_traz_exatamente_os_dados_e_preferencias_do_cliente` | Coberto: ids conferidos contra o banco e preferências do seed |
| CA03 | `test_api::test_ca03_registrar_interacao_persiste_apos_reiniciar_aplicacao`, `test_cobertura_ca::test_ca03_*` | Coberto, inclusive instantes automáticos |
| CA04 | `test_api::test_ca04_interacao_invalida_nao_cria_registro`, `test_cobertura_ca::test_ca04_*` | Coberto: erro identifica o campo e nada é criado; cliente inexistente → 404 sem registro |
| CA05 | `test_rules::test_ca05_classificar_vencimento`, `test_alertas::test_limites_*`, `test_cobertura_ca::test_ca05_*` | Coberto, incluindo vencido há 31 e 400 dias. Ver decisão sobre singular abaixo |
| CA06 | — | Sem teste automatizado (opcional, T08) |
| CA07 | `test_rules`, `test_alertas`, `test_cobertura_ca::test_ca07_*` | Coberto de ponta a ponta: contato de hoje, limite 7/6 dias, ocorrência × registro, intervalo das preferências, fuso perto da meia-noite |
| CA08 | `test_api::test_tratar_alerta_*`, `test_cobertura_ca::test_ca08_*` | Coberto, com contagens absolutas do seed |
| CA09 | `test_api::test_relacionamento_exige_justificativa_*`, `test_cobertura_ca::test_ca09_*` | Coberto nos dois sentidos (alerta não altera relacionamento; relacionamento não altera prioridade, RN11) |
| CA10 | `test_api::test_ca10_parcial_pagina_base_responde` (só GET `/` → 200) | **Sem teste automatizado; não verificado em celular** |
| CA12 | `test_cobertura_ca::test_ca12_*` | Coberto: prioridade, filtros e contagem absoluta (3 → 2) |
| CA34 | `test_alertas::test_ca34_prioridade_do_cliente_e_a_maior_pendente`, `test_api::test_ca34_prioridade_recalculada_apos_tratar` | Coberto |
| CA35 | `test_alertas`, `test_cobertura_ca::test_ca35_*` | Coberto: um alerta, RN13, tratado no mesmo ano e nova ocorrência no ano seguinte |
| CA36 | `test_cobertura_ca::test_ca36_*`, `::test_rn02_*` | Coberto; desempate por registro isolado do id |
| CA37 | `test_api::test_ca37_resumo_com_fontes_e_ausencias`, `test_cobertura_ca::test_ca37_*` | Coberto: fonte existe e pertence ao cliente; ausência não vira fato; próximos passos e relacionamento |
| CA38 | `test_api::test_ca38_resultado_independe_do_dia_real`, `test_cobertura_ca::test_ca38_*` | Coberto: outro dia, fuso e seed sobre todas as tabelas. Não há teste do comando CLI `flask seed` |
| CA39 | `test_cobertura_ca::test_ca39_*`, `test_alertas::test_ca39_calculo_e_idempotente_sem_duplicar` | Coberto: contagens e chaves únicas |
| RN11 | `test_cobertura_ca::test_rn11_*` | Coberto, incluindo desempate por nome |

## T09 (CA40–CA56): incrementos 01 e 02 (testes em `main`)

Os testes passam a trazer o ID no nome (`test_caNN_...` ou `test_rnNN_...`).
Estes testes ainda **não passaram por revisão independente nem mutação**; o
mapeamento abaixo vem do nome e da descrição do CA, não de leitura do corpo.
Os CA26–CA33 da proposta antiga (`test/aceite-congelados`) foram substituídos
por estes e a branch está obsoleta.

| CA | Testes | Situação |
| --- | --- | --- |
| CA40 | `test_fontes::test_ca40_*` (3) | A revisar |
| CA41 | `test_fontes::test_ca41_reimportacao_idempotente_apos_reinicio` | A revisar |
| CA42 | `test_fontes::test_ca42_identidade_nao_resolvida_*` | A revisar |
| CA43 | `test_fontes::test_ca43_*` (2) | A revisar |
| CA44 | `test_fontes::test_ca44_conflito_nao_grava_parte_do_lote` | A revisar |
| CA45 | `test_fontes::test_ca45_*` (4) | A revisar |
| CA46 | `test_fontes::test_ca40_importa_formulario_e_conversa_sem_alterar_decisoes_humanas` | A revisar |
| CA47 | — | **Sem teste automatizado** (interface; o texto do incremento admite verificação visual parcial) |
| CA48 | `test_contexto::test_ca48_*` (2) | A revisar |
| CA49 | `test_contexto::test_ca49_cache_novidades_e_correcao_persistem_apos_reinicio` | A revisar |
| CA50 | `test_contexto::test_ca50_*` (2), `test_ia_gemini::test_ca50_*` | A revisar |
| CA51 | `test_contexto::test_ca51_acoes_humanas_e_adiamento` | A revisar |
| CA52 | `test_contexto::test_ca52_*` (2) | A revisar |
| CA53 | `test_contexto::test_ca53_*` (2) | A revisar |
| CA54 | `test_contexto::test_ca54_*` (2), `test_ia_gemini::test_ca54_*` (3) | A revisar |
| CA55 | `test_contexto::test_ca55_*` (2) | A revisar |
| CA56 | — | **Sem teste automatizado** (interface) |
| RN27, RN31 | `test_contexto::test_rn27_*`, `::test_rn31_*` | A revisar |

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
