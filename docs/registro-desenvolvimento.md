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
| Organização | Interface atual continua servida pelo Flask | Aplicação/testes/lockfiles em `backend/`; documentos em `docs/` | Commit `7456543`, enviado para main |
| Incremento 01: fontes | Importação JSON, resultado/erro, pendências de identidade, versões e origem no detalhe/histórico | Validação pura, transação SQLite, documentos versionados e API/CLI compartilhados | Implementado: 34 testes novos + 47 anteriores = 81 aprovados; CSS e sintaxe JS verificados; visual parcial |
| Incremento 02: contexto e feedback | Processamento, fila, evidências, quatro ações e bloqueio por cliente | Gemini REST, validação literal, cache, controle de concorrência, revisão/auditoria | 44 testes novos, total 125; testes simulados + extração real de 4 fontes/7 propostas. Visual completo pendente |
| Notícias e reuniões | Notícias pertinentes e keynotes | NewsAPI compartilhada, cache, preparação de pauta | Planejado, não implementado |
| Protótipo visual React (XP Pulse) | Tela do Figma em `frontend/` (React + TypeScript + Tailwind v4): clientes com busca/filtro, resumo, percepção, carteira, notícias e assistente com sugestão de abertura | Nenhum; dados fictícios locais em `frontend/src/data` | Build e lint aprovados; conferido no navegador em 1600px e 390px. Não integrado à API Flask; respostas do assistente são estáticas |

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
- Entrega registrada em commit local na `main`, a pedido do usuário; push não
  executado. Fonte real, lembretes derivados, notícias e keynotes pendentes.

## Roteiro para a apresentação

| Tempo sugerido | Mostrar e explicar |
| --- | --- |
| 0:00–0:40 | Conversas dispersas e o que o assessor precisa saber antes do contato |
| 0:40–1:40 | Entrada de fontes e rastreabilidade; indicar dados fictícios e estágio real da entrega |
| 1:40–2:40 | Cliente, histórico, pendências e prioridade calculada |
| 2:40–3:40 | Revisão humana se implementada; caso contrário, preferências e avaliação manual da base |
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
