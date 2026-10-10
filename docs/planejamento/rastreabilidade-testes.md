# Rastreabilidade: critérios de aceite × testes

Status: levantamento de 10/10/2026 na branch `test/cobertura-ca-base`, com a
`main` de 75d7898 (inclui T09). Os testes não citam IDs `CA` no código; a ligação abaixo vem
da leitura do corpo de cada teste. Novos testes: `backend/tests/test_cobertura_ca.py`.

Verificação (execução real): `uv run --locked pytest` → **244 passaram** (125 da `main` + 47 de `test_cobertura_ca.py` + 72 de `test_cobertura_t09.py`).

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

## T09 (CA40–CA56): incrementos 01 e 02

Os testes trazem o ID no nome (`test_caNN_...` ou `test_rnNN_...`). Os da
equipe estão em `test_fontes.py`, `test_contexto.py` e `test_ia_gemini.py`; os
acrescentados após a revisão estão em `test_cobertura_t09.py`.

Avaliação: dois revisores de fidelidade (Opus e Fable) e dois de mutação (Opus:
88 mutantes, 54 mortos; Fable: 84 contabilizados, 56 mortos). Os sobreviventes
e os "mortos pelo motivo errado" viraram testes novos. Reaplicados os 39
mutantes sobreviventes, **39/39 morreram**. Isso mostra sensibilidade, não
ausência de defeitos. O provedor Gemini é simulado: a forma real da resposta
da API não é verificada por pytest.

| CA | Testes | Situação |
| --- | --- | --- |
| CA40 | `test_fontes::test_ca40_*`, `test_cobertura_t09::test_ca40_*` | Coberto: tipos, isolamento, ordenação decrescente, conteúdo preservado |
| CA41 | `test_fontes::test_ca41_*`, `test_cobertura_t09::test_ca41_*` | Coberto: reimportação, reinício e chaves do formulário em outra ordem |
| CA42 | `test_fontes::test_ca42_*`, `test_cobertura_t09::test_ca42_*` | Coberto: pendência, reuso e referência preservada |
| CA43 | `test_fontes::test_ca43_*`, `test_cobertura_t09::test_ca43_*` | Coberto: v1, v3, v2 e registro preservado |
| CA44 | `test_fontes::test_ca44_*`, `test_cobertura_t09::test_ca44_*` | Coberto: 409 com campo exato e sem gravação parcial |
| CA45 | `test_fontes::test_ca45_*`, `test_cobertura_t09::test_ca45_*` | Coberto, inclusive limites e marca fictícia |
| CA46 | `test_fontes::test_ca40_importa_formulario_*`, `test_cobertura_t09::test_ca46_*` | Coberto: interações manuais comparadas campo a campo |
| CA47 | — | **Sem teste automatizado** (interface) |
| CA48 | `test_contexto::test_ca48_*` | Coberto |
| CA49 | `test_contexto::test_ca49_*`, `test_cobertura_t09::test_ca49_*` | Coberto: cache por estado e modelo, só documento novo enviado |
| CA50 | `test_contexto::test_ca50_*`, `test_ia_gemini::test_ca50_*`, `test_cobertura_t09::test_ca50_*` | Coberto: limites 30/5/80/500, literalidade e campo certo do erro |
| CA51 | `test_contexto::test_ca51_*`, `test_cobertura_t09::test_ca51_*` | Coberto: histórico completo e correção preservada |
| CA52 | `test_contexto::test_ca52_*`, `test_cobertura_t09::test_ca52_*` | Coberto: sujeito, conflito e evidência atual isolados como causa |
| CA53 | `test_contexto::test_ca53_*`, `test_cobertura_t09::test_ca53_*` | Coberto: isolamento entre clientes e descarte só do item |
| CA54 | `test_contexto::test_ca54_*`, `test_ia_gemini::test_ca54_*`, `test_cobertura_t09::test_ca54_*` | Coberto, com ressalva: contrato real do Gemini não verificado |
| CA55 | `test_contexto::test_ca55_*`, `test_cobertura_t09::test_ca55_*` | Coberto: campo do erro, 404 com corpo válido e tentativa substituída |
| CA56 | — | **Sem teste automatizado** (interface) |
| RN27 | `test_contexto::test_rn27_*`, `test_cobertura_t09::test_rn27_*` | Coberto: fronteira de 2 minutos e concorrência sem recursão |
| RN31 | `test_contexto::test_rn31_*` | Coberto |
| RN32 | `test_cobertura_t09::test_rn32_*` | Coberto: resumo, alertas e datas inalterados após aprovar |

