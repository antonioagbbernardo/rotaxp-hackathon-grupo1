# MVP — acompanhamento de investidores

Status: base funcional Flask/Tailwind integrada em 10/10/2026, com regras da
branch da equipe preservadas. A direção atual do produto inclui consumo de
fontes existentes, inferência e feedback. Importação de JSON fictício está
implementada; extração Gemini e revisão humana implementadas com testes simulados.
Extração real validada em uma amostra fictícia; notícias via NewsAPI com coleta
manual/CLI e cache implementadas no incremento 05. Incrementos 06–08 integram
login, agenda, keynotes, processo local de atualização e lembranças confirmadas.
Fonte real pendente. Verificação atual mínima a pedido do usuário; fluxo visual
completo dos novos incrementos e qualidade geral ainda não validados.
Detalhamento: [requisitos](requisitos.md) (RF01–RF31 e CA11–CA33), [contratos](contracts.md),
[arquitetura](design.md). Leitura rápida: [visão geral](../visao-geral.md).
Nas divergências sobre regras de alerta, prioridade, preferências e acesso, vale
este documento (decisões de 10/10/2026).

## Objetivo

Poupar tempo do assessor e melhorar sua relação com o investidor. O sistema
apoia o profissional: a decisão de contato e de uso das informações continua
com ele. Não pretende substituir o assessor ou automatizar o relacionamento.

Transformar formulário inicial, transcrições, e-mails e WhatsApp Business já
existentes em contexto, lembranças e pautas pertinentes. O assessor revisa
as sugestões e fornece feedback. A base atual oferece consulta, histórico,
preferências e alertas determinísticos para sustentar esse fluxo.

## Fluxos

**Base atual:** listar clientes (ordenados por prioridade) → abrir cliente → consultar resumo,
alertas e fontes → registrar interação → tratar alerta → consultar histórico
e prioridade atualizados após recarregar.

**Fluxo alvo:** consumir fontes existentes → extrair contexto com evidências →
assessor revisa e dá feedback → selecionar lembranças/notícias → preparar reunião
com keynotes → atualizar o contexto após novos registros.

## Base funcional integrada

- Lista de clientes com busca, filtro e ordenação por prioridade.
- Detalhe com perfil, preferências de contato, posições, datas importantes e
  histórico.
- Resumo factual por template, sem IA, derivado dos registros (RN08).
- Alertas de vencimento e de aniversário (`DataImportante`), calculados sob demanda.
- Registro manual de interações de WhatsApp, e-mail, telefone e presencial.
- Estado de relacionamento informado pelo assessor, com justificativa.
- Marcar alertas como tratados, com persistência.
- Importar fonte JSON fictícia: formulário e conversas versionados, histórico
  integrado, fontes consultáveis e identidades não resolvidas em pendência.
  Regras e aceites em [incremento 01](incrementos/01-fontes.md).
- Notícias: associação humana a interesse revisado, coleta NewsAPI compartilhada,
  cache diário, cota e feedback individual ([incremento 05](incrementos/05-noticias-newsapi.md)).

## Direção do produto — estágios de entrega

Esclarecido pelo usuário e preservado neste merge:

- Consumo da fonte existente e formulário, extração de fatos/hipóteses,
  revisão humana e feedback (RF03, RF05, RF16, RF25–RF30): JSON fictício e
  contexto revisável e lembranças com data confirmada implementados
  ([incremento 08](incrementos/08-lembrancas.md)).
- Notícias via NewsAPI.org por assunto compartilhado: coleta manual/CLI, cache
  e cota implementados; processo local para atualização diária e antecipação
  por reunião no [incremento 07](incrementos/07-agenda-keynotes.md) (RF17–RF20).
- Reuniões próximas com pauta (keynotes), fontes e observações revisáveis
  (RF21–RF24).

