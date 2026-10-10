# Assessor do Futuro — MVP Rota XP (grupo 1)

Documentação: `docs/` (índice em `docs/README.md`; planejamento em `docs/planejamento/`).
Dados do projeto são fictícios.

## Como usar

### Requisitos
- [`uv`](https://docs.astral.sh/uv/) (instala o Python 3.13 do projeto sozinho, se faltar).
- Node.js 22+ **somente** se for mexer no CSS/interface. Para rodar o app não precisa.

### Rodar o app
```bash
uv sync --locked                       # instala as dependências do lockfile
uv run flask --app app seed            # popula dados fictícios (só em base vazia)
uv run flask --app app run             # http://127.0.0.1:5000
```
Se a porta 5000 estiver ocupada (comum no macOS), use `run -p 5001`.
O app roda só em `127.0.0.1`, sem login, e **não deve receber dados reais**.

### Usar a interface
1. **Lista de clientes:** ordenada por prioridade de atendimento. Busque por nome
   ou filtre por prioridade.
2. **Detalhe do cliente** (clique no nome): resumo com a fonte de cada fato,
   alertas pendentes e tratados, posições e histórico.
3. **Marcar como tratado:** tira o alerta das pendências e recalcula a prioridade.
4. **Registrar interação:** canal, texto, e opcionalmente quando ocorreu e
   próximos passos. Datas futuras são recusadas.
5. **Avaliar relacionamento:** estado + justificativa obrigatória (não altera
   a prioridade).
6. **Preferências:** canal, intervalo mínimo entre contatos e permissão para
   assuntos pessoais (sem permissão, não há alerta de aniversário).

### Dados e testes
```bash
uv run --locked pytest                          # testes (47)
uv run flask --app app seed                     # não sobrescreve base já populada
uv run flask --app app reset-demo               # apaga tudo e recria a demonstração
```
O banco fica em `instance/app.db` (ignorado pelo Git; cada pessoa tem o seu).
Os vencimentos do seed são relativos ao dia em que você roda o comando.

### Chamar a API direto
```bash
curl -s localhost:5000/api/clientes                      # lista priorizada
curl -s localhost:5000/api/clientes/1                    # detalhe
curl -s -X POST localhost:5000/api/clientes/1/interacoes \
  -H 'content-type: application/json' \
  -d '{"canal": "telefone", "texto": "Conversa sobre o CDB"}'
```
Rotas e formatos: [`docs/planejamento/contracts.md`](docs/planejamento/contracts.md).

### Mexer na interface (Node)
```bash
npm install
npm run css:watch    # recompila ao salvar
npm run css:build    # rebuild único; faça antes de commitar
```
O CSS compilado (`app/static/css/app.css`) é versionado, então o clone roda sem Node.

### Problemas comuns
| Sintoma | Causa e solução |
| --- | --- |
| Lista vazia | Base nova: rode `flask --app app seed` |
| Datas "velhas" na demo | Seed de outro dia: rode `reset-demo` |
| Classe Tailwind sem efeito | Falta `npm run css:build` |
| `uv sync --locked` falha | `uv.lock` desatualizado: rode `uv lock` e avise a equipe |

## Estrutura

| Caminho | Papel |
| --- | --- |
| `app/clock.py` | `Clock` único (America/Sao_Paulo); injetável via `config["CLOCK"]` |
| `app/rules.py` | Regras puras: vencimento, prioridade, aniversário, preferências (RN03/04/11/12/13) |
| `app/alertas.py` | Alertas calculados sob demanda (RN14/15); só o tratamento é persistido |
| `app/resumo.py` | Resumo por template com fontes (RN08) |
| `app/api.py` | Rotas JSON `/api/...` (lista, detalhe, interações, relacionamento, preferências, tratar) |
| `app/db.py`, `app/seed.py` | Schema SQLite e dados fictícios com datas relativas |
| `app/templates`, `app/static/js` | Página base e JS que consome a API |
| `tests/` | pytest (regras, alertas, API, persistência, relógio, seed) |

Ainda planejados: consumo de fontes existentes, inferência e feedback (T09);
NewsAPI, reuniões e keynotes (T08). A base registra interações manualmente e não
importa conversas nem executa extração por IA. Ver [visão do produto](docs/visao-geral.md).
