# Arquitetura — plataforma de assessores

Status: arquitetura da base Flask/Tailwind integrada em 10/10/2026.
NewsAPI, fonte existente, inferência de contexto e feedback são a direção
planejada do produto; esses módulos ainda não estão implementados.

## Stack

| Camada | Escolha |
| --- | --- |
| Backend | Python 3.13 + Flask + Jinja2, gerenciado com `uv` |
| Dados | SQLite |
| Interface | Página única responsiva (Jinja serve o HTML base) com JS que consome a API JSON; Tailwind CSS compilado com Node (CLI) |
| Node.js | Somente ferramenta da interface (build de CSS/JS). Não é runtime do backend |
| Testes | pytest (regras e API); verificação manual no navegador |

Regras de uso:

- O CSS compilado é versionado, para que o clone da organização rode só com
  Python (sem `npm install`).
- Versões de Python/Node/Flask são conferidas na ferramenta instalada e fixadas
  em `pyproject.toml`/`uv.lock`, `.python-version` e `.nvmrc`; não presumir
  patches não verificados.
- Sem Django e sem Docker.

## Organização

Uma aplicação Flask simples, com núcleo de regras puro (prioridade, vencimento,
aniversário), acesso a dados em módulo separado e rotas JSON finas. Sem serviços
distribuídos. Web responsiva não é app nativo e não deve ser apresentada como tal.

## Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| Interface | Lista, filtros, detalhe, linha do tempo, registro de interação, tratar alerta (via API JSON) |
| API JSON | Validar entradas, chamar regras, devolver JSON e erros padronizados |
| Regras | Prioridade (RN11), vencimentos (RN03/04), aniversários (RN12), preferências (RN13), `Clock` injetável |
| Persistência | Assessor, clientes, posições, interações, datas importantes, avaliações de relacionamento e tratamentos de alerta |
| Preparação de reunião (planejada) | Combina contexto interno e notícias em pauta versionada; preserva notas manuais |
| Resumo | Template determinístico; cada fato com `{tipo_fonte, id_fonte, data_referencia}` (RN08); sem LLM |

## Entidades

Campos mínimos da base em `contracts.md`. Interesse/evento, reunião e versão
da pauta abaixo são entidades planejadas, ainda ausentes do schema.

| Entidade | Relações |
| --- | --- |
| Assessor | Único e fictício (seed); identifica interações, avaliações e tratamentos |
| Cliente | Tem posições, interações, datas importantes, preferências e avaliações |
| Posição | Pertence a cliente; origem dos alertas de vencimento |
| Interação | Pertence a cliente; `ocorrida_em` (informada) e `registrada_em` (automática) |
| DataImportante | Pertence a cliente; origem dos alertas de aniversário |
| Avaliação do relacionamento | Histórico: estado, justificativa, assessor, data |
| Tratamento de alerta | Única entidade persistida do alerta: chave de ocorrência, `tratado_em`, `assessor_id` |
| Interesse / Evento | Assunto compartilhado e notícia/evento com fonte; só após o fluxo principal |
| Reunião | Objetivo, início/fuso, responsável e estado; pertence a cliente; pode ter interação de conclusão |
| Versão da pauta | Conteúdo, fontes, versão dos dados e data; pertence a reunião; notas manuais em campo separado |

Restrições: vínculos válidos, `chave_ocorrencia` única em tratamento, dinheiro
em `Decimal` (TEXT/NUMERIC, nunca float), instantes em UTC. Exclusão e retenção
não fazem parte do MVP.

## Relógio

Serviço `Clock` único, com fuso `America/Sao_Paulo`. Toda regra de vencimento,
aniversário e intervalo recebe a data/hora dele; nenhuma regra chama
`date.today()`. Testes injetam data fixa (ex.: `2026-10-10`).

Seed: só popula base vazia, com vencimentos relativos à execução em −2, 0, 5, 7,
8, 30 e 31 dias. Reexecutar não sobrescreve nem desloca dados. Um comando de
reset explícito reconstrói a demonstração.

## Alertas: cálculo sob demanda

Alerta é uma **representação calculada** a partir de posições e datas
importantes a cada consulta de lista ou detalhe; não há cópia persistida, cron,
worker nem botão de processamento. Somente o tratamento é gravado.

- Identidade: `(cliente_id, regra, entidade_origem_id, ocorrencia)`.
- Vencimento: `ocorrencia` = data de vencimento; a prioridade é recalculada
  sem mudar a identidade. Vencimento corrigido = nova ocorrência.
- Aniversário: `ocorrencia` = data no ano; ano seguinte = nova ocorrência.
- Estado `tratado` vem da existência do tratamento para a chave.
- Alertas pessoais passam pelo filtro de RN13 (permissão e intervalo mínimo).

## Acesso

Sem autenticação. Um assessor fictício único; executar somente em
`127.0.0.1`; sem dados reais. Não há `403` no contrato. Não publicar nem tratar
dados financeiros pessoais reais com esta versão.

## Notícias e reuniões — planejadas

Fonte escolhida: **NewsAPI.org**. Coleta diária por assuntos compartilhados e
atualização antecipada quando houver reunião próxima, reutilizando cache. Filtrar
por interesse, preferência (RN13), atualidade e duplicidade antes de qualquer IA
(opcional, com entradas e orçamento limitados). Plano, horários, orçamento e
parâmetros: [busca de notícias](../integracoes/busca-noticias.md).

O agendador e o coletor são rotinas de backend **apenas para notícias e
reuniões**; o cálculo de alertas continua sob demanda. O agendador prepara
reuniões na janela definida. Alterações internas podem renovar a pauta sem nova
busca externa; mudanças de data ou estado reconciliam disparos. Reunião concluída
preserva a pauta usada e a interação resultante.

## Evolução planejada: contexto e supervisão

A fonte de formulário/transcrições/e-mails/WhatsApp Business já existe por premissa.
Um adaptador futuro deve preservar identidade, origem e versão. O processador
propõe fatos e hipóteses com evidências; o assessor aprova, corrige ou descarta
e fornece feedback com alcance explícito por item, assunto ou cliente.

Entidades propostas: documento de origem, formulário versionado, item de contexto,
lembrança/sugestão e feedback. Persistência desses itens não significa persistir
cópias dos alertas de vencimento/aniversário da base. Correções humanas são
preservadas; nova evidência conflitante gera revisão.

O template atual permanece como resumo da base; extração/inferência planejada
acrescenta contexto revisável sem transformar hipóteses em fatos confirmados.
Detalhes: [contexto e feedback](../integracoes/contexto-investidor.md).

## Questões abertas para a evolução

- Fonte real das posições (Open Finance etc.) e análises de risco/tributárias.
- Autenticação, autorização e acesso multiassessor, gestor/investidor.
- Contrato e acesso à fonte existente, modelo/provedor de extração e custo.
- Armazenamento, correção, exclusão e retenção de dados pessoais.
