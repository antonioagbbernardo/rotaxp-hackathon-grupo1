# XP Pulse — frontend integrado

Layout recebido da equipe, adaptado aos registros do Flask/SQLite, sem fallback
para os mocks estáticos. Notícias vêm do cache NewsAPI compartilhado pelo backend.

## Stack

React 19 · TypeScript · Tailwind CSS v4 · Vite

## Rodando

```bash
npm ci
npm run dev
```

Node.js 22.18+ ou 24+. Acesse http://127.0.0.1:5173 e mantenha o backend em
http://127.0.0.1:5001. O proxy de `vite.config.ts` encaminha `/api` sem CORS nem
chaves no navegador. Prepare o backend conforme [README da raiz](../README.md).

Para demonstração em uma origem, execute `npm run build` nesta pasta.
O Flask serve `frontend/dist/` em `/`; o diretório é ignorado pelo Git.
Mudou o frontend? Recompile para atualizar a demonstração na porta 5001.
Login em `/login`, **admin** / **admin**, com logo centralizado no tema XP Pulse.
Sem recuperação de senha. A sessão é validada antes de consultar os clientes;
**Sair** encerra o acesso. Cookie HttpOnly e CSRF ficam sob controle do backend.

## Fluxos integrados

- Clientes/IDs/ordem vêm de `GET /api/pulse`; seleção fica em `#/clientes/{id}`.
- Relacionamento vem do assessor; prioridade vem dos alertas pendentes.
- Importar JSON, registrar contato, tratar alerta, revisar contexto, bloquear
  assunto e salvar preferências usam as rotas existentes e atualizam o painel.
- Processar fontes com IA é ação explícita. Consultar a tela não chama Gemini.
- **Preparar resumo com IA** usa OpenAI pelo backend, com carregamento, erro/retry,
  fontes por trecho e cache persistente. Texto organizado em três seções;
  registros da base continuam acessíveis. Recargas não chamam o modelo.
- Perguntas básicas usam `POST /api/pulse/clientes/{id}/perguntar`, por templates
  com fontes. Rascunhos são para revisão/cópia, sem envio automático.
- Notícias: associação explícita entre interesse revisado e assunto do catálogo,
  busca com reuso do cache diário e fonte/link/publicação/coleta. Descarte com
  motivo vale só para o cliente; bloqueios/preferências/revisões ocultam resultados.
  Recargas não chamam o provedor; há estado de falha, ausência e processamento.
- Campos ausentes e notícias ainda não coletadas aparecem como ausência.
- Reuniões: criar/reagendar/cancelar, preparar/revisar keynotes com fontes,
  notas separadas e conclusão com resumo/próximos passos no histórico.
  Lista lateral abre o cliente de reuniões nas próximas 24h.
- Lembranças: confirmar data/tipo/descrição de candidato revisado, consultar
  fonte/sujeito/ocorrência e concluir/descartar/adiar com motivo.
- Leitura do painel é renovada a cada 60s. Para atualização automática de
  notícias/pautas, o processo `acompanhar-agenda` deve ficar aberto no backend.
  `src/data/clients.ts` é referência visual antiga e não é importado pela aplicação.

## Verificar

```bash
npm test
npm run lint
npm run build
```

Testes verificam precisão monetária, ausências e comunicação/erros da API.
Verificação visual e seus limites ficam no
[registro do incremento](../docs/registro-desenvolvimento.md).
Especificação: [incremento SDD 03](../docs/planejamento/incrementos/03-front-pulse.md).
Síntese: [incremento SDD 04](../docs/planejamento/incrementos/04-resumo-openai.md).
Notícias: [incremento SDD 05](../docs/planejamento/incrementos/05-noticias-newsapi.md).
Login: [incremento SDD 06](../docs/planejamento/incrementos/06-login.md).
Agenda: [incremento SDD 07](../docs/planejamento/incrementos/07-agenda-keynotes.md).
Lembranças: [incremento SDD 08](../docs/planejamento/incrementos/08-lembrancas.md).

## Estrutura

```
src/
├── components/
│   ├── layout/        # Cabeçalho da aplicação
│   └── ui/            # Primitivos e formulário de gravação
├── features/
│   ├── clients/          # Lista, busca/filtros e importação de fontes
│   ├── auth/             # Tela de login e composição visual do acesso
│   ├── client-overview/  # Resumo, carteira, contexto/revisão e registros
│   ├── news/             # Notícias NewsAPI, associação e feedback
│   ├── meetings/         # Agenda, keynotes, notas e resultado
│   ├── reminders/        # Datas confirmadas e feedback de ocorrência
│   └── assistant/        # Consultas com fontes e rascunhos
├── hooks/             # Filtros, clipboard e recurso API com atualização/erros
├── lib/               # API, erros e valores decimais exatos
├── data/              # Referência visual antiga, fora do fluxo em execução
└── types/             # Tipos de domínio
```

Os tokens de cor e tipografia ficam em `src/index.css` (`@theme`).
