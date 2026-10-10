# Arquitetura proposta — plataforma de assessores

Status: planejamento somente. NewsAPI.org definido como fonte de notícias;
stack, demais integrações e escopo aguardam definição.

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
| Preparação de reunião | Combinar contexto e fontes em pauta versionada; preservar notas manuais |

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
| Reunião | Objetivo, início/fuso, responsável e estado | Pertence a cliente; pode ter interação de conclusão |
| Versão da pauta | Conteúdo, fontes, versão dos dados e data de geração/revisão | Pertence a reunião; notas manuais armazenadas separadamente |

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

Fonte escolhida: **NewsAPI.org**. Planejar coleta diária por assuntos compartilhados
e atualização antecipada quando houver reunião próxima, reutilizando cache.
Plano, horários, orçamento e parâmetros ainda precisam de definição.

O agendador e o coletor são rotinas de backend. Um especialista de IA é opcional
para analisar resultados filtrados, com entradas e orçamento limitados.
Detalhamento e fontes oficiais: [busca de notícias](../integracoes/busca-noticias.md).

## Questões ainda abertas

O agendador prepara reuniões na janela definida. Alterações internas podem renovar
a pauta sem outra busca externa; mudanças de data ou estado reconciliam disparos.
Reunião concluída preserva a pauta usada e a interação resultante.

- Fonte das posições financeiras e critérios das análises de risco e tributárias.
- Captura real ou registro manual por canal; revisão e envio de atas.
- Acesso de gestores e investidores, autenticação e autorização por cliente.
- Uso de IA no produto, dados enviados ao provedor e custo máximo.
- Armazenamento, correção, exclusão e retenção de informações pessoais.
- Forma de execução da demonstração e necessidade de publicação.