Critérios CA16–CA25 e regras de busca: [requisitos](requisitos.md) e
[integração NewsAPI](../integracoes/busca-noticias.md). O agendador serve só à
busca de notícias e às reuniões; alertas continuam calculados sob demanda (RN14).

Fora da entrega atual: conexão à fonte real. Construir captura dos canais e
formulário, envio de mensagens/atas, app nativo e análises tributárias
não fazem parte desta integração. Login local autorizado no incremento 06.

Alertas calculados da base só têm pendente/tratado (RN15). Ações de adiar ou
descartar itens inferidos pertencem à revisão de contexto do incremento 02,
sem alterar a regra de tratamento desses alertas. Lembranças derivadas têm
confirmação e feedback próprios (RN67–RN70), sem influenciar prioridade.

Demonstração com um assessor fictício único, dados fictícios identificados,
somente em ambiente local (`127.0.0.1`). **Proibido usar dados reais de
investidores.** O MVP não tem segurança adequada para publicação ou para dados
financeiros pessoais reais. Login de demonstração definido no
[incremento 06](incrementos/06-login.md); autorização e acesso multiassessor são
requisitos posteriores.

## Regras

Os valores abaixo são decisões da equipe, não regras dos organizadores. "Hoje" é
a data local no fuso `America/Sao_Paulo`, fornecida por um único `Clock`
injetável.

### Vencimentos (RN03, RN04)

Δ = data de vencimento − hoje, em dias corridos.

| Δ (dias) | Classificação | Prioridade | Rótulo |
| --- | --- | --- | --- |
| negativo | Vencido | Alta | `Vencido há N dias` |
| 0 | Vence hoje | Alta | `Vence hoje` |
| 1 a 7 | Vencimento próximo | Alta | `Vence em N dias` |
| 8 a 30 | Vencimento futuro | Média | `Vence em N dias` |
| 31 ou mais | Fora da janela | Sem alerta | — |

Dia 0 e dia 7 são inclusivos. Todo vencimento passado gera alerta de prioridade
alta, qualquer que seja N.

### Demais regras

RN01. Cada interação pertence a um único cliente existente e exige canal e texto
      não vazio.
RN02. Cada interação tem `ocorrida_em` (informada; padrão: agora) e
      `registrada_em` (automática, imutável). Ocorrência futura é recusada.
      Histórico ordenado por `ocorrida_em DESC`, `registrada_em DESC`, `id DESC`.
      Instantes persistidos em UTC; entrada sem fuso é interpretada como
      `America/Sao_Paulo`.
RN05. Eventos externos/simulados (opcional) só se relacionam a interesses
      registrados e às preferências do cliente (RN13); o mesmo evento não gera
      alertas duplicados.
RN06. Um evento pessoal não modifica o perfil financeiro nem presume o humor.
RN07. Alterar o estado de relacionamento exige justificativa, responsável e
      data. Nenhum evento, posição ou interação altera esse estado.
RN08. Na base atual, o resumo é montado por template a partir de registros persistidos (perfil,
      posições, próximos vencimentos, última interação e próximos passos). Cada
      fato carrega referência `{tipo_fonte, id_fonte, data_referencia}`. Ausência
      de registro é apresentada como ausência de informação, sem inferência:
      `Nenhuma posição cadastrada`, `Nenhuma interação registrada`,
      `Não avaliado`.
RN09. Um alerta tratado não entra na contagem de pendências.
RN10. Dados persistem entre recargas e reinicializações. O seed só inicializa
      base vazia; reexecutá-lo não sobrescreve nem desloca dados. Um comando
      explícito de reset reconstrói os dados fictícios.
RN11. A prioridade do cliente é a maior prioridade entre seus alertas pendentes;
      sem alertas, é **baixa**. Alertas tratados não influenciam. Empate de
      faixa: pendência mais próxima, depois nome. O estado de relacionamento não
      altera a prioridade.
