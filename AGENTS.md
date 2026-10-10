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
Python 3.13 + Flask + SQLite (gerenciado com `uv`); interface em JS puro com
Tailwind compilado via Node (só ferramenta de build). Sem Django e sem Docker.

```bash
uv sync --locked                      # dependências Python
uv run --locked pytest                # testes
uv run flask --app app seed           # popula base vazia (não sobrescreve)
uv run flask --app app reset-demo     # reconstrói a demonstração
uv run flask --app app run            # http://127.0.0.1:5000
npm install && npm run css:build      # recompila o CSS (versionado) após mexer em classes
```

Nunca use `pip` ou `python` direto no host: use `uv run`.

## Estrutura
| Caminho | Papel |
| --- | --- |
| `app/rules.py` | Regras puras (vencimento, prioridade, aniversário, preferências) |
| `app/alertas.py` | Cálculo de alertas sob demanda |
| `app/resumo.py` | Resumo por template com fontes |
| `app/clock.py` | `Clock` único (America/Sao_Paulo) |
| `app/api.py`, `app/db.py`, `app/seed.py` | Rotas JSON, schema SQLite, dados fictícios |
| `app/static/js/app.js`, `app/templates/` | Interface |
| `tests/` | pytest |

## Regras que não podem ser quebradas
- **Tempo:** toda regra recebe a data do `Clock`. Nunca chame `date.today()` ou
  `datetime.now()` fora de `app/clock.py`. Testes injetam `relogio_fixo(...)`.
- **Alertas** são calculados a cada consulta; só o tratamento é persistido
  (`tratamento_alerta`). Não crie tabela ou cópia de alerta, nem cron/worker
  para esses alertas. Agendamento de notícias/reuniões é evolução separada (T08).
- **Prioridade do cliente** vem só dos alertas pendentes (RN11). O estado de
  relacionamento é manual e **não** altera prioridade.
- **Resumo da base** é por template, sem IA. Cada fato tem fonte; ausência de dado é
  mensagem de ausência, nunca conclusão sobre o cliente.
- **Dinheiro** como `Decimal`/texto, nunca `float`. Instantes em UTC no banco.
- **Dados:** apenas fictícios e identificados. Execução local em `127.0.0.1`,
  sem autenticação no MVP. Não colocar dado real, segredo ou `.env` no Git.
- **Erros:** identifique a entrada inválida (`erro.campo`); nada de fallback
  silencioso. Entrada inválida não persiste registro.
- **API/contratos:** mudou rota, campo ou erro? Atualize `contracts.md` na mesma
  mudança e avise a equipe. IDs `RF`/`CA` existentes não mudam; crie novos.

## Como trabalhar
- Menor mudança completa que resolve a causa; sem refatoração não pedida.
- Regra nova: critério de aceite no `spec.md`, teste que falha, depois código.
- Código novo: núcleo puro (regras) separado de I/O (rotas, banco).
- Uma tarefa = uma branch `tipo/descricao-em-kebab-case` (`feat/`, `fix/`,
  `docs/`, `test/`). Cada pessoa valida a própria entrega.
- Mudou classes Tailwind em JS/HTML? Rode `npm run css:build` e commite o CSS.
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
Login/permissões, envio de mensagens ou atas, integrações de canais, app nativo,
análise tributária, dispensar/silenciar alertas. NewsAPI, reuniões e keynotes são
a tarefa T08, depois do fluxo principal validado. Consumo de fontes existentes,
extração, supervisão e feedback são a evolução T09 já planejada pelo usuário;
ainda não implementada. IA para extração não altera o resumo por template da base.

## Materiais locais
`material-local/` (PDF do evento, comandos, guias) é pessoal, fica fora do Git e
pode não existir na sua máquina; a documentação em `docs/` basta.
