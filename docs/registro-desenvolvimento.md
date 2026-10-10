# Registro de desenvolvimento e material para apresentação

Atualizado em 10/10/2026. Fonte de trabalho para o pitch de até 5 minutos.
Registrar entregas de frontend e backend junto com requisitos, testes e limites;
não apresentar planos ou mocks como integrações reais.

## Mensagem do produto

Poupar o tempo do assessor e ajudá-lo a melhorar a relação com o investidor.
Transformar informações já existentes em contexto e acompanhamento pertinente,
mantendo a decisão final com o assessor. A ferramenta apoia o profissional;
não pretende substituí-lo nem conduzir o relacionamento autonomamente.

Problema: conversas dispersas dificultam lembrar combinados, interesses e
pendências. Benefício pretendido: preparar atendimento com evidências e reduzir
buscas repetidas. Ainda não medimos ganho de tempo, qualidade ou adoção.

## Diferencial proposto e como defendê-lo

**Proposta de valor:** preparar o assessor com contexto rastreável do investidor,
respeitando como ele quer se relacionar e aprendendo com a revisão do profissional.

| Elemento da proposta | Por que importa | Evidência para o pitch |
| --- | --- | --- |
| Conversas e formulário conectados | Evita reunir o histórico de cada canal manualmente antes do contato | Fonte versionada e histórico; conexão real ainda pendente |
| Fatos, hipóteses e origem separados | Assessor consegue conferir e corrigir o que será usado no atendimento | Incremento 02 implementado com testes simulados; qualidade real pendente |
| Preferências e pertinência pessoal | Lembrar de algo só é útil se fizer sentido para aquele investidor | Permissão/intervalo da base e bloqueio individual implementados |
| Feedback com alcance explícito | Corrigir ou descartar uma sugestão não apaga um interesse nem afeta outros clientes | Revisão/correção/bloqueio persistidos e testados |
| Preparação de reunião com custo compartilhado | Reaproveita contexto e notícias por assunto em vez de repetir trabalho por cliente | NewsAPI, cache e keynotes planejados, ainda não demonstrados |

Essa combinação é a **hipótese de diferenciação**, não prova de exclusividade.
Não afirmar “único no mercado” sem comparação documentada com concorrentes.
O pitch deve mostrar o ciclo e seu benefício, com cada capacidade marcada como
implementada, demonstrada ou planejada.

Antes de alegar ganhos: medir tempo para preparar o mesmo atendimento com e sem
a ferramenta, com o mesmo cenário; registrar correções necessárias e relevância
das sugestões avaliadas pelo assessor. Não inventar percentuais de economia.

**Frase para o pitch:** “Damos ao assessor mais tempo para cuidar do investidor:
organizamos o histórico em contexto com evidências, para que ele revise e conduza
um relacionamento mais pertinente.”

Para demonstrar o diferencial, usar um caso: conversa revela um interesse,
o sistema apresenta o trecho, o assessor corrige a proposta e bloqueia o assunto
para contato sem perder o histórico. O aprendizado aqui é aplicar decisões
persistidas; não é retreinamento automático do modelo.

## Entregas e evidências

| Entrega | Frontend | Backend | Evidência e limite |
| --- | --- | --- | --- |
| Base integrada | Lista com busca/filtro, detalhe, histórico, preferências, avaliação e tratamento de alertas | Flask/SQLite, Clock injetável, resumo por template com fontes, alertas sob demanda | 47 testes aprovados na base; HTTP e CSS verificados. Sem avaliação visual nesta sessão |
| Organização | React em `frontend/`; build pode ser servido pelo Flask | API/testes/lockfiles Python em `backend/`; documentos em `docs/` | Base organizada em `7456543`; execução atual no README |
| Incremento 01: fontes | Importação JSON, resultado/erro, pendências de identidade, versões e origem no detalhe/histórico | Validação pura, transação SQLite, documentos versionados e API/CLI compartilhados | Implementado: 34 testes novos + 47 anteriores = 81 aprovados; CSS e sintaxe JS verificados; visual parcial |
| Incremento 02: contexto e feedback | Processamento, fila, evidências, quatro ações e bloqueio por cliente | Gemini REST, validação literal, cache, controle de concorrência, revisão/auditoria | 44 testes novos, total 125; testes simulados + extração real de 4 fontes/7 propostas. Visual completo pendente |
| Notícias e reuniões | Notícias pertinentes e keynotes | NewsAPI compartilhada, cache, preparação de pauta | Planejado, não implementado |
| Incremento 03: XP Pulse integrado | Layout React recebido da equipe; clientes, resumo, carteira, percepção, fontes, revisão, alertas e registros conectados | Adaptador `/api/pulse`, perguntas por templates, assets no Flask; SQLite e regras anteriores preservados | 143 testes backend + cinco frontend, build/lint aprovados; fluxos no navegador e viewport móvel, com limites abaixo |

