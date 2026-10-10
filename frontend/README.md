# XP Pulse

Painel de relacionamento do assessor: carteira de clientes, impacto de notícias e assistente com sugestões de abordagem.

## Stack

React 19 · TypeScript · Tailwind CSS v4 · Vite

## Rodando

```bash
npm install
npm run dev
```

## Estrutura

```
src/
├── components/
│   ├── layout/        # Cabeçalho da aplicação
│   └── ui/            # Primitivos reutilizáveis (Badge, Button, Panel, Avatar…)
├── features/
│   ├── clients/          # Lista, busca e filtros de clientes
│   ├── client-overview/  # Resumo, histórico de percepção e carteira
│   ├── news/             # Notícias com impacto personalizado
│   └── assistant/        # Assistente do assessor
├── hooks/             # useClientFilters, useClipboard
├── lib/               # Formatação e helpers
├── data/              # Dados fictícios
└── types/             # Tipos de domínio
```

Os tokens de cor e tipografia ficam em `src/index.css` (`@theme`).
