# Arquitetura — plataforma de assessores

Status: painel React XP Pulse integrado ao Flask/SQLite em 10/10/2026.
Importação de fonte JSON fictícia é o primeiro incremento SDD implementado.
Extração Gemini e revisão persistida são o incremento 02; chamada real validada
com amostra fictícia. Síntese OpenAI, NewsAPI, login, agenda/keynotes e lembranças
confirmadas implementados. Conexão aos canais reais permanece pendente.

## Stack

| Camada | Escolha |
| --- | --- |
| Backend | Python 3.13 + Flask + Jinja2, gerenciado com `uv` |
| Dados | SQLite |
| Interface | React/TypeScript/Tailwind/Vite em `frontend/`; dados da API JSON, interface anterior em `/legacy` |
| Node.js | Somente ferramenta da interface (build de CSS/JS). Não é runtime do backend |
| Testes | pytest (regras e API), Node (formatação/transporte); build/lint e verificação no navegador |

Regras de uso:

- O React precisa de `npm ci`/`npm run build` após o clone. `frontend/dist` é
  ignorado; Flask serve os assets na mesma origem. Vite em desenvolvimento usa
  proxy `/api` para a porta 5001. CSS da interface anterior é versionado.
- Versões de Python/Node/Flask são conferidas na ferramenta instalada e fixadas
  em `backend/pyproject.toml`/`backend/uv.lock`, `backend/.python-version` e `backend/.nvmrc`; não presumir
  patches não verificados.
- Sem Django e sem Docker.

## Organização

Backend em `backend/`; frontend principal em `frontend/`; documentação em `docs/`.
Executar `uv` no backend e `npm` no frontend. O Node do backend recompila somente
o CSS da interface anterior. Guia: [execução](../../README.md).

Uma aplicação Flask simples, com núcleo de regras puro (prioridade, vencimento,
aniversário), acesso a dados em módulo separado e rotas JSON finas. Sem serviços
distribuídos. Web responsiva não é app nativo e não deve ser apresentada como tal.

## Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| Interface | Lista, filtros, detalhe, linha do tempo, registro de interação, tratar alerta (via API JSON) |
| API JSON | Validar entradas, chamar regras, devolver JSON e erros padronizados |
| Adaptador XP Pulse | `pulse.py`: formato de leitura do painel, IDs preservados, Decimal/texto, ausências explícitas e consultas por template; reutiliza regras existentes, sem IA na leitura |
| Regras | Prioridade (RN11), vencimentos (RN03/04), aniversários (RN12), preferências (RN13), `Clock` injetável |
| Persistência | Assessor, clientes, posições, interações, datas importantes, avaliações de relacionamento e tratamentos de alerta |
| Ingestão de fontes | `fontes_rules.py` valida sem I/O; `fontes.py` importa JSON em transação; API/CLI usam o mesmo serviço |
| Contexto | `contexto_rules.py` valida saída/evidência e revisão; `contexto.py` persiste processamento incremental, correções e bloqueios |
| Provedor de IA | `ia_gemini.py`, REST HTTPS, chave no backend, timeout 30 s, sem ferramentas ou fallback simulado |
| Preparação de reunião | `reunioes.py`: fatos/contexto revisado/notícias em pauta versionada, notas separadas e conclusão idempotente |
| Atualização local | `agendador.py`: processo CLI para coleta diária e preparação na janela de 24h, sem alterar alertas |
| Lembranças | `lembrancas.py`: data confirmada do item/revisão, sujeito, recorrência e feedback por ocorrência/versão |
| Resumo | Template determinístico; cada fato com `{tipo_fonte, id_fonte, data_referencia}` (RN08); sem LLM |

## Entidades

Campos mínimos em `contracts.md`. Interesse/vínculo, notícias, reunião/pauta,
lembrança e feedback já estão no schema aditivo; evento semântico é evolução.

| Entidade | Relações |
| --- | --- |
| Assessor | Único e fictício (seed); identifica interações, avaliações e tratamentos |
| Cliente | Tem posições, interações, datas importantes, preferências e avaliações |
| Posição | Pertence a cliente; origem dos alertas de vencimento |
| Interação | Pertence a cliente; `ocorrida_em` (informada) e `registrada_em` (automática) |
| DataImportante | Pertence a cliente; origem dos alertas de aniversário |
| Avaliação do relacionamento | Histórico: estado, justificativa, assessor, data |
| Tratamento de alerta | Única entidade persistida do alerta: chave de ocorrência, `tratado_em`, `assessor_id` |
| DocumentoFonte | Evidência imutável por origem/registro/versão; vínculo resolvido ou pendência, conteúdo original e referência à interação |
| ProcessamentoContexto / ItemContexto | Cache por fontes/modelo/prompt; proposta pendente com sujeito e evidência, sem alterar cadastro da base |
| RevisãoContexto / PreferênciaAssunto / HistóricoAssunto | Decisão, motivo, assessor e data; bloqueio individual sem apagar contexto |
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

## Notícias e reuniões — incrementos 05/07

Fonte escolhida: **NewsAPI.org**. Coleta diária por assuntos compartilhados e
atualização antecipada quando houver reunião próxima, reutilizando cache. Filtrar
por interesse, preferência (RN13), atualidade e duplicidade antes de qualquer IA
(opcional, com entradas e orçamento limitados). Plano, horários, orçamento e
parâmetros: [busca de notícias](../integracoes/busca-noticias.md).

O agendador e o coletor são rotinas de backend **apenas para notícias e
reuniões**; o cálculo de alertas continua sob demanda. O agendador prepara
reuniões na janela definida. Alterações internas podem renovar a pauta sem nova
busca externa; mudanças de data ou estado reconciliam disparos. Reunião concluída
preserva versões no banco e a interação resultante. Conteúdo inelegível não é
reexibido como pauta atual; notas permanecem separadas. As assinaturas incluem
dados, versões/revisões, objetivo, início e dia do Clock.
O comando `acompanhar-agenda` precisa ficar aberto (60s); `--uma-vez` roda um ciclo.
Não há cron na requisição web ou geração de pauta em GET. Notícias com cache
>=2h podem ser antecipadas em reuniões das próximas 24h, sob cota/cache/lease.

## Contexto e supervisão — incremento 02

A fonte de formulário/transcrições/e-mails/WhatsApp Business já existe por premissa.
O primeiro adaptador JSON já preserva identidade, origem e versão; não conecta
provedores reais. O processador implementado
propõe fatos e hipóteses com evidências; o assessor aprova, corrige ou descarta
e fornece feedback com alcance explícito por item, assunto ou cliente.

Documento de origem e formulário versionado já usam `documento_fonte`.
Itens, revisões e bloqueios já persistem; lembranças derivadas implementadas no
incremento 08 exigem data confirmada, fonte/revisão atual e sujeito elegível.
Persistência desses itens não significa persistir
cópias dos alertas de vencimento/aniversário da base. Correções humanas são
preservadas; nova evidência conflitante gera revisão.

O template atual permanece como resumo da base; extração/inferência
acrescenta contexto revisável sem transformar hipóteses em fatos confirmados.
Detalhes: [contexto e feedback](../integracoes/contexto-investidor.md).

## Questões abertas para a evolução

- Fonte real das posições (Open Finance etc.) e análises de risco/tributárias.
- Autenticação, autorização e acesso multiassessor, gestor/investidor.
- Contrato/acesso à fonte existente e custo/qualidade real do Gemini configurado.
- Armazenamento, correção, exclusão e retenção de dados pessoais.
