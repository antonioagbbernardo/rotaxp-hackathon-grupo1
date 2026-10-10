# Documentação da equipe

**Situação atual:** painel React/TypeScript/Tailwind integrado ao Flask/SQLite: clientes, detalhe, interações
manuais, preferências, relacionamento e alertas de vencimento/aniversário.
Incremento SDD 01 implementa importação de fontes JSON fictícias com versões
e pendências de identidade. Incremento 02 acrescenta extração Gemini e revisão
persistida; extração Gemini real de quatro fontes fictícias com sete propostas
pendentes na base da demonstração. Incremento 03 adapta o layout XP Pulse à API;
Incremento 04 acrescenta síntese OpenAI com fontes/cache, separada dos fatos.
Incremento 05 integra NewsAPI com associação humana, cache diário compartilhado,
cota e feedback de relevância por cliente. Coleta real compartilhada demonstrada.
Incremento 06 acrescenta login local, sessão/CSRF, painel protegido e logout.
Incremento 07 integra agenda, pautas versionadas, notas, conclusão e processo
local de atualização diária/antecipação. Incremento 08 integra datas confirmadas,
lembranças com fontes e feedback por ocorrência.
Última suíte completa: 352 backend e 11 frontend, antes dos incrementos 07/08.
Entrega atual: 17 casos backend direcionados, 11 frontend, build e lint; detalhes no registro.
Conferência visual adicional e suíte completa adiadas a pedido do usuário.
Conexão real aos canais continua pendente; o processo automático deve ficar aberto.
**Última revisão:** 10/10/2026. Núcleo: consumir fontes existentes, inferir contexto
e sugerir lembranças sob supervisão humana, incorporando feedback.

## Comece por aqui

| Documento | Para que serve |
| --- | --- |
| [Visão geral](visao-geral.md) | Entender rapidamente o produto, frontend, backend e fluxo de reunião |
| [Registro para apresentação](registro-desenvolvimento.md) | Entregas de front/back, evidências, decisões, limitações e roteiro do pitch |
| [Incremento SDD 01](planejamento/incrementos/01-fontes.md) | Contrato, regras e aceites da entrada de fontes fictícias |
| [Incremento SDD 02](planejamento/incrementos/02-contexto-revisao.md) | Extração por IA, evidências, revisão e bloqueio por cliente |
| [Incremento SDD 03](planejamento/incrementos/03-front-pulse.md) | Integração React, dados reais da base, perguntas e execução |
| [Incremento SDD 04](planejamento/incrementos/04-resumo-openai.md) | Síntese OpenAI em três seções, fontes, cache e limites |
| [Incremento SDD 05](planejamento/incrementos/05-noticias-newsapi.md) | NewsAPI, associação de interesses, custo compartilhado e feedback |
| [Incremento SDD 06](planejamento/incrementos/06-login.md) | Login no design XP Pulse, proteção de sessão/CSRF e logout |
| [Incremento SDD 07](planejamento/incrementos/07-agenda-keynotes.md) | Agenda, pautas versionadas, notas, conclusão e atualização automática |
| [Incremento SDD 08](planejamento/incrementos/08-lembrancas.md) | Confirmação de datas pessoais, fontes e feedback por ocorrência |
| [Incremento SDD 10](planejamento/incrementos/10-google-agenda.md) | OAuth e sincronização unidirecional de reuniões com Google Agenda |
| [Incremento SDD 10](planejamento/incrementos/10-perfil-assessor.md) | Perfil do assessor, edição e persistência dos dados profissionais |
| [Requisitos](planejamento/requisitos.md) | Consultar comportamentos, critérios de aceite e como implementar por etapa |
| [Especificação curta](planejamento/spec.md) | Alinhar o fluxo principal e regras básicas |
| [Contratos](planejamento/contracts.md) | Entidades, rotas `/api`, formato JSON e erros do MVP |
| [Arquitetura](planejamento/design.md) | Consultar responsabilidades, dados e decisões técnicas |
| [Tarefas](planejamento/tasks.md) | Dividir responsabilidades, integração e tempo |
| [Dados fictícios e testes](planejamento/plano-dados-ficticios.md) | Planejar uma fonte simulada e resultados esperados para validar o fluxo |
| [Contexto e feedback](integracoes/contexto-investidor.md) | Fonte existente, inferências, lembranças e revisão humana |
| [Busca de notícias](integracoes/busca-noticias.md) | Entender NewsAPI, atualização diária, cache, custos e reuniões |
| [Google Agenda](integracoes/google-agenda.md) | Configurar OAuth local e sincronizar reuniões |

## Organização local

API/testes Python estão em [backend/](../backend/README.md); painel/build em
[frontend/](../frontend/README.md). Execute `uv` no backend e `npm` no frontend
(CSS da interface anterior permanece no backend).

```text
backend/                      Aplicação Flask, testes e ferramentas de CSS
frontend/                     Painel React, testes e build Vite
docs/                         Documentação da equipe, destinada ao GitHub
  README.md                   Índice
  visao-geral.md               Explicação rápida e diagramas
  planejamento/               Requisitos, spec, arquitetura e tarefas
  integracoes/                Busca de notícias e futuras integrações
material-local/               Materiais pessoais, ignorados pelo Git
  preparacao/                 Comandos e guias de preparação
  referencias/                PDF do evento e ideia inicial
```

Os materiais pessoais são preservados neste computador e excluídos por
`.git/info/exclude`. A documentação da equipe deve ser compreensível sem eles.

## Como manter atualizado

1. Registrar mudança de comportamento em `planejamento/requisitos.md`.
2. Atualizar a visão geral quando mudar o fluxo ou o escopo.
3. Ajustar arquitetura, integração e tarefas afetadas.
4. Preservar IDs RF/CA existentes; acrescentar IDs novos para manter referências.
5. Marcar decisões como propostas ou confirmadas. Só indicar implementação
   concluída quando houver código e verificação correspondente.

Escopo e critérios detalhados ficam em requisitos; a visão geral é um resumo
para leitura rápida. Alterações locais ainda precisam de commit/push para chegar à equipe.
