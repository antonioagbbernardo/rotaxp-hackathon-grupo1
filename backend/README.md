# Assessor do Futuro — MVP Rota XP (grupo 1)

Documentação compartilhada: [índice](../docs/README.md) e [planejamento](../docs/planejamento/spec.md).
Todos os comandos deste guia devem ser executados dentro de `backend/`.
O Flask também serve a interface atual (templates, JavaScript e CSS).
Dados do projeto são fictícios.

## Como usar

### Requisitos
- [`uv`](https://docs.astral.sh/uv/) (instala o Python 3.13 do projeto sozinho, se faltar).
- Node.js 22+ **somente** se for mexer no CSS/interface. Para rodar o app não precisa.

### Rodar o app
```bash
cd backend                            # a partir da raiz do repositório
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
7. **Importar fonte fictícia:** na lista, selecione `dados/fonte-demo.json`.
   Consulte fontes e versões no detalhe; identidades não resolvidas ficam na
   lista de pendências. Importação não confirma informações do formulário.
8. **Contexto:** processe fontes novas com IA, confira os trechos e registre
   aprovação, correção, descarte ou adiamento com motivo. Bloquear assunto vale
   só para este cliente e mantém o contexto. Nenhuma decisão envia mensagem.

### Configurar IA (incremento SDD 02)

Em `backend/.env` local, ignorado pelo Git:

```dotenv
GEMINI_API_KEY=sua-chave-local
GEMINI_MODEL=gemini-3.5-flash-lite
```

Reinicie o Flask após configurar. Variáveis de ambiente prevalecem sobre `.env`.
Processamento usa apenas fontes fictícias novas do cliente. Sem novidades,
reutiliza contexto; falhas preservam revisões e mostram erro. Sem chave não há
resposta simulada automática. [Contrato/aceites](../docs/planejamento/incrementos/02-contexto-revisao.md).

### Fonte simulada (incremento SDD 01)

Dentro de `backend/`, depois do seed:

```bash
uv run flask --app app importar-fontes dados/fonte-demo.json
```

O arquivo contém 14 documentos fictícios: três formulários, nove conversas
(telefone/e-mail/WhatsApp) e duas identidades pendentes. Repetir a importação
reutiliza as mesmas versões, sem duplicar o histórico. Novas versões preservam
evidências anteriores. Há também importação pelo seletor de arquivo na interface.
Contrato e testes: [incremento 01](../docs/planejamento/incrementos/01-fontes.md).

### Dados e testes
```bash
uv run --locked pytest                          # regras, API e fontes
uv run flask --app app seed                     # não sobrescreve base já populada
uv run flask --app app reset-demo               # apaga tudo e recria a demonstração
```
O banco fica em `backend/instance/app.db`, a partir da raiz. É ignorado pelo Git; cada pessoa tem o seu.
Os vencimentos do seed são relativos ao dia em que você roda o comando.

### Chamar a API direto
```bash
curl -s localhost:5000/api/clientes                      # lista priorizada
curl -s localhost:5000/api/clientes/1                    # detalhe
curl -s -X POST localhost:5000/api/clientes/1/interacoes \
  -H 'content-type: application/json' \
  -d '{"canal": "telefone", "texto": "Conversa sobre o CDB"}'
```
Rotas e formatos: [`docs/planejamento/contracts.md`](../docs/planejamento/contracts.md).

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
| `app/fontes_rules.py`, `app/fontes.py`, `dados/` | Validação, ingestão transacional e fonte JSON fictícia |
| `app/contexto_rules.py`, `app/contexto.py`, `app/ia_gemini.py` | Evidências, cache incremental, Gemini REST e supervisão persistida |
| `app/templates`, `app/static/js` | Página base e JS que consome a API |
| `tests/` | pytest (regras, alertas, API, persistência, relógio, seed) |

Importação fictícia e contexto/revisão implementados, com 125 testes aprovados
(chamadas ao provedor/transporte simuladas).
Chamada Gemini real validada em amostra fictícia; conexão à fonte real, NewsAPI, reuniões e
keynotes seguem planejados. Ver [visão do produto](../docs/visao-geral.md)
e [registro para apresentação](../docs/registro-desenvolvimento.md).
