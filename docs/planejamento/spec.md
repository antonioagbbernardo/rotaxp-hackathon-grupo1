# MVP — acompanhamento de investidores

Status: proposta documental, sujeita às decisões da equipe. Implementação suspensa
por solicitação do usuário; esta especificação não autoriza gerar código.
Detalhamento: [requisitos](requisitos.md). Leitura rápida: [visão geral](../visao-geral.md).

## Objetivo

O sistema consome formulário inicial, transcrições, e-mails e WhatsApp Business
já existentes. Extrai e infere contexto para sugerir lembranças, alertas e pautas
pertinentes. O assessor decide o uso e fornece feedback para melhorar a seleção.

## Primeiro fluxo

Consumir fontes existentes → extrair contexto com evidências → assessor revisa
e dá feedback → selecionar lembranças/notícias → preparar reunião → atualizar contexto.

## Recorte proposto

- Lista de clientes com busca e filtro de prioridade.
- Detalhe com perfil, interesses, preferências de contato, posições e histórico.
- Fatos e hipóteses extraídos das fontes, com evidência e revisão humana.
- Datas, aniversários e lembranças com sujeito correto e pertinência revisável.
- Feedback persistido que corrige contexto e reduz sugestões irrelevantes.
- Alertas de vencimento e notícias via NewsAPI associadas a interesses; dados
  fictícios identificados para teste e demonstração quando necessário.
- Leitura do formulário e da fonte de conversas existente; registro manual é complemento.
- Estado de relacionamento informado pelo assessor com justificativa.
- Marcar alertas como tratados, com persistência.
- Visualização de clientes e de prioridades.
- Reuniões próximas com pauta breve, fontes e observações revisáveis pelo assessor.

Construção da captura dos canais e do formulário fica fora do recorte.
Envio de mensagens/atas, aplicação mobile separada e análise
tributária automatizada ficam pendentes de definição. Propõe-se usar dados
fictícios identificados na primeira demonstração.

## Regras iniciais propostas para a demonstração

Os períodos de 7 e 30 dias abaixo são sugestões, não regras fornecidas pela equipe
ou pelos organizadores. Precisam ser validados antes da implementação.

RN01. Cada interação pertence a um único cliente existente e exige canal e texto.
RN02. O histórico é ordenado do registro mais recente para o mais antigo.
RN03. Vencimentos de hoje até 30 dias geram alertas; os próximos 7 dias têm prioridade alta.
RN04. Ativos vencidos têm indicação própria; o limite dos períodos é inclusivo.
RN05. Eventos pessoais só se relacionam a interesses registrados e à permissão
de abordar assuntos pessoais. O mesmo evento não gera alertas duplicados.
RN06. Um evento pessoal não modifica o perfil financeiro nem presume o humor.
RN07. Alterar o estado de relacionamento exige justificativa do assessor.
RN08. Resumos e alertas exibem suas fontes; ausência de dado não vira conclusão.
RN09. Um alerta tratado não permanece na contagem de pendências.
RN10. Dados devem persistir entre recargas e reinicializações do servidor.

## Critérios de aceite

- CA01: busca por nome e filtros retornam somente os clientes correspondentes.
- CA02: abrir um cliente mostra somente suas posições, interações e preferências.
- CA03: ingerir interação válida atualiza o histórico e permanece após recarregar.
- CA04: canal inválido, texto vazio ou cliente inexistente não criam registros.
- CA05: vencimentos em 0, 7 e 30 dias seguem os limites; 31 dias fica fora do alerta.
- CA06: evento associado a interesse aparece com fonte e não se repete no processamento.
- CA07: cliente que não deseja assuntos pessoais não recebe esse tipo de sugestão.
- CA08: tratar um alerta atualiza a lista/contagem e persiste após recarregar.
- CA09: alterar relacionamento sem justificativa é recusado.
- CA10: o fluxo principal pode ser realizado em tela de celular sem rolagem horizontal da página.

## Validação

Critérios CA11–CA33, incluindo notícias, reuniões, inferência e feedback, estão em
[requisitos](requisitos.md). As regras de busca estão em
[integração NewsAPI](../integracoes/busca-noticias.md).

Testes de regras e persistência/API, seguidos de verificação do fluxo no navegador
em desktop e celular. Informar separadamente verificações executadas e limitações.

## Decisões pendentes

- Definir contrato e acesso à fonte existente e vínculo de identidade dos clientes.
- Confirmar stack. Python, Node.js, React, SQL e NoSQL foram opções mencionadas;
  nenhuma combinação foi aprovada. O escopo solicitado abrange o MVP completo.
- Confirmar regras RN03/RN04 e o recorte do MVP.
- Definir controle de acesso antes de uso real ou publicação com dados pessoais.