RN12. Datas importantes (`DataImportante`, aniversário) geram alerta recorrente
      de prioridade **média** com 0 a 7 dias de antecedência, sujeito às
      preferências (RN13). A ocorrência anual é identificada pela data naquele
      ano.
RN13. Preferências estruturadas do cliente: `canal_preferido`,
      `intervalo_minimo_dias` (7, 14 ou 30; padrão 7) e
      `permite_assuntos_pessoais` (padrão `false`).
      - O canal preferido é o padrão ao registrar interação; não há envio
        automático.
      - O intervalo é contado desde a última interação realizada, em qualquer
        canal. Sem histórico, não bloqueia.
      - Alertas e sugestões pessoais só aparecem com permissão e intervalo
        respeitado.
      - Alertas financeiros não são ocultados por canal ou frequência.
RN14. Alertas são calculados sob demanda a cada consulta de lista ou detalhe,
      sem cron, worker ou botão de processamento. Identidade do alerta:
      `(cliente_id, regra, entidade_origem_id, ocorrencia)`; para vencimento,
      `ocorrencia` = data de vencimento; para aniversário, a data da ocorrência
      no ano. Somente o tratamento é persistido (chave, `tratado_em`,
      `assessor_id`, unicidade).
RN15. Estados do alerta: `pendente` e `tratado`. O tratamento é definitivo para
      aquela ocorrência. Alerta tratado fica em filtro/histórico, fora da
      contagem. Uma nova ocorrência (vencimento corrigido, aniversário do ano
      seguinte) é um novo alerta.

| Situação | Comportamento |
| --- | --- |
| Vencimento passa de 30 para 7 dias | Mesmo alerta; prioridade recalculada |
| Alerta tratado | Permanece tratado em novas consultas e reinícios |
| Página atualizada dez vezes | Nenhuma duplicação |
| Data de vencimento corrigida | Nova ocorrência; a antiga deixa de ser elegível |
| Posição deixa de ser elegível | Alerta some das pendências atuais |

### Prioridade do cliente (resumo)

| Prioridade | Origem |
| --- | --- |
| Alta | Posição vencida ou vencimento em 0–7 dias |
| Média | Vencimento em 8–30 dias ou aniversário em 0–7 dias |
| Baixa | Nenhum alerta pendente |

Na interface, sempre rótulos completos: `Relacionamento: Atenção` (avaliação
humana) e `Prioridade de atendimento: Alta` (cálculo determinístico).

### Estados de relacionamento (RN07)

| Estado | Significado |
| --- | --- |
| `positivo` | Assessor registra contexto favorável |
| `atencao` | Assessor identifica pendência ou questão a acompanhar |
| `negativo` | Assessor registra dificuldade relevante |

Estado inicial: sem avaliação (`NULL`), exibido como "Não avaliado".

## Critérios de aceite

- CA01: busca por nome e filtros retornam somente os clientes correspondentes.
- CA02: abrir um cliente mostra somente suas posições, interações e preferências.
- CA03: salvar interação válida atualiza o histórico e permanece após recarregar.
- CA04: canal inválido, texto vazio, ocorrência futura ou cliente inexistente não
  criam registros.
- CA05: com Δ = −1, 0, 7, 8, 30 e 31, verificar existência, rótulo e
  prioridade do alerta (RN03/RN04). Vencido exibe `Vencido há N dias`.
- CA06: evento/notícia associado a interesse aparece com fonte e não se repete
  no recálculo.
- CA07: sem permissão pessoal, não há alerta pessoal. Com permissão mas contato
  mais recente que o intervalo mínimo, não há sugestão pessoal. Sem histórico,
  o intervalo não bloqueia. Alertas financeiros permanecem.
- CA08: tratar um alerta reduz a contagem de pendências, persiste entre recargas
  e reinicializações e não é revertido pelo recálculo.
- CA09: alterar relacionamento sem justificativa é recusado; alertas financeiros
  não alteram o relacionamento.
- CA10: o fluxo principal funciona em viewport de celular sem rolagem horizontal
  da página.
