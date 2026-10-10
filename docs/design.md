# Arquitetura — plataforma de assessores

Status: decisões de 10/10/2026. Integrações externas e IA fora do MVP.

## Stack

| Camada | Escolha |
| --- | --- |
| Backend | Python 3.13 + Flask + Jinja2, gerenciado com `uv` |
| Dados | SQLite |
| Interface | Página única responsiva (Jinja serve o HTML base) com JS que consome a API JSON; Tailwind CSS compilado com Node (CLI) |
| Node.js | Somente ferramenta da interface (build de CSS/JS). Não é runtime do backend |
| Testes | pytest (regras e API); verificação manual no navegador |

Regras de uso:

- O CSS compilado é versionado, para que o clone da organização rode só com
  Python (sem `npm install`).
- Versões de Python/Node/Flask são conferidas na ferramenta instalada e fixadas
  em `pyproject.toml`/`uv.lock`, `.python-version` e `.nvmrc`; não presumir
  patches não verificados.
- Sem Django e sem Docker.

## Organização

Uma aplicação Flask simples, com núcleo de regras puro (prioridade, vencimento,
aniversário), acesso a dados em módulo separado e rotas JSON finas. Sem serviços
distribuídos. Web responsiva não é app nativo e não deve ser apresentada como tal.

## Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| Interface | Lista, filtros, detalhe, linha do tempo, registro de interação, tratar alerta (via API JSON) |
| API JSON | Validar entradas, chamar regras, devolver JSON e erros padronizados |
| Regras | Prioridade (RN11), vencimentos (RN03/04), aniversários (RN12), relógio injetável |
| Persistência | Clientes, posições, interações, datas importantes, alertas, decisões |
| Resumo | Organiza fatos registrados com fonte e atualidade (template, sem IA) |

## Entidades

Campos mínimos em `contracts.md`.

| Entidade | Relações |
| --- | --- |
| Assessor | Único no MVP; sem autenticação |
| Cliente | Tem posições, interações, datas importantes, interesses e alertas |
| Posição | Pertence a cliente; origem dos alertas de vencimento |
| Interação | Pertence a cliente |
| DataImportante | Pertence a cliente; origem dos alertas de aniversário; separada de Interesse e Evento |
| Interesse / Interesse do cliente | Assunto e evidência; usado só pelo opcional de eventos |
| Evento (opcional) | Fonte e identificador externo; pode gerar alertas |
| Alerta | Pertence a cliente; aponta para posição, data importante ou evento; `chave_ocorrencia` única |
| Avaliação do relacionamento | Estado, justificativa, autor, data |

Restrições: vínculos válidos, `chave_ocorrencia` única por alerta, dinheiro em
`Decimal` (inteiro de centavos ou NUMERIC como texto no SQLite, nunca float).
Exclusão e retenção não fazem parte do MVP.

## Alertas: geração

Geração idempotente, executada na carga/abertura da lista e após mudanças
relevantes (não é job agendado). Reprocessar não recria alerta existente,
inclusive tratado, pela `chave_ocorrencia`:

- Vencimento: `venc:{posicao_id}`; a prioridade é recalculada pela distância a
  "hoje", mantendo o mesmo alerta.
- Aniversário: `aniv:{data_importante_id}:{ano}`.

## Eventos externos (opcional)

Se o fluxo principal estiver validado: eventos simulados e identificados,
consultados uma vez por assunto e reutilizados entre clientes. Fonte real,
frequência, limites e orçamento não aprovados.

## Questões abertas

- Fonte real das posições (Open Finance etc.) e análises de risco/tributárias.
- Autenticação e autorização por cliente, gestor/investidor.
- Uso de IA, dados enviados e custo.
- Armazenamento, correção, exclusão e retenção de dados pessoais.
