# Plataforma de relacionamento entre assessores e investidores

Status: ideia estruturada para discussão. O escopo do MVP e a stack ainda
não estão fechados. Tempo informado para o trabalho: 6h30.

## Problema e objetivo

O assessor precisa acompanhar informações financeiras e pessoais de vários
investidores, distribuídas entre canais de conversa. A proposta é reunir esse
contexto para ajudar a identificar quem precisa de atenção, por qual motivo
e qual contato faz sentido naquele momento.

Usuário principal proposto: assessor de investimentos. Ainda é necessário
definir se haverá também acesso do investidor ou de gestores de assessores.

## Visão do produto

Aplicativo e interface web para consultar a carteira de clientes, acompanhar
interações e visualizar um resumo atualizado de cada investidor.

Cada cliente reúne:

- Perfil financeiro e de investidor, com informações disponíveis da carteira.
- Preferências de relacionamento: canais, frequência e assuntos de interesse.
- Interações por WhatsApp, telefone, e-mail e reuniões presenciais.
- Notas e atas de reuniões presenciais, com envio previsto ao investidor.
- Resumo da situação atual, com referência às conversas e dados que o sustentam.
- Interesses e datas relevantes, como aniversário, time e Fórmula 1.
- Alertas financeiros e oportunidades pertinentes de contato pessoal.
- Histórico do relacionamento, próximos passos e prioridade de acompanhamento.

As integrações e os envios fazem parte da visão do produto; sua implementação
no hackathon ainda depende de viabilidade e decisão da equipe.

## Fluxo principal proposto

1. O assessor abre a visão geral dos clientes e identifica prioridades.
2. Seleciona um investidor e consulta resumo, alertas e histórico de interações.
3. Abre um alerta para entender o fato, a fonte e sua relação com aquele cliente.
4. Decide se o contato é pertinente, considerando as preferências do investidor.
5. Registra a interação ou prepara uma ata para revisão e envio.
6. O histórico e o resumo passam a refletir a nova informação.

## Interações e resumo do cliente

| Canal | Informação a reunir | Decisão pendente |
| --- | --- | --- |
| WhatsApp | Conversas e assuntos relevantes | Integração, importação ou registro manual |
| Telefone | Registro da ligação e seus pontos principais | Notas manuais ou transcrição |
| E-mail | Mensagens e encaminhamentos relevantes | Integração ou importação |
| Presencial | Notas, ata e próximos passos | Revisão, meio de envio e confirmação de envio |

O resumo deve distinguir fatos registrados, interpretações e informações
desatualizadas ou ausentes. Pontos positivos e negativos do relacionamento
precisam de evidência e contexto, com possibilidade de correção pelo assessor.

## Alertas e eventos

### Financeiros

- Riscos identificados nos dados disponíveis.
- Questões tributárias relevantes, conforme regras e fontes a definir.
- Ativos próximos do vencimento.
- Ocorrências de mercado relacionadas à carteira ou ao perfil do investidor.

Cada alerta deve explicar o motivo, a fonte, a data e o que merece revisão.
As regras financeiras e tributárias ainda precisam ser especificadas e
validadas; este documento não define cálculos nem recomendações de investimento.

### Pessoais e de relacionamento

- Aniversários e datas relevantes informadas pelo cliente.
- Eventos ligados a interesses mencionados nas conversas.
- Resultados de partidas de um time ou acontecimentos da Fórmula 1.
- Compromissos e próximos contatos combinados com o assessor.

Exemplo: uma conversa registra interesse por determinado time. Um resultado
confirmado pode gerar uma sugestão de assunto para o próximo contato, desde
que esse tipo de interação seja compatível com a preferência do cliente.

## Status e criticidade dos investidores

A ideia inclui os estados **positivo**, **negativo** e **atenção**, influenciados
pelas conversas e por eventos relevantes. É necessário definir exatamente o
que esses estados representam antes de automatizar mudanças.

Proposta para evitar interpretações ambíguas:

