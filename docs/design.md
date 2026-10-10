# Arquitetura proposta — plataforma de assessores

Status: planejamento somente. Stack, integrações e escopo aguardam definição.

## Organização

Uma interface web adaptada ao celular e uma API central podem atender ao
primeiro fluxo. A API concentra regras, acesso aos dados e processamento de
eventos. Um banco relacional é uma opção inicial para os vínculos entre clientes,
interações, posições e alertas. A necessidade de NoSQL ainda não foi demonstrada.

Aplicativo separado permanece parte da visão do produto, sujeito à priorização
no prazo de 6h30. Web responsiva não deve ser apresentada como app nativo.

## Responsabilidades

| Parte | Responsabilidade |
| --- | --- |
| Interface | Lista, filtros, detalhes, linha do tempo e registro de interação |
| API | Validar entradas, aplicar regras e devolver dados por cliente |
| Persistência | Guardar clientes, preferências, registros, fontes e decisões |
| Processamento de eventos | Consultar fontes escolhidas, deduplicar e associar interesses |
| Resumo | Organizar fatos registrados e indicar evidências e atualidade |

Sugestão: uma aplicação simples, com responsabilidades separadas internamente,
sem serviços distribuídos no primeiro recorte.

## Entidades e relações propostas

| Entidade | Informações principais | Relações |
| --- | --- | --- |
| Assessor | Identificação e acesso | Acompanha clientes; regra de atribuição a definir |
| Cliente | Nome, perfil, objetivo e preferências | Tem posições e interações |
| Interação | Canal, data, registro, próximos passos | Pertence a cliente e identifica responsável |
| Interesse | Assunto e origem da informação | Pode ser compartilhado por vários clientes |
| Interesse do cliente | Interesse, evidência e revisão | Liga cliente a interesse |
| Posição | Ativo, valor, vencimento e fonte | Pertence a cliente |
| Evento | Assunto, ocorrência, fonte e identificador externo | Pode gerar alertas para vários clientes |
| Alerta | Motivo, prioridade, evidência e estado | Pertence a cliente; pode apontar para evento ou posição |
| Avaliação do relacionamento | Estado, justificativa, autor e data | Histórico de avaliações por cliente |

Restrições propostas: vínculos válidos, identificação única de evento por fonte,
deduplicação de alerta por cliente/regra/origem e valores monetários sem ponto
flutuante binário. Exclusão e retenção dependem de decisão explícita.

## Contratos a combinar antes de dividir o código

- Campos e identificadores de cliente, interação, alerta e evento.
- Formato de datas e fuso das regras de vencimento.
- Estados de relacionamento separados dos níveis de prioridade.
- Erros esperados para dados inválidos, acesso negado e registros inexistentes.
- Responsável por cada área e momento da primeira integração.

## Eventos pertinentes com custo controlado

Consultar um assunto uma vez e reutilizar o resultado entre clientes interessados.
Filtrar por interesse, preferência de contato, atualidade e duplicidade antes
de qualquer uso de IA. Processar mudanças, evitando reanalisar todo o histórico.

Para demonstrar, eventos simulados e identificados são uma alternativa. Para
integração real, a equipe precisa escolher fonte, frequência, limites de uso e
orçamento. Não há fonte ou estimativa de custo aprovada.

## Questões ainda abertas

- Fonte das posições financeiras e critérios das análises de risco e tributárias.
- Captura real ou registro manual por canal; revisão e envio de atas.
- Acesso de gestores e investidores, autenticação e autorização por cliente.
- Uso de IA no produto, dados enviados ao provedor e custo máximo.
- Armazenamento, correção, exclusão e retenção de informações pessoais.
- Forma de execução da demonstração e necessidade de publicação.
