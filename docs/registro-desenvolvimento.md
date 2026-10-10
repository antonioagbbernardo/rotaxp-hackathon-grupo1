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
| Notícias com custo compartilhado | Reaproveita uma consulta entre clientes e evita chamadas em recargas | Dois clientes fictícios compartilharam uma chamada real; incremento 07 antecipa coleta e monta keynotes |

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
| Incremento 05: notícias | Associação de interesse, coleta, fontes/datas, estado do cache e feedback individual | NewsAPI REST, cache diário compartilhado, cota, lease e descarte persistente | 41 testes novos; uma consulta real compartilhada por dois clientes fictícios; limites visuais abaixo |
| Incremento 07: reuniões e keynotes | Agenda, fontes, revisão, notas e resultado | Pauta versionada, conclusão única e processo local diário/antecipação | Implementado; seis casos novos, verificação visual adiada |
| Incremento 08: lembranças | Confirmação de data e feedback | Sujeito/fonte/revisão, recorrência e feedback por ocorrência/versão | Implementado; sete casos novos, sem envio automático |
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

## Incremento 05 — notícias com pertinência humana e custo compartilhado

- SDD: [especificação 05](planejamento/incrementos/05-noticias-newsapi.md)
  e contrato publicados localmente antes do código. RF17/RF20 e feedback RF29;
  RN46–RN52, CA72–CA78. Primeira execução do teste falhou com 404 (rota ausente).
  Consulta de notícias no assistente também teve teste observado falhando antes
  de substituir a mensagem antiga de ausência por leitura do cache.
- Backend: `noticias_rules.py` separa catálogo/elegibilidade/URL/validação;
  `newsapi.py` usa REST com chave em cabeçalho e sem redirecionamento; `noticias.py`
  coordena vínculo humano, tentativas, orçamento, cache e feedback. Schema aditivo
  preserva dados anteriores. Artigos por URL única, snapshots por coleta e
  vínculos/revisões anteriores guardados; reset explícito respeita dependências.
- Pertinência: o assessor associa interesse revisado a Fórmula 1, Palmeiras ou
  Corinthians. Sem inferir a consulta do texto. Revisão nova, hipótese, terceiro,
  fonte antiga/conflitante, bloqueio e preferências/intervalo impedem uso.
  Notícias são sugestões para revisar; nunca avaliação de humor, alerta ou
  recomendação financeira. Síntese OpenAI continua usando só seus fatos internos.
- Custo: uma consulta por assunto/dia após sucesso, inclusive resultado vazio.
  Primeira página de dez artigos; até três exibidos por cliente. Padrão local
  20 tentativas/dia, configurável entre 1 e 100; erros e reservas contam.
  GET não coleta. CLI `coletar-noticias` reutiliza a mesma rotina; agendador
  automático e antecipação por reunião não instalados. Sem retries automáticos.
- Falhas: timeout 15 s e saída até 1 MB, intervalo 15 min após falha, 429 bloqueia
  por 30 min e cota externa pelo dia local. Lease de dois minutos e transações
  curtas; tentativa antiga não sobrescreve a nova. Última coleta bem-sucedida
  permanece consultável com datas e estado de falha/desatualização.
- Frontend: associação explícita, botão Buscar notícias, estados de erro/espera,
  fonte/link/publicação/coleta e motivo da seleção. Feedback com motivo oculta
  URL só para o cliente escolhido, preservando interesse e resultados dos demais.
  Perguntas básicas leem o mesmo cache com fontes, sem outra chamada.
- Validação real: **uma chamada NewsAPI**, assunto Fórmula 1, em 10/10/2026 às
  14h32 local. Três artigos mostrados para Ana e Carla fictícias; a segunda
  atualização retornou `reutilizado`. Consulta sem nome/carteira/conversas.
  Fixture separada para interesse/revisão, sem chamada Gemini/OpenAI neste lote;
  banco de trabalho anterior não teve decisões humanas alteradas.
- CLI também conferida sobre o cache real: saída `reutilizado`, exit 0, total
  mantido em uma chamada. Aplicação recriada preservou cache e feedback individual.
  Servidor de trabalho reiniciado na 5001; cinco clientes e síntese OpenAI anterior
  de Bruno preservados, novas rotas disponíveis e chave NewsAPI local reconhecida.
- Navegador desktop: associação idempotente, busca reutilizada e feedback
  preenchido/salvo. Artigo descartado saiu de Ana e permaneceu para Carla;
  próxima notícia da coleta ocupou o lugar, sem outra chamada. Fonte e datas
  conferidas nos cartões. Viewport **390 × 844**, DOM medido: viewport 390 e
  `document.documentElement.scrollWidth` 390. A inspeção visual móvel dos cartões
  ficou parcial por falhas `noWindowsAvailable` do controle nativo; sem teste em
  aparelho físico. Falhas externas/retry têm cobertura de API, sem simulação
  visual de todos os estados.
- Validação automatizada: **329 testes backend** (288 anteriores + 41 notícias),
  cinco frontend, lint e build. Cache/reinício, isolamento, fonte/revisão, limite,
  dia local, concorrência/retomada, HTTP/timeout, URLs e erro sem dados parciais.
- Limites: catálogo inicial de três assuntos, sem resumo de artigo por IA,
  notícias financeiras, agrupamento semântico de eventos ou publicação automática.
  Resultados podem ser irrelevantes (a coleta real incluiu conteúdo patrocinado),
  daí a seleção final e o feedback do assessor. Orçamento local não mede outros
  sistemas usando a mesma chave. Não alegar economia de tempo/qualidade medida.

