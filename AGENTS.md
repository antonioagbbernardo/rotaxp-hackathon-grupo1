# AGENTS.md — como atuar neste repositório

Projeto do hackathon Rota XP (grupo 1): MVP "Assessor do Futuro", um painel para
o assessor de investimentos priorizar clientes, entender o motivo (com fonte) e
registrar contatos. Idioma de código, commits e documentação: **português do Brasil**.

## Antes de mexer
1. Leia `docs/README.md` e, para regras, `docs/planejamento/spec.md`.
2. Contratos da API: `docs/planejamento/contracts.md`. Requisitos RF/CA: `docs/planejamento/requisitos.md`.
3. Em divergência de regras (alerta, prioridade, preferências, acesso), vale
   `spec.md` + `contracts.md` (decisões de 10/10/2026), não `requisitos.md`.
4. Confira o estado real (`git status`, rodar os testes) antes de afirmar algo.

## Stack e comandos
Python 3.13 + Flask + SQLite (gerenciado com `uv`). Frontend principal recebido
pela equipe: React/TypeScript/Tailwind/Vite em `frontend/`, integração autorizada
pelo usuário. Interface JS anterior em `/legacy`. Sem Django e sem Docker.

Executar os comandos dentro de `backend/` (a partir da raiz: `cd backend`).

```bash
uv sync --locked                      # dependências Python
uv run --locked pytest                # testes
uv run --locked flask --app app seed           # popula base vazia (não sobrescreve)
uv run --locked flask --app app reset-demo     # reconstrói a demonstração
uv run --locked flask --app app run -p 5001    # http://127.0.0.1:5001
uv run --locked flask --app app acompanhar-agenda  # processo separado, atualizações a cada 60s
npm install && npm run css:build      # recompila o CSS (versionado) após mexer em classes
```

No frontend: `npm ci`, `npm run build`, `npm run lint`, `npm test`, `npm run dev`.
Build `frontend/dist` local/ignorado pode ser servido pelo Flask; desenvolvimento
usa proxy `/api` para 127.0.0.1:5001. Não expor credenciais com prefixo VITE_.

Nunca use `pip` ou `python` direto no host: use `uv run`.

## Estrutura
| Caminho | Papel |
| --- | --- |
| `backend/app/rules.py` | Regras puras (vencimento, prioridade, aniversário, preferências) |
| `backend/app/alertas.py` | Cálculo de alertas sob demanda |
| `backend/app/resumo.py` | Resumo por template com fontes |
| `backend/app/clock.py` | `Clock` único (America/Sao_Paulo) |
| `backend/app/api.py`, `backend/app/db.py`, `backend/app/seed.py` | Rotas JSON, schema SQLite, dados fictícios |
| `frontend/src/` | Interface principal React e chamadas à API |
| `backend/app/pulse.py` | Adaptador de leitura XP Pulse e consultas por template |
| `backend/app/reunioes.py`, `backend/app/agendador.py` | Reuniões, pautas versionadas e processo de atualização |
| `backend/app/lembrancas.py` | Datas confirmadas com fonte e feedback por ocorrência |
| `backend/app/static/js/app.js`, `backend/app/templates/` | Interface anterior `/legacy` |
| `backend/tests/` | pytest |

## Regras que não podem ser quebradas
- **Tempo:** toda regra recebe a data do `Clock`. Nunca chame `date.today()` ou
  `datetime.now()` fora de `backend/app/clock.py`. Testes injetam `relogio_fixo(...)`.
- **Alertas** são calculados a cada consulta; só o tratamento é persistido
  (`tratamento_alerta`). Não crie tabela ou cópia de alerta, nem cron/worker
  para esses alertas. O processo do incremento 07 atualiza apenas notícias/pautas.
- **Prioridade do cliente** vem só dos alertas pendentes (RN11). O estado de
  relacionamento é manual e **não** altera prioridade.
- **Resumo da base** é por template, sem IA. Cada fato tem fonte; ausência de dado é
  mensagem de ausência, nunca conclusão sobre o cliente.
- **Dinheiro** como `Decimal`/texto, nunca `float`. Instantes em UTC no banco.
- **Dados:** apenas fictícios e identificados. Execução local em `127.0.0.1`,
  com login de demonstração autorizado no incremento 06. Não colocar dado real,
  segredo de sessão ou `.env` no Git. APIs de dados exigem sessão; escritas exigem CSRF.
