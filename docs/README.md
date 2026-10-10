# Documentação da equipe

**Situação atual:** planejamento. Nenhuma funcionalidade está implementada nesta pasta.
**Última revisão:** 10/10/2026.

## Comece por aqui

| Documento | Para que serve |
| --- | --- |
| [Visão geral](visao-geral.md) | Entender rapidamente o produto, frontend, backend e fluxo de reunião |
| [Requisitos](planejamento/requisitos.md) | Consultar comportamentos, critérios de aceite e como implementar por etapa |
| [Especificação curta](planejamento/spec.md) | Alinhar o fluxo principal e regras básicas |
| [Contratos](planejamento/contracts.md) | Entidades, rotas `/api`, formato JSON e erros do MVP |
| [Arquitetura](planejamento/design.md) | Consultar responsabilidades, dados e decisões técnicas |
| [Tarefas](planejamento/tasks.md) | Dividir responsabilidades, integração e tempo |
| [Busca de notícias](integracoes/busca-noticias.md) | Entender NewsAPI, atualização diária, cache, custos e reuniões |

## Organização local

```text
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
