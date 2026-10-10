# Documentação da equipe

**Situação atual:** base Flask/Tailwind implementada: clientes, detalhe, interações
manuais, preferências, relacionamento e alertas de vencimento/aniversário.
Incremento SDD 01 implementa importação de fontes JSON fictícias com versões
e pendências de identidade. Incremento 02 acrescenta extração Gemini e revisão
persistida; 125 testes e extração Gemini real de quatro fontes fictícias,
com sete propostas pendentes. Validação visual completa ainda pendente.
Conexão real aos canais, NewsAPI e keynotes ainda planejados.
**Última revisão:** 10/10/2026. Núcleo: consumir fontes existentes, inferir contexto
e sugerir lembranças sob supervisão humana, incorporando feedback.

## Comece por aqui

| Documento | Para que serve |
| --- | --- |
| [Visão geral](visao-geral.md) | Entender rapidamente o produto, frontend, backend e fluxo de reunião |
| [Registro para apresentação](registro-desenvolvimento.md) | Entregas de front/back, evidências, decisões, limitações e roteiro do pitch |
| [Incremento SDD 01](planejamento/incrementos/01-fontes.md) | Contrato, regras e aceites da entrada de fontes fictícias |
| [Incremento SDD 02](planejamento/incrementos/02-contexto-revisao.md) | Extração por IA, evidências, revisão e bloqueio por cliente |
| [Requisitos](planejamento/requisitos.md) | Consultar comportamentos, critérios de aceite e como implementar por etapa |
| [Especificação curta](planejamento/spec.md) | Alinhar o fluxo principal e regras básicas |
| [Contratos](planejamento/contracts.md) | Entidades, rotas `/api`, formato JSON e erros do MVP |
| [Arquitetura](planejamento/design.md) | Consultar responsabilidades, dados e decisões técnicas |
| [Tarefas](planejamento/tasks.md) | Dividir responsabilidades, integração e tempo |
| [Dados fictícios e testes](planejamento/plano-dados-ficticios.md) | Planejar uma fonte simulada e resultados esperados para validar o fluxo |
| [Contexto e feedback](integracoes/contexto-investidor.md) | Fonte existente, inferências, lembranças e revisão humana |
| [Busca de notícias](integracoes/busca-noticias.md) | Entender NewsAPI, atualização diária, cache, custos e reuniões |

## Organização local

Aplicação, testes e ferramentas estão em [backend/](../backend/README.md).
Executar os comandos de Python e CSS dentro dessa pasta.

```text
backend/                      Aplicação Flask, testes e ferramentas de CSS
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
