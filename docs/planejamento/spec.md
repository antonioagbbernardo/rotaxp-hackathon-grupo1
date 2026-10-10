# MVP — acompanhamento de investidores

Status: base funcional Flask/Tailwind integrada em 10/10/2026, com regras da
branch da equipe preservadas. A direção atual do produto inclui consumo de
fontes existentes, inferência e feedback; essa evolução ainda não está implementada.
Detalhamento: [requisitos](requisitos.md) (RF01–RF30 e CA11–CA33), [contratos](contracts.md),
[arquitetura](design.md). Leitura rápida: [visão geral](../visao-geral.md).
Nas divergências sobre regras de alerta, prioridade, preferências e acesso, vale
este documento (decisões de 10/10/2026).

## Objetivo

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

## Direção do produto — implementação pendente

Esclarecido pelo usuário e preservado neste merge:

- Consumo da fonte existente e formulário, extração de fatos/hipóteses,
  revisão humana, lembranças e feedback (RF03, RF05, RF16, RF25–RF30).
- Notícias via NewsAPI.org por assunto compartilhado, com cache e atualização
  diária (RF17–RF20).
- Reuniões próximas com pauta (keynotes), fontes e observações revisáveis
  (RF21–RF24).

Critérios CA16–CA25 e regras de busca: [requisitos](requisitos.md) e
[integração NewsAPI](../integracoes/busca-noticias.md). O agendador serve só à
busca de notícias e às reuniões; alertas continuam calculados sob demanda (RN14).

Fora da base atual: importação, inferência, revisão de sugestões, notícias e
reuniões. Estes itens continuam planejados em requisitos. Construir captura
dos canais e formulário, envio de mensagens/atas, app nativo, análises tributárias
e autenticação não fazem parte desta integração.

Alertas calculados da base só têm pendente/tratado (RN15). Ações de adiar ou
descartar sugestões inferidas pertencem ao fluxo futuro de revisão, não alteram
a regra de tratamento desses alertas.

Demonstração com um assessor fictício único, dados fictícios identificados,
somente em ambiente local (`127.0.0.1`). **Proibido usar dados reais de
investidores.** O MVP não tem segurança adequada para publicação ou para dados
financeiros pessoais reais; autenticação, autorização e acesso multiassessor são
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

CA11–CA25 (notícias, reuniões e keynotes) estão em [requisitos](requisitos.md);
CA26–CA33 de inferência/feedback continuam em requisitos; CA34–CA39 acima
validam a base implementada (IDs reconciliados durante o merge).

Primeiro lote de testes (antes das rotas): limites de vencimento, `Clock`,
identidade do alerta, persistência do tratamento e permissões pessoais. Depois,
testes de API/persistência e verificação do fluxo no navegador (desktop e
viewport de celular), a partir de um clone limpo. Informar separadamente
verificações executadas e limitações.

## Decisões pendentes

Para a evolução: contrato e acesso à fonte existente, modelo/provedor de
extração, limites de relevância e orçamento, contrato de revisão/feedback
e dados de demonstração. Stack da base já definida em `design.md`.

### Identificadores de aceite após o merge

CA26–CA33 em `requisitos.md` preservam ingestão/inferência/feedback publicados
na main. A branch havia usado CA26–CA31 para testes da base; foram reconciliados
como CA34–CA39 neste documento e em tarefas. Nenhum cenário foi removido.