**Demo sugerida:** interesse revisado → associação → uma coleta → fonte/datas →
mesmo assunto em outro cliente sem custo adicional → feedback individual.

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
| 3:40–4:20 | Keynotes com fontes, custo compartilhado implementado e decisão humana |
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

## Incremento 06 — login XP Pulse (10/10/2026)

- Pedido explícito: `/login`, `admin` / `admin`, logo centralizado no design da
  equipe, sem recuperação de senha. Substitui a decisão anterior sem login.
- SDD: RF31, RN53–RN58, CA79–CA84 e contrato registrados antes do código.
  TDD registrou 23 falhas backend e cinco frontend esperadas antes da implementação.
- Frontend: composição escura/amarela, campos com labels, senha mascarada,
  alternância de visibilidade, envio com Enter, erro e estado de envio. Verificar
  sessão antes de consultar clientes; logout e 401 removem o painel da interface.
- Backend: cookie assinado HttpOnly/SameSite=Lax, sessão opaca de oito horas
  revogável no SQLite, chave aleatória local 0600 e CSRF em todas as escritas.
  `/` e `/legacy` redirecionam sem sessão; APIs retornam 401 antes dos serviços.
  Logout não apaga clientes; CLI continua disponível. Interface anterior envia CSRF.
- Validação: **352 backend + 11 frontend**, lint/build aprovados. Desktop com logo
  centralizado, senha mascarada e erro de credenciais observado; painel autenticado
  preserva cinco clientes e síntese OpenAI anterior. Não houve chamadas externas.
- A pedido do usuário, conferência visual adicional de logout/celular adiada para
  acelerar as demandas SDD. Logout/expiração/reinício cobertos por testes HTTP.
- Limites: acesso único local de demonstração, sem recuperação/multiassessor.
  Reuniões, keynotes e agendamento foram entregues depois no incremento 07.

**Demo:** tela de entrada → entrar → contexto do cliente → Sair. O profissional
continua decidindo como usar as fontes e abordar o investidor.

## Incrementos 07/08 — concluir agenda e lembranças (10/10/2026)

- Pedido: concluir as demandas SDD, acelerar e testar minimamente; commit/push
  na main. Especificações/contratos escritos antes do código: RN59–RN70,
  CA85–CA94; RF18–RF24 e RF27–RF29. TDD inicial: cinco falhas de agenda e seis
  de lembranças (rotas ausentes), seguidas pela implementação; mais dois casos
  cobrem cota na preparação e edição da anotação após feedback.
- Frontend: agenda geral lateral e seção por cliente; criação/reagendamento/
  cancelamento, pauta com fontes/avisos, revisão da versão exata, notas separadas
  e conclusão com resultado. Lembranças têm candidato revisado, confirmação
  explícita de data/tipo/descrição, sujeito/fontes e feedback com motivo/adiamento.
  GET do painel a cada 60s mantém leitura atualizada, sem chamar provedores.
- Backend: tabelas aditivas de reunião/pauta e lembrança/feedback. Pauta
  determinística reúne fatos, contexto factual revisado, combinados, alertas
  pendentes e até três notícias; perguntas são sugestões. Dados novos invalidam
  a versão atual; notas e versões históricas persistem. Conclusão transacional
  cria uma única interação presencial, inclusive quando o envio é repetido.
- Atualização: processo CLI `acompanhar-agenda`, enquanto aberto, faz coleta
  diária por assunto e prepara encontros das próximas 24h. Cache >=2h pode ser
  renovado uma vez e reutilizado por outras reuniões. Cota/cache/lease/intervalo
  continuam valendo. Falha externa/cota mantém pauta interna com aviso explícito.
- Lembranças: apenas fato elegível do cliente/familiar com data confirmada;
  aniversário guarda dia/mês, compromisso data exata. Mudança de fonte/revisão,
  bloqueio ou permissão retira elegibilidade. Feedback vale por ocorrência e
  versão; editar anotação não reaplica decisão anterior. Respeita a indicação
  de intervalo de contato, sem autorizar abordagem ou alterar prioridade.
- Perguntas básicas sobre reuniões/lembranças leem os mesmos dados elegíveis
  e devolvem fontes; não há chamada de IA/NewsAPI nessa consulta.
- Validação mínima: **17 testes backend direcionados aprovados**, incluindo
  13 casos novos de agenda/lembranças e quatro regressões de acesso, notícias
  e bloqueio/reset. **11 testes frontend, lint e build aprovados.** Nenhuma chamada externa
  nesse lote; provedores simulados. Última suíte completa (antes desta entrega):
  352 backend + 11 frontend. Suíte completa e visual dos novos fluxos adiados
  pelo pedido de velocidade; não alegar CA90/CA94 visualmente validados.
- Execução local: servidor 5001 reiniciado, login/sessão e novas leituras HTTP
  retornaram 200; cinco clientes e quatro caches de síntese anteriores preservados.
  Processo contínuo iniciado; primeiro ciclo sem reuniões/vínculos retornou vazio,
  sem buscar notícias ou criar decisões humanas na base de trabalho.
- Limites: fontes dos canais simuladas por JSON; acesso real ainda precisa de
  contrato/credenciais. Processo automático precisa permanecer em execução.
  Reuniões não sincronizam calendários ou enviam atas; não há app nativo,
  análise tributária/risco completo ou acesso multiassessor. Privacidade da demo
  não representa conformidade LGPD de produção. Ganho de tempo ainda não medido.

**Demo sugerida:** entrar → fonte/evidência → revisão → reunião agendada →
keynotes/fontes → revisão humana/notas → concluir → histórico; confirmar uma
data pertinente e mostrar feedback. Para mostrar notícias automáticas, manter
o processo aberto e usar um vínculo de interesse já revisado pelo assessor.