## Registro SDD por incremento

### 01 — Entrada de fontes existentes simuladas

- Problema: histórico atual exige cadastro manual; falta entrada rastreável das fontes.
- Especificação: [incremento 01](planejamento/incrementos/01-fontes.md), RF03/RF04/RF16/RF25, CA40–CA47.
- Contrato: [fontes fictícias](planejamento/contracts.md#incremento-01--contrato-de-fontes-fictícias).
- Decisão: JSON local simula formulário/conversas; identidade por ID, versões imutáveis e pendências sem associação por nome.
- Testes antes do código: primeira execução registrou **30 falhas**, por ausência das rotas, tabela e fixture. Na revisão, limites de inteiros foram especificados e dois casos adicionais falharam antes da correção. Execução final: **81 testes aprovados** (34 de fontes, 47 da base).
- Backend: `backend/app/fontes_rules.py` valida o contrato sem I/O; `fontes.py` importa em transação e atende API/CLI; `db.py` acrescenta `documento_fonte` sem apagar a base. Origem/registro/versão únicos, evidências anteriores preservadas, conflito 409 e lote sem gravação parcial.
- Frontend: `backend/app/static/js/app.js` ganha seletor de JSON, resultado/erro, botão bloqueado durante importação, pendências, fontes atuais/anteriores e origem no histórico. Conteúdo renderizado em nós de texto. CSS recompilado.
- Dados: `backend/dados/fonte-demo.json`, 14 documentos para três clientes fictícios (três formulários, nove conversas e duas identidades pendentes).
- Demonstração executada pela CLI: primeira carga **14 importados / 0 reutilizados / 2 pendentes**; segunda carga **0 importados / 14 reutilizados / 2 pendentes**.
- Validação de interface: lista, seletor e pendências renderizados no Chrome nativo, com screenshot inspecionada. Fluxo completo de seleção/envio, detalhe e viewport móvel permanecem pendentes; automação nativa interrompida por falha de captura de áudio/vídeo. Testes de API não substituem essa validação.
- Demonstração para o pitch: importar fonte → abrir Ana → consultar formulário/conversa e origem → repetir lote sem duplicação. Ensaio completo ainda pendente.
- Limites: não é conexão real nem extração por IA. Sem envio ao cliente, sem alteração automática de preferências.

Comandos executados dentro de `backend/`:

```bash
uv run --locked pytest
npm run css:build
node --check app/static/js/app.js
uv run flask --app app importar-fontes dados/fonte-demo.json
uv run flask --app app run -p 5001
```

Não houve chamadas a IA ou NewsAPI neste incremento. Custo externo desta execução:
nenhuma chamada; não representa estimativa do custo futuro. Credenciais ficam
apenas na configuração local ignorada, nunca neste documento ou nos mocks.

### 02 — Contexto e revisão sob decisão do assessor

- Especificação/contrato antes do código: RN24–RN32 e CA48–CA56 no
  [incremento 02](planejamento/incrementos/02-contexto-revisao.md).
- Primeira execução: **28 testes falharam** por ausência das rotas. Implementação
  aprovada; verificações adicionais de transporte/concorrência/limites/auditoria
  resultaram em **125 testes aprovados** (44 novos, 81 anteriores).
- Backend: Gemini REST com JSON estruturado, timeout 30 s, até 40 mil caracteres,
  validação de fonte/trecho/campo antes de persistir. Processa apenas novidades;
  não mantém transação SQLite durante a chamada externa. Erros preservam contexto.
- Revisão: quatro ações com motivo, versão, assessor e data. Valor original e
  correção preservados; nova versão pode sinalizar possível divergência. Bloqueio
  é individual, auditado e não apaga o contexto. Sem decisões implícitas.
- Frontend: processamento explícito, fila e revisados separados, fontes, sujeito,
  conflitos, correção/adiamento e preferência de assunto. Requisições de formulários
  bloqueiam repetição enquanto estão em andamento; texto da API continua seguro.
- Princípio do produto: preparar o assessor, poupar sua busca e manter a decisão
  profissional com ele. Sem envio, mudança automática de humor/perfil/aniversário
  ou influência sobre prioridade da base.
- Verificação: `uv run --locked pytest -q` (125 aprovados), `node --check
  app/static/js/app.js`, `npm run css:build` e `git diff --check`.
- Interface: detalhe de Ana, fontes, mensagem de apoio ao assessor, estado sem
  chave e fila vazia confirmados pela árvore de acessibilidade do Chrome. Captura
  visual retornou imagem cinza; ação posterior interrompida por mudança do usuário.
  Fluxo com propostas carregadas e viewport móvel não verificados.
- HTTP local: página, JS e consulta do contexto retornaram 200; processamento
  sem chave retornou 503 com orientação de configuração e sem contexto falso.
- Chave Gemini configurada apenas no `.env` ignorado, com permissões 0600.
  Teste real em 10/10: quatro fontes fictícias de Ana produziram sete propostas,
  todas pendentes, com evidências literais validadas. Repetição retornou zero novas
  fontes/itens e `reutilizado: true`, sem nova chamada ao modelo.
- Amostra real: aniversário de Ana (12/10), interesse em Fórmula 1, objetivo,
  retorno sobre CDB e aniversário da filha em novembro. A filha permaneceu
  `familiar`, sem dia inventado. Uma menção nominal a Ana ficou com sujeito
  `incerto`; uma resposta genérica “Revisar com o assessor” virou proposta de
  preferência. São exemplos que exigem revisão, não prova de precisão geral.
- Compatibilidade: esquema completo recusado com HTTP 400. Isolação confirmou
  que o esquema sem `minItems/maxItems` era aceito. Enviar esquema simplificado,
  com formato REST atual `responseFormat`, mantendo os limites no validador local.
  Teste do transporte falhou antes das correções e os 125 testes passaram depois.
- Houve 11 requisições `generateContent` nesta validação: cinco recusadas e
  seis aceitas (cinco diagnósticos mínimos e uma extração). Uma consulta de
  modelos adicional; nenhuma chamada NewsAPI. Não medimos faturamento/tokens;
  essa investigação não representa custo rotineiro. Sem retries automáticos
  ou fallback simulado no produto. Nenhuma revisão humana aplicada à amostra.
- Entrega registrada em `dccc3e9` na `main` e enviada a pedido do usuário.
  Fonte real, lembretes derivados, notícias e keynotes pendentes.

### 03 — Integrar o layout XP Pulse à aplicação

- Pedido: buscar a primeira versão do frontend no repositório e adaptar as
  inconsistências para funcionar. `main` atualizada até `5eac9c5`; trabalho
  na branch `feat/integra-front-pulse`; commit/push autorizado pelo usuário após
  a validação da integração.
- SDD: [incremento 03](planejamento/incrementos/03-front-pulse.md), RN33–RN39,
  CA57–CA64 e contrato do painel escritos antes do código. Os 16 primeiros
  testes falharam pela ausência da integração; duas regressões adicionais
  falharam antes dos ajustes de preferência/atualização.
- Backend: `/api/pulse` adapta o formato do React com IDs da base e reutiliza
  prioridade, resumo, fontes e contexto existentes. Totais somados com Decimal,
  sem converter valores monetários em float. `/perguntar` consulta registros por
  templates com referências; não é conversa generativa e não recomenda ativos.
- Frontend: remove uso dos clientes/notícias fixos durante execução. Preserva
  o layout preto/amarelo, separa prioridade de relacionamento humano e mostra
  ausências de cadastro, contato e distribuição. Nova leitura após gravações,
  erro/retry, seleção por ID, cancelamento e proteção contra resposta antiga.
- Ações: importar JSON, consultar originais, processar fontes explicitamente,
  aprovar/corrigir/descartar/adiar, bloquear assunto, registrar contato,
  avaliar relacionamento, salvar preferências e tratar alertas pela API.
  Rascunhos de abertura por template são revisáveis/copiáveis; nenhum envio.
- Execução: Vite em `127.0.0.1:5173` com proxy para Flask na 5001; build
  `frontend/dist` servido em `/`, assets/favicon e interface anterior `/legacy`.
  Node necessário para compilar após o clone; build ignorado pelo Git.
- Verificação: `uv run --locked pytest -q` **143 aprovados** (18 novos);
  `npm test` **cinco aprovados**, `npm run lint`, `npm run build` e
  `git diff --check`. HTTP de build/assets/favicon/legacy e proxy verificados.
  Nenhuma chave encontrada nos arquivos publicáveis ou no bundle; `.env`
  permanece ignorado e com permissão 0600.
- Navegador: layout com cinco clientes do SQLite; Ana com sete propostas e
  R$ 80.000,00; pergunta de perfil com fonte; troca para Bruno sem manter
  resposta de Ana. Em cópia isolada da base: aprovação com evidência/auditoria,
  bloqueio do assunto sem apagar conhecimento, tratamento do alerta com
  prioridade recalculada, contato, avaliação e preferência pessoal persistidos
  após recarregar. Dados da demonstração original não alterados por esses testes.
- Celular: Chrome em viewport **390 × 844**, colunas empilhadas e medidas
  `innerWidth = scrollWidth = 390`. Verificação de layout; não equivale a teste
  em dispositivo físico nem a executar todos os formulários em celular.
  Importação pelo seletor e todas as variantes de revisão não foram executadas
  visualmente neste incremento; contratos correspondentes têm testes de API.
- Não houve novas chamadas Gemini ou NewsAPI. Reaproveitamos a amostra anterior
  para validar a revisão. NewsAPI, reuniões, keynotes, análise tributária/risco
  e autenticação continuam pendentes. Ganho de tempo ainda não medido.

**Demonstração sugerida:** lista priorizada → cliente → evidência e proposta →
decisão do assessor → interesse revisado/bloqueio → alerta tratado → registro
do contato e percepção. Pergunta básica mostra a fonte; notícias são evolução.

**Integração na main:** solicitada pelo usuário após o push da branch. A main
recebeu `67591c6` com logo, cursores e cartão mais claro. Conflitos de App,
resumo, cartão e lista conciliados: preservar esses ajustes visuais e os dados
da API, ausências explícitas e distinção entre relacionamento e prioridade.
Removido o `isDemo` do cabeçalho conforme seu contrato novo; indicação de dados
fictícios permanece no painel. Após a combinação: 143 testes backend e cinco
frontend aprovados, build e lint aprovados. Layout/fluxos visuais registrados
acima correspondem à integração anterior; não repetidos após este merge visual.

## Incremento SDD 04 — resumo OpenAI legível (10/10/2026)

- Problema: o assistente concatenava os fatos num parágrafo, com `dia(s)` e
  sem hierarquia. Pedido do usuário: usar sua API OpenAI e melhorar o texto.
  [Spec](planejamento/incrementos/04-resumo-openai.md), RN40–RN45/CA65–CA71 e
  contrato escritos antes do código; testes novos falharam por módulo ausente.
- Backend: Responses REST com JSON Schema estrito, `store: false`, saída
  limitada a 1.200 tokens, timeout de 30 segundos, erro seguro e nenhuma chave
  no frontend. Configuração local `OPENAI_API_KEY`/`OPENAI_MODEL`;
  modelo usado `gpt-4.1-mini`. Sem dependência/SDK adicional.
- Seleção: fatos, ausências, preferências, alertas pendentes e fatos revisados
  elegíveis. Propostas pendentes, hipóteses, bloqueios, terceiros, conflitos e
  evidências antigas não entram. Não enviamos transcrições completas.
  A avaliação de relacionamento aparece diretamente com autoria humana;
  não é reinterpretada na síntese. IA não altera nenhum registro/prioridade.
- Cache SQLite: uma síntese atual por cliente, assinatura do conteúdo, dia,
  modelo e prompt. GET não chama IA; POST repetido reutiliza resultado.
  Lock curto antes da chamada, proteção contra concorrência, retomada após
  dois minutos e verificação de versão antes de salvar. Mudança relevante
  esconde o resultado anterior até nova geração.
- Frontend: fatos em linhas com plural correto; botão de geração, carregamento,
  erro/retry. Síntese em **Visão geral**, **Pontos de atenção** e **Antes do
  contato**, fontes por trecho e registros originais acessíveis. Síntese e
  decisões humanas distintas; consultas básicas/rascunhos continuam por templates.
- Validação real: duas chamadas OpenAI para **Bruno fictício**, sendo a segunda
  um ajuste de redação/separação da avaliação humana. Ambas HTTP 200. Contadores
  do provedor: **1.912 tokens de entrada + 507 de saída = 2.419** no total.
  A síntese atual usou 1.205 tokens; repetição da primeira já demonstrou cache
  (`reutilizado: true`). Não medimos cobrança, economia financeira nem qualidade
  em uma amostra representativa. Não houve novas chamadas Gemini/NewsAPI.
- Testes: 26 novos casos (seleção, formato/fontes, erro/recusa/timeout, cache,
  alterações, persistência, concorrência e tentativa antiga); **169 backend**
  e **cinco frontend** aprovados, além de build, lint e diff sem erro.
- Navegador: síntese atual de Bruno visível no desktop e em viewport
  **390 × 844**, com três seções e quebras de texto; fonte da visão geral aberta
  e conferida. Sem cortes horizontais visíveis. Medição DOM da largura não foi
  obtida nesta conferência; não equivale a teste em celular físico. Geração/retry
  e falhas têm cobertura de API; botão não foi acionado visualmente neste lote.
- Limites: estrutura/IDs de fontes validados não garantem precisão semântica;
  assessor confere texto e fonte antes do atendimento. NewsAPI, reuniões,
  keynotes, análise tributária e autenticação continuam pendentes. Chave e cache
  são locais, não acompanham o clone; cada equipe configura a própria chave.

**Demonstração:** abrir Bruno → mostrar síntese e pendências → abrir fontes →
destacar avaliação do assessor → explicar cache e revisão final. Nos demais
clientes, “Preparar resumo com IA” solicita a geração explícita.

## Integração do incremento 04 na main

Solicitada pelo usuário. Atualização até `52eb841` preserva a cobertura adicional
da equipe e os ajustes de ícones/cartões/filtros do React. Merge automático sem
conflitos de texto; resolvida a divergência do README que descrevia o frontend
como mock independente. A documentação agora informa API Flask e proxy Vite.
Após a integração: **288 testes backend + cinco frontend**, lint, build e
diff aprovados. Credenciais locais excluídas do commit. A verificação visual
da síntese foi feita antes deste merge; o layout combinado não foi novamente
verificado em navegador. Não houve chamadas adicionais aos provedores.

Durante o push, a main remota avançou para `c84a9bd` (onda dourada no cabeçalho
do assistente). A atualização foi integrada sem conflitos, preservando o resumo
OpenAI. Os cinco testes frontend, lint e build passaram novamente. Backend
sem alterações neste merge; imagem nova não conferida em navegador.

## Correção: humor e prioridade visíveis no painel (10/10/2026)

- **Problema:** prioridade de atendimento só aparecia no cliente selecionado e o
  humor (relacionamento) era um ícone cinza sem texto; 4 dos 5 clientes do seed
  não têm avaliação (`unknown`).
- **Diagnóstico:** `/api/pulse` entrega `priority` e `sentiment` corretos (verificado
  com o seed); a falha era de renderização no frontend.
- **Frontend:** `ClientCard` mostra a prioridade e o humor com texto em português;
  `ClientSummary` mostra o humor do relacionamento e deriva o tom do badge da
  prioridade (antes vinha do status); rótulos em `lib/sentiment.ts`.
- **Backend/contrato:** sem mudança.
- **Verificação:** build, lint e testes do frontend; pytest do backend (288). Não
  validado no navegador/celular.

## Roteiro para a apresentação

| Tempo sugerido | Mostrar e explicar |
| --- | --- |
| 0:00–0:40 | Conversas dispersas e o que o assessor precisa saber antes do contato |
| 0:40–1:40 | Entrada de fontes e rastreabilidade; indicar dados fictícios e estágio real da entrega |
| 1:40–2:40 | Cliente, histórico, pendências e prioridade calculada |
| 2:40–3:40 | Conferir evidência, registrar revisão e mostrar o efeito do feedback |
| 3:40–4:20 | Arquitetura, testes, custo compartilhado planejado e privacidade na demo |
| 4:20–5:00 | Resultado demonstrado, limites e próximos passos |

## Evidências a guardar antes do pitch

- Commit da versão apresentada e comandos de execução realmente testados.
- Capturas de desktop e celular, sem dados reais, com tarefa/critério associado.
- Resultado dos testes, quantidade e o que cobrem; validação visual separada.
- Exemplo de fonte/evidência, duplicação evitada e decisão humana preservada.
- Integrações reais versus simuladas; custo medido versus estimativas/propostas.
- Qualquer funcionalidade que precise de preparação manual para funcionar na demo.

## Como atualizar este documento

A cada incremento, registrar problema, RF/CA, decisão, alteração de frontend,
alteração de backend, testes executados, roteiro de demonstração e limitações.
Atualizar status da tabela e não apagar decisões/limites ainda aplicáveis.