Divergência a decidir pela equipe: `contracts.md` diz que `elegivel_contato`
exige permissão e intervalo pessoal, mas `contexto.py` só aplica isso às
categorias `interesse`, `data_importante` e `preferencia`; `objetivo`,
`compromisso` e `ponto_atencao` ficam livres. Nenhum documento descreve a exceção.

## Síntese OpenAI (CA65–CA71): incremento 04

Integração na `main` com a base `52eb841`: `uv run --locked pytest -q` →
**288 aprovados** (262 anteriores + 26 de `test_resumo_ia.py`). Transporte OpenAI
simulado nos testes; duas chamadas reais fictícias registradas separadamente
em [registro de desenvolvimento](../registro-desenvolvimento.md).

| CA | Testes em `test_resumo_ia.py` | Evidência |
| --- | --- | --- |
| CA65 | `test_get_sem_chamada_fatos_separados_cache_persistente` | Linhas/plural cobertos; layout e fontes conferidos manualmente antes do merge |
| CA66 | `test_get_sem_chamada_fatos_separados_cache_persistente` | GET, reuso por POST e cache após recriar a aplicação |
| CA67 | `test_mudancas_invalidam_cache`, `test_mudanca_durante_chamada_nao_persiste_e_permite_retry`, `test_selecao_nao_envia_propostas_bloqueios_terceiros_transcricoes` | Contato, preferência, vencimento, data/modelo e correção de contexto; alteração durante geração |
| CA68 | `test_saida_invalida_nao_persiste` | Formato, tamanho, fontes, ausência de saída persistida |
| CA69 | `test_selecao_nao_envia_propostas_bloqueios_terceiros_transcricoes` | Cliente, revisão, hipóteses, bloqueio, conflito, fonte antiga e elegibilidade |
| CA70 | `test_configuracao_entrada_grande_e_corpo_sem_chamada`, `test_transporte_*` | Configuração, limite, schema, timeout, HTTP 401/429, recusa e saída incompleta |
| CA71 | `test_requisicao_concorrente_e_retomada_de_tentativa`, `test_tentativa_antiga_nao_sobrescreve_a_retomada` | Concorrência, retomada e preservação do resultado mais recente |

## Notícias (CA72–CA78): incremento 05

Execução atual: **329 testes backend**, incluindo 41 novos em `test_noticias.py`.
Provedor/transporte simulados nos testes; uma chamada real compartilhada entre
dois clientes fictícios documentada no registro, sem chamadas Gemini/OpenAI.

| CA | Testes em `test_noticias.py` | Evidência |
| --- | --- | --- |
| CA72 | `test_vinculo_recusa_*`, `test_releitura_oculta_*`, `test_item_alheio_*` | Revisão humana, tipo/sujeito/categoria, origem atual, conflito, bloqueio, preferência, contato e cliente |
| CA73 / CA16 | `test_get_sem_http_vinculo_explicito_cache_compartilhado_e_reinicio`, `test_vazio_e_sucesso_cli_reutiliza_e_novo_dia_coleta` | GET, reuso entre clientes, vazio, CLI, persistência e novo dia |
| CA74 / CA18 | `test_erro_preserva_cache_intervalo_e_recuperacao`, `test_sem_chave_*`, `test_transporte_falhas_*` | Preservação de cache, intervalo, credencial, timeout, formato e limites externos |
| CA75 | `test_cota_conta_falha_*`, `test_erro_global_*`, `test_concorrencia_e_tentativa_antiga_nao_sobrescrevem` | Orçamento, fuso/dia local, suspensão global, lease e tentativa substituída |
| CA76 | `test_deduplicacao_limite_janela_e_artigos_removidos`, `test_saida_invalida_nao_persiste_parcial`, `test_transportadora_*` | URLs, publicação, janela, fonte, limite e cabeçalho sem dados pessoais |
| CA77 / CA31–CA32 (notícia) | `test_feedback_motivo_isolamento_idempotencia_persistencia` | Motivo, cliente, idempotência, persistência e base inalterada |
| CA78 | Manual, além dos contratos de API | Desktop: associação/busca/reuso/feedback; DOM móvel 390/390 px. Inspeção visual móvel dos cartões parcial; sem celular físico |

