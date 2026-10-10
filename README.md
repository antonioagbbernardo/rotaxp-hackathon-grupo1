# Assessor do Futuro — MVP Rota XP (grupo 1)

Documentação: `docs/` (`spec.md`, `design.md`, `contracts.md`, `tasks.md`).
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
| `app/rules.py` | Regras puras (RN03, RN04, RN11, RN12) |
| `app/alertas.py` | Geração de alertas — **T04, pendente** |
| `app/api.py` | Rotas JSON `/api/...`; POST ainda devolvem 501 (T03–T05) |
| `app/db.py`, `app/seed.py` | Schema SQLite e dados fictícios com datas relativas a hoje |
| `app/templates`, `app/static/js` | Página base e JS que consome a API |
| `tests/` | pytest; relógio injetável via `config["HOJE"]` |
