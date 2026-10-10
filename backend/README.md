# Assessor do Futuro — MVP Rota XP (grupo 1)

Documentação compartilhada: [índice](../docs/README.md) e [planejamento](../docs/planejamento/spec.md).
Todos os comandos deste guia devem ser executados dentro de `backend/`.
O Flask serve a API e o build React de `../frontend/dist` quando disponível.
A interface anterior (templates/JavaScript) fica em `/legacy`.
Dados do projeto são fictícios.

## Como usar

### Requisitos
- [`uv`](https://docs.astral.sh/uv/) (instala o Python 3.13 do projeto sozinho, se faltar).
- Node.js 22.18+ ou 24+ para compilar o React em `frontend/`.
  Backend e interface anterior podem rodar sem Node.

### Rodar o app
```bash
cd backend                            # a partir da raiz do repositório
uv sync --locked                       # instala as dependências do lockfile
uv run flask --app app seed            # popula dados fictícios (só em base vazia)
uv run flask --app app run             # http://127.0.0.1:5000
```
Para o frontend integrado, use `run -p 5001`, porta do proxy Vite.
Compile o React antes conforme [README da raiz](../README.md).
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
   Consulte fontes e versões no detalhe; identidades não resolvidas ficam em
   pendências (contador no React; lista em `/legacy` ou `/api/fontes/pendencias`).
   Importação não confirma informações do formulário.
8. **Contexto:** processe fontes novas com IA, confira os trechos e registre
   aprovação, correção, descarte ou adiamento com motivo. Bloquear assunto vale
   só para este cliente e mantém o contexto. Nenhuma decisão envia mensagem.
9. **Assistente:** consultas básicas por templates com fontes dos registros.
   Rascunhos podem ser copiados e revisados pelo assessor. Notícias não coletadas
   permanecem vazias. **Preparar resumo com IA** gera uma síntese OpenAI em
   Visão geral, Pontos de atenção e Antes do contato, com fontes por trecho.
   Relacionamento vem da avaliação humana; nenhum contato é enviado.

### Configurar síntese OpenAI (incremento SDD 04)

Copie `.env.example` para `.env` se ainda não existir; preserve as chaves
existentes. Preencha localmente:

```dotenv
OPENAI_API_KEY=sua-chave-local
OPENAI_MODEL=gpt-4.1-mini
```

Reinicie o Flask. A chave nunca vai ao frontend. GET/recargas não chamam o
modelo; o botão usa POST e cache SQLite por dados, dia, modelo e prompt. Depois
de alterar registros relevantes, gere outra síntese. Falhas mantêm os fatos e
permitem retry. Apenas dados fictícios; o assessor deve conferir texto e fontes.
Extração continua no Gemini; perguntas básicas continuam por templates.
[Contrato/aceites](../docs/planejamento/incrementos/04-resumo-openai.md).

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

### Mexer na interface principal (React)

Em `../frontend/`: `npm ci`, `npm run dev`, `npm test`, `npm run lint` e
`npm run build`. Vite na porta 5173 usa o backend na 5001; Flask na 5001
serve o build recompilado. Guia: [frontend](../frontend/README.md).

### Mexer na interface anterior (Node)
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
| `/` mostra interface anterior | Compile o React com `npm run build` em `frontend/` |
| React na 5173 não carrega dados | Flask deve estar rodando na porta 5001 |
| `uv sync --locked` falha | `uv.lock` desatualizado: rode `uv lock` e avise a equipe |

## Estrutura

| Caminho | Papel |
| --- | --- |
| `app/clock.py` | `Clock` único (America/Sao_Paulo); injetável via `config["CLOCK"]` |
| `app/rules.py` | Regras puras: vencimento, prioridade, aniversário, preferências (RN03/04/11/12/13) |
| `app/alertas.py` | Alertas calculados sob demanda (RN14/15); só o tratamento é persistido |
| `app/resumo.py` | Resumo por template com fontes (RN08) |
| `app/api.py` | Rotas JSON `/api/...` (lista, detalhe, interações, relacionamento, preferências, tratar) |
| `app/pulse.py` | Adaptador do painel React e perguntas básicas com fontes |
| `app/resumo_ia_rules.py`, `app/resumo_ia.py`, `app/ia_openai.py` | Seleção de fatos, validação, cache e síntese OpenAI por REST |
| `app/db.py`, `app/seed.py` | Schema SQLite e dados fictícios com datas relativas |
| `app/fontes_rules.py`, `app/fontes.py`, `dados/` | Validação, ingestão transacional e fonte JSON fictícia |
| `app/contexto_rules.py`, `app/contexto.py`, `app/ia_gemini.py` | Evidências, cache incremental, Gemini REST e supervisão persistida |
| `app/templates`, `app/static/js` | Interface anterior `/legacy` |
| `tests/` | pytest (regras, alertas, API, persistência, relógio, seed) |

Importação fictícia, contexto/revisão, painel React e síntese OpenAI integrados, com 288 testes aprovados
(chamadas ao provedor/transporte simuladas).
Chamadas Gemini e OpenAI reais validadas em amostras fictícias; conexão à fonte real, NewsAPI, reuniões e
keynotes seguem planejados. Ver [visão do produto](../docs/visao-geral.md)
e [registro para apresentação](../docs/registro-desenvolvimento.md).
