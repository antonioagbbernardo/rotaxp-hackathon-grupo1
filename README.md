# Assessor do Futuro — MVP Rota XP (grupo 1)

A aplicação Flask, os testes e as ferramentas de CSS ficam em [backend/](backend/README.md).
O Flask serve a API e a interface atual em JavaScript/Tailwind.
A documentação da equipe fica em [docs/](docs/README.md). Dados da demo são fictícios.

## Executar

A partir da raiz:

```bash
cd backend
uv sync --locked
uv run flask --app app seed
uv run flask --app app run -p 5001
```

Acesse http://127.0.0.1:5001. O seed só popula a base vazia.

### Protótipo do front (React)

O `frontend/` é um protótipo visual separado: usa dados fictícios próprios e
**não chama a API Flask**, então não depende do backend estar rodando. Requer Node.js 22+.

```bash
cd frontend
npm install
npm run dev
```

Acesse a URL que o Vite mostrar no terminal (por padrão http://localhost:5173).
Outros comandos: `npm run build` (checagem de tipos + build) e `npm run lint`.
Detalhes em [frontend/README.md](frontend/README.md).

## Verificar

Dentro de `backend/`:

```bash
uv run --locked pytest
```

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `backend/app/` | Flask, regras, banco, templates e arquivos estáticos |
| `backend/tests/` | Testes de regras e API |
| `backend/src/` | Fonte do CSS Tailwind |
| `backend/pyproject.toml` e `uv.lock` | Dependências Python |
| `backend/package.json` e `package-lock.json` | Ferramentas para compilar CSS |
| `docs/` | Requisitos, arquitetura, contratos e planejamento |
| `frontend/` | Protótipo visual em React + TypeScript + Tailwind (dados fictícios, sem integração com a API) |

[Comandos completos e detalhes da aplicação](backend/README.md).