- CA34: cliente com múltiplos alertas assume a maior prioridade, recalculada
  após tratar um alerta.
- CA35: um aniversário próximo gera apenas um alerta, respeita RN13 e não
  reaparece como pendência depois de tratado naquela ocorrência anual; no ano
  seguinte é nova ocorrência.
- CA36: reunião realizada ontem e cadastrada hoje não fica acima de conversa
  realizada hoje (RN02).
- CA37: resumo com registros ausentes usa as mensagens de RN08 e cada fato
  apresentado tem referência de fonte.
- CA38: os testes têm resultado idêntico em qualquer dia de execução (relógio
  injetado) e reexecutar o seed não altera uma base já populada.
- CA39: atualizar a lista várias vezes não duplica alertas.

## Validação

O desenvolvimento incremental começa por [fontes fictícias](incrementos/01-fontes.md):
RN16–RN23 e CA40–CA47 detalham RF03/RF04/RF16/RF25 antes da implementação.
Cada entrega registra mudanças de front/back e evidências no
[registro de desenvolvimento](../registro-desenvolvimento.md).

Segundo recorte SDD: [contexto e revisão](incrementos/02-contexto-revisao.md),
RN24–RN32 e CA48–CA56. Gemini configurável, evidências validadas e decisões
humanas persistidas; não altera o resumo por template nem os alertas da base.

Integração autorizada do frontend React recebido: [incremento 03](incrementos/03-front-pulse.md),
RN33–RN39 e CA57–CA64. Layout XP Pulse, dados persistidos e ações explícitas.

Síntese OpenAI autorizada: [incremento 04](incrementos/04-resumo-openai.md),
RN40–RN45 e CA65–CA71. Melhora a redação com fontes, cache e revisão humana;
o resumo factual RN08 e as regras determinísticas continuam independentes.

Primeiro recorte de T08: [incremento 05](incrementos/05-noticias-newsapi.md),
RN46–RN52 e CA72–CA78. Notícias por consultas compartilhadas, vínculo humano,
cache diário, cota e feedback por cliente. Agenda e keynotes são outro recorte.

Incremento 06: [login](incrementos/06-login.md), RF31, RN53–RN58 e CA79–CA84.
Login de demonstração substitui o recorte anterior sem autenticação.

Incremento 07: [agenda e keynotes](incrementos/07-agenda-keynotes.md), RF18–RF24,
RN59–RN66 e CA85–CA90. Processo local para coleta diária/antecipação, pautas com
fontes, revisão exata, notas separadas e resultado vinculado ao histórico.
Incremento 08: [lembranças](incrementos/08-lembrancas.md), RF27–RF29,
RN67–RN70 e CA91–CA94. Datas explícitas e feedback por ocorrência sob decisão humana.

CA11–CA25 (notícias, reuniões e keynotes) estão em [requisitos](requisitos.md);
CA26–CA33 de inferência/feedback continuam em requisitos; CA34–CA39 acima
validam a base implementada (IDs reconciliados durante o merge).

Primeiro lote de testes (antes das rotas): limites de vencimento, `Clock`,
identidade do alerta, persistência do tratamento e permissões pessoais. Depois,
testes de API/persistência e verificação do fluxo no navegador (desktop e
viewport de celular), a partir de um clone limpo. Informar separadamente
verificações executadas e limitações.

## Decisões pendentes

Para a evolução: contrato/acesso à fonte real, qualidade/custo da extração,
limites de relevância/orçamento e dados de demonstração. Gemini e revisão/feedback
definidos no incremento 02, com uma amostra real validada. Stack em `design.md`.

### Identificadores de aceite após o merge

CA26–CA33 em `requisitos.md` preservam ingestão/inferência/feedback publicados
na main. A branch havia usado CA26–CA31 para testes da base; foram reconciliados
como CA34–CA39 neste documento e em tarefas. Nenhum cenário foi removido.
