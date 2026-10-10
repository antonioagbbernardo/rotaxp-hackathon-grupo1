# Assessor do Futuro — MVP Rota XP (grupo 1)

Documentação: `docs/` (índice em `docs/README.md`; planejamento em `docs/planejamento/`).
Dados do projeto são fictícios.

## Executar (só Python)

```bash
uv sync --locked
uv run flask --app app seed        # cria/recria o banco com dados fictícios
uv run flask --app app run         # http://127.0.0.1:5000
uv run pytest
```

O CSS compilado (`app/static/css/app.css`) é versionado: o clone roda sem Node.

## Desenvolver a interface (Node)

```bash
npm install
npm run css:watch    # ou: npm run css:build  (rebuild antes de commitar)
```

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

Comandos de dados: `flask --app app seed` só popula base vazia;
`flask --app app reset-demo` reconstrói a demonstração.

Fora desta etapa: NewsAPI, reuniões e keynotes (T08).