- **Situação financeira:** alertas e riscos derivados de dados e regras definidos.
- **Contexto do relacionamento:** fatos positivos, dificuldades ou pendências nas interações.
- **Prioridade de acompanhamento:** urgência, prazo e motivo para o assessor agir.

Um resultado esportivo não comprova o humor do cliente e não deve alterar sua
classificação financeira. Pode acrescentar uma oportunidade de contato ao
contexto de relacionamento. Mudanças de estado devem ter justificativa visível.

A criticidade indica prioridade de atendimento, não valor pessoal do investidor.
Critérios, níveis e possibilidade de ajuste manual ainda serão definidos.

## Diferentes modos de visualização

Opções para avaliação da equipe, ainda sem compromisso de implementar todas:

- **Lista:** clientes, resumo, status, próximo contato e filtros de prioridade.
- **Painel de prioridades:** alertas agrupados por urgência e motivo.
- **Detalhe do cliente:** perfil, resumo e linha do tempo das interações.
- **Agenda:** aniversários, vencimentos, eventos e contatos programados.

Aplicativo e web devem compartilhar o mesmo contexto e as mesmas regras.
Uma web responsiva/PWA é uma alternativa para reduzir o trabalho inicial;
um aplicativo separado permanece uma decisão aberta.

## Pertinência dos eventos e controle de custos

Estratégia proposta:

1. Manter interesses estruturados por cliente, com origem e revisão pelo assessor.
2. Consultar cada assunto compartilhado uma vez, em vez de pesquisar por cliente.
   Exemplo: obter o resultado de um time e relacioná-lo aos clientes interessados.
3. Priorizar fontes selecionadas, calendários e feeds, evitando buscas abertas contínuas.
4. Atualizar conforme a frequência do assunto: calendário de eventos ou consultas
   periódicas, com cache e eliminação de eventos duplicados.
5. Filtrar por regras simples antes de usar IA: interesse correspondente,
   atualidade, preferências de contato e ausência de alerta já apresentado.
6. Usar IA somente onde agregar valor, como resumir uma nova interação ou
   explicar a relação de um evento com o contexto. Reutilizar resultados.
7. Limitar alertas por cliente e permitir dispensar, silenciar ou marcar como tratado.
8. Medir chamadas externas, uso de IA e custo estimado, com limite configurável.

O objetivo é produzir poucos alertas úteis. Fontes, frequência, orçamento e
limites numéricos ainda precisam ser escolhidos. Não há estimativa de custo validada.

## Privacidade e controle

Requisitos propostos para detalhamento sob a preocupação com LGPD:

- Coletar apenas dados necessários e definir finalidade, acesso e retenção.
- Restringir o acesso aos clientes conforme a responsabilidade do assessor.
- Permitir corrigir informações e revisar interesses inferidos de conversas.
- Definir condições para capturar mensagens, registrar ligações e enviar atas.
- Revisar atas e mensagens antes de enviá-las ao investidor.
- Evitar dados pessoais em logs e definir o que pode ser enviado a serviços de IA.
- Usar dados fictícios identificados na demonstração.

Esses pontos orientam o desenho; não constituem uma validação de conformidade legal.

## Próximas decisões para fechar o MVP

1. Escolher um fluxo demonstrável e quais visualizações são essenciais.
2. Definir se o acesso pelo celular será web responsiva/PWA ou aplicativo separado.
3. Escolher quais canais terão integração real e quais usarão dados fictícios ou registro manual.
4. Selecionar um alerta financeiro e um evento pessoal para demonstrar, com regras claras.
5. Definir status, criticidade e evidências necessárias para cada mudança.
6. Escolher fontes externas e orçamento máximo de uso.
7. Alinhar stack, contratos entre as partes e divisão entre as seis pessoas.
8. Escrever critérios de aceite (SDD) e testes das regras essenciais (TDD).

Sugestão para discussão: demonstrar a abertura de um cliente, a leitura do
resumo com suas fontes, um alerta de vencimento, uma oportunidade de contato
por interesse pessoal e o registro de uma nova interação.