`test_pergunta_noticias_le_cache_com_fontes_e_respeita_bloqueio` verifica consulta
com fonte/link sem HTTP novo e sem expor notícia de assunto bloqueado.

## Sem teste e sem implementação

| CA | Tema | Tarefa |
| --- | --- | --- |
| CA11 | Resumo mostra nova conversa importada como fonte | T09 |
| CA13 | Evento repetido mantém um alerta | T08/CA06 |
| CA15 | Falha ao salvar preserva o texto (interface) | Verificação manual/E2E |
| CA17, CA19–CA25 | Reuniões, antecipação da coleta e keynotes | Incremento 07 implementado; testes direcionados abaixo, visual adicional pendente |

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

## Incremento 06 — login (RF31, CA79–CA84)

23 casos em `test_autenticacao.py`: mapa completo de APIs protegido, login e
validação de campos, CSRF, cookie adulterado, validade absoluta, revogação,
reinício/chave 0600 e cache HTTP. Testes de domínio fazem login HTTP real.
Seis casos frontend em `auth.test.mjs`: envio de token/cookie, evento 401,
credenciais inválidas, renovação de sessão no login/logout e erro de rede.

Execução no incremento 06: **352 backend + 11 frontend**, lint/build aprovados. Desktop do
login conferido; mobile e conferência visual adicional adiados a pedido do
usuário. As evidências visuais anteriores conservam seus limites individuais.

## Incrementos 07/08 — agenda e lembranças

Verificação mínima atual: **17 casos backend direcionados + 11 frontend**, lint
e build aprovados. Suíte backend completa e visual adicionais adiados pelo usuário.
Contagem de 352/11 acima é da última suíte completa, antes destas alterações.

| Aceite | Evidência executada | Limite |
| --- | --- | --- |
| CA85 | `test_agenda::test_ca85_identidade_validacao_e_isolamento` | API + perguntas básicas |
| CA86 | `test_agenda::test_ca86_pauta_fontes_reuso_revisao_e_notas_preservadas` | Versão atual/notas, sem inspeção visual |
| CA87 | `test_agenda::test_ca87_cancelamento_reagendamento_e_conclusao_unica` | Uma interação no retry |
| CA88 | Dois casos `test_ca88_*` em `test_agenda.py` | Cache 2h compartilhado, cota e aviso com pauta interna; NewsAPI simulada |
| CA89 | `test_agenda::test_ca89_cli_janela_reuso_e_cancelada` | 24h inclusivo, ciclo CLI e versão reutilizada |
| CA90, CA94 | Lint e build frontend | Fluxo visual completo pendente |
| CA91 | `test_ca91_*` em `test_lembrancas.py` | Sujeito/fonte/data/idempotência; terceiro, hipótese e ambiguidade recusados |
| CA92 | `test_ca92_recorrencia_e_compromisso_vencido` | 29/02, compromisso vencido e janela |
| CA93 | Dois casos `test_ca93_*` em `test_lembrancas.py` | Adiamento/revisão/bloqueio, sem duplicação e nova versão após edição |

Quatro regressões executadas: guarda de todas as APIs (`test_autenticacao`),
cache compartilhado/reinício e erro preservando cache (`test_noticias`),
bloqueio auditado/reset (`test_contexto`). Nenhuma chamada externa neste lote.
