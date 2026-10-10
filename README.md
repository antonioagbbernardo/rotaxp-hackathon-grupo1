# XP Pulse — MVP Rota XP (grupo 1)

Painel para poupar a busca do assessor e preparar o relacionamento com o investidor.
React/TypeScript/Tailwind em [frontend/](frontend/README.md), API Flask e SQLite em
[backend/](backend/README.md), especificações e registro do pitch em [docs/](docs/README.md).
Dados fictícios; execução local sem autenticação.

## Executar a demonstração

Requisitos: `uv` e Node.js 22.18+ (ou 24+).
A partir da raiz, compile o frontend:

```bash
cd frontend
npm ci
npm run build
cd ../backend
uv sync --locked
uv run flask --app app seed
uv run flask --app app importar-fontes dados/fonte-demo.json
uv run flask --app app run -p 5001
```

Acesse http://127.0.0.1:5001. O seed só popula base vazia; repetir a importação
não duplica as versões. O build é local/ignorado: precisa ser gerado após o clone.
Sem build, `/` mostra a interface anterior, também disponível em `/legacy`.

Para desenvolvimento, mantenha o Flask na porta 5001 e, em outro terminal:

```bash
cd frontend
npm run dev
```

Acesse http://127.0.0.1:5173. O Vite encaminha `/api` ao Flask.
Credenciais OpenAI/Gemini ficam somente em `backend/.env` (modelo em
`backend/.env.example`). Extração Gemini é explícita na tela de contexto;
o botão **Preparar resumo com IA** usa OpenAI. Sem chave, os registros continuam
consultáveis. Reinicie o Flask após configurar ou alterar o `.env`.

### Frontend React em desenvolvimento

O `frontend/` consulta os dados fictícios persistidos na API Flask. Mantenha
o backend em `127.0.0.1:5001`; o proxy do Vite encaminha as chamadas `/api`.
Requer Node.js 22.18+ ou 24+.

```bash
cd frontend
npm ci
npm run dev
```

Acesse a URL que o Vite mostrar no terminal (por padrão http://127.0.0.1:5173).
Outros comandos: `npm run build` (checagem de tipos + build) e `npm run lint`.
Detalhes em [frontend/README.md](frontend/README.md).

## Verificar

```bash
cd backend
uv run --locked pytest
cd ../frontend
npm test
npm run lint
npm run build
```

O painel integra lista/prioridade, posições, histórico, fontes, revisão,
bloqueios, preferências, relacionamento e alertas. Perguntas básicas e rascunhos
usam templates com fontes. Gemini extrai contexto revisável; OpenAI redige
uma síntese com fontes em três seções, reutilizada enquanto os fatos estiverem
iguais. Relacionamento humano e prioridade calculada aparecem separados. NewsAPI e keynotes
continuam planejados, sem notícias estáticas apresentadas como coleta real.

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `frontend/src/` | Interface XP Pulse e chamadas à API |
| `backend/app/` | Flask, regras, ingestão, contexto e adaptador do painel |
| `backend/tests/`, `frontend/tests/` | Testes de comportamento e integração |
| `backend/app/templates/`, `backend/app/static/` | Interface anterior `/legacy` |
| `backend/pyproject.toml` e `uv.lock` | Dependências Python |
| `backend/package.json` e `package-lock.json` | Ferramentas para compilar CSS |
| `docs/` | Requisitos, arquitetura, contratos e planejamento |

[Comandos completos e detalhes da aplicação](backend/README.md).