- **Erros:** identifique a entrada inválida (`erro.campo`); nada de fallback
  silencioso. Entrada inválida não persiste registro.
- **API/contratos:** mudou rota, campo ou erro? Atualize `contracts.md` na mesma
  mudança e avise a equipe. IDs `RF`/`CA` existentes não mudam; crie novos.

## Como trabalhar
- Menor mudança completa que resolve a causa; sem refatoração não pedida.
- Regra nova: critério de aceite no `spec.md`, teste que falha, depois código.
- Código novo: núcleo puro (regras) separado de I/O (rotas, banco).
- SDD incremental: atualizar especificação e contrato antes dos testes/código.
  A cada entrega, registrar mudanças de frontend/backend, evidências e limites
  em `docs/registro-desenvolvimento.md`, usado para montar a apresentação.
- Uma tarefa = uma branch `tipo/descricao-em-kebab-case` (`feat/`, `fix/`,
  `docs/`, `test/`). Cada pessoa valida a própria entrega.
- Mudou a interface React? Rode build, lint e testes em `frontend/`; `dist` é
  ignorado. Mudou classes da interface anterior? Rode `npm run css:build` em
  `backend/` e versione seu CSS compilado.
- Verifique antes de dar como pronto: testes + o fluxo no navegador (inclusive
  viewport de celular, sem rolagem horizontal). Diga o que **não** foi verificado.

## Git
- Commits em português, no formato `tipo: resumo` (`feat`, `fix`, `docs`, `test`,
  `chore`), com corpo explicando o que e por quê.
- Stage por caminho explícito; revise `git diff --staged`. Nunca `git add .`
  às cegas, `--no-verify`, `push --force` ou `reset --hard` sem pedido.
- Não faça push, merge, rebase, stash ou amend por conta própria: só quando o
  usuário pedir.
- Não atribua autoria ou co-autoria de agente nos commits (decisão da equipe).
- **Congelamento do código: 10/10/2026, 17h.** O repositório é clonado às 17h30.

## Fora do escopo (não implementar sem decisão da equipe)
Permissões multiassessor, envio de mensagens ou atas, integrações de canais, app nativo,
análise tributária, dispensar/silenciar alertas. NewsAPI, reuniões e keynotes são
a tarefa T08, depois do fluxo principal validado. Consumo de fontes existentes,
extração, supervisão e feedback são a evolução T09 autorizada pelo usuário.
T09.1 importa JSON fictício e preserva evidências; T09.2/T09.3 acrescentam Gemini,
revisão, correções e bloqueio por cliente. Chamada real validada em amostra fictícia;
IA para extração não altera o resumo por template da base.
Incremento 04 autorizado: síntese OpenAI separada (RN40–RN45), gerada por POST,
com fontes validadas e cache SQLite. GET não chama provedor. O relacionamento
humano é exibido diretamente, sem reinterpretação na síntese. Chaves no `.env`.
Incremento 05 autorizado: notícias por catálogo/vínculo humano com interesse
elegível, coleta explícita/CLI, cache diário compartilhado, cota local e feedback.
GET não coleta. Notícias não alteram alertas, prioridade, humor ou síntese OpenAI.
Agendador automático e reuniões/keynotes são o incremento 07, separado desse recorte.
Incremento 06 autorizado explicitamente: login `/login`, `admin` / `admin`,
sessão com validade/revogação, CSRF e painel protegido. Sem recuperação de senha.
Incrementos 07/08 autorizados no pedido de concluir as demandas SDD: agenda,
pautas determinísticas com fontes, notas separadas, conclusão idempotente,
processo local de coleta diária/antecipação e datas pessoais confirmadas com
feedback. Janelas: reunião em até 24h, cache de notícias com idade >=2h,
lembrança em até sete dias. Sem envio automático ou avaliação de humor.
Pedido atual do usuário: verificações mínimas para acelerar; conferência visual
adicional e suíte completa adiadas. Registrar exatamente o que foi executado.

## Materiais locais
`material-local/` (PDF do evento, comandos, guias) é pessoal, fica fora do Git e
pode não existir na sua máquina; a documentação em `docs/` basta.
