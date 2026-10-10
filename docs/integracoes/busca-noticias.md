# Busca de notícias — atualização diária e preparação de reuniões

Status: desenho documental. NewsAPI.org foi escolhido pela equipe como fonte;
plano contratado, horários, limites e uso de IA ainda estão pendentes.

Interpretação da proposta: a rotina diária pode ser antecipada quando há uma
reunião próxima. Atualizar a visão atual preserva notícias, fontes e históricos;
não apaga registros de interações ou avaliações anteriores.

## 1. Responsabilidades

**Recomendação inicial:** rotina agendada no backend para coleta; IA opcional
para classificar ou resumir somente os resultados relevantes.

| Componente | Responsabilidade |
| --- | --- |
| Agendador | Disparar atualização diária e verificar reuniões próximas |
| Coletor NewsAPI | Executar consultas previamente definidas com limites e timeout |
| Cache por assunto | Reutilizar consultas entre clientes e reuniões |
| Regras de pertinência | Associar interesses, preferências e assuntos financeiros definidos |
| Especialista de IA, opcional | Produzir resumo curto com referências aos artigos recebidos |
| Interface | Mostrar contexto, fonte, publicação, última coleta e falhas de atualização |

O agendamento não precisa de um agente de IA. Se houver um subagente no produto,
seu papel deve ser limitado à análise dos artigos já coletados, sem liberdade
para criar consultas ilimitadas. No MVP, essa análise pode ser uma chamada
delimitada ao modelo; não exige uma infraestrutura de múltiplos agentes.

## 2. Coleta compartilhada por assunto

1. Normalizar assuntos acompanhados: por exemplo, Fórmula 1 e determinado time.
2. Usar consultas revisadas pela equipe, evitando enviar nome, carteira ou
   conversas do investidor ao NewsAPI.
3. Buscar cada consulta uma vez por ciclo e armazenar resultados compartilhados.
4. Deduplicar artigos por URL normalizada; agrupar cobertura repetida de um
   mesmo acontecimento quando possível. Uma URL diferente pode cobrir o mesmo fato.
5. Relacionar artigos aos clientes por interesses e preferências registrados.
6. Apresentar somente informações pertinentes com fonte e data.

O endpoint proposto é `/v2/everything`, com `q`, `language=pt`, período de busca,
`sortBy=publishedAt` e tamanho limitado da página. Fontes/domínios podem ser
selecionados. Aumentar paginação consome chamadas adicionais.
[Documentação do endpoint](https://newsapi.org/docs/endpoints/everything).

Uma notícia pode sugerir um assunto de conversa. Ela não comprova o humor do
cliente, nem permite sozinha calcular risco, tributo ou recomendar investimento.
Resultados esportivos exatos podem exigir uma fonte específica além das notícias.

## 3. Política de atualização

### Rotina diária

- Executar uma vez por dia, em horário configurável no fuso America/Sao_Paulo.
- Consultar assuntos ativos compartilhados, com pequeno período de sobreposição
  para recuperar artigos indexados depois da coleta anterior.
- Avançar o marcador de coleta bem-sucedida somente após persistir os resultados.
- Atualizar os resumos apenas se houver mudança relevante nos artigos.
- Resultados vazios são válidos; registrar tentativa bem-sucedida mesmo sem novidades.

### Reunião próxima

Proposta de parâmetros para revisão: reunião nas próximas **24 horas** e cache
dos assuntos com mais de **2 horas** desde a última coleta bem-sucedida.

1. Identificar reuniões futuras confirmadas e seus clientes.
2. Selecionar assuntos pertinentes e reunir consultas iguais entre reuniões.
3. Se o cache estiver recente, reutilizar sem nova chamada externa.
4. Se estiver antigo, enfileirar atualização antecipada, respeitando cota e
   consulta já em andamento para o mesmo assunto.
5. Preparar o contexto da reunião com as notícias disponíveis e suas fontes.

Esse contexto alimenta os **keynotes**, a pauta pré-reunião descrita em
[requisitos](../planejamento/requisitos.md). A pauta também utiliza objetivos,
conversas e alertas internos; sua atualização não depende de haver notícia nova.
Versões geradas preservam observações manuais do assessor.

A reunião aumenta a prioridade da consulta; não remove limites do provedor.
Um botão “Atualizar contexto” pode usar o mesmo fluxo, com intervalo mínimo
entre tentativas. Reagendar/cancelar uma reunião deve atualizar seus disparos.

### Limitação do plano gratuito

Na consulta de 10/10/2026, o plano Developer informa **100 chamadas por dia**,
**atraso de 24 horas** e uso em desenvolvimento/testes, excluindo staging e
produção. Antecipar uma busca não remove esse atraso. Confirmar o plano para
a demonstração e para eventual publicação. [Planos oficiais](https://newsapi.org/pricing).

## 4. Custos e limites

Orçamento deve considerar consultas únicas, páginas, atualizações antecipadas
e retries; quantidade de clientes não deve multiplicar consultas idênticas.

Exemplo ilustrativo: 10 consultas diárias de uma página e 5 consultas adicionais
antes de reuniões = 15 chamadas, antes de retries. O orçamento real depende
dos assuntos, paginação e limite contratado.

- Separar orçamento diário de rotina, reuniões e reserva para falhas.
- Configurar teto abaixo da cota e contar todas as tentativas HTTP.
- Priorizar reuniões próximas se o orçamento estiver curto.
- Evitar execuções concorrentes da mesma consulta; consolidar solicitações.
- Reutilizar análise de IA por conjunto/versão dos artigos, idioma e versão do prompt.
- Registrar chamadas ao provedor e uso de IA separadamente.
- Definir limite de artigos por assunto e de sugestões por cliente.

No caso de cota esgotada, mostrar os últimos resultados com sua data e explicar
que a atualização não ocorreu. Não inventar notícia para preencher a tela.

## 5. Informação persistida

| Registro | Campos propostos |
| --- | --- |
| Assunto/consulta | Identificador, termos revisados, idioma, fontes e estado ativo |
| Artigo | URL, título, descrição disponível, fonte e data de publicação |
| Coleta | Consulta, tentativa, sucesso, erro, próxima elegibilidade e contagem de chamadas |
| Reunião | Cliente, data/hora, fuso e estado confirmado/cancelado |
| Contexto de reunião | Cliente, reunião, artigos usados e data de preparação |
| Pauta da reunião | Versão, contexto interno e artigos usados, revisão e notas manuais separadas |
| Análise opcional | Artigos de origem, resultado, versão e uso/custo do modelo |

Separar **data de publicação**, **data do evento quando conhecida**, **data de
coleta** e **data de preparação do resumo**. Publicação recente não garante
que o evento tenha ocorrido recentemente.

O NewsAPI não fornece o artigo completo; o campo `content`, quando disponível,
é truncado. Resumir apenas o material recebido, apontar seus limites e oferecer
link à fonte. [Campos da resposta](https://newsapi.org/docs/endpoints/everything).

## 6. Integração e falhas

- Chave guardada no backend, enviada no cabeçalho `X-Api-Key`; sem chave no
  frontend, repositório ou logs.
- Timeout e retries limitados para falhas temporárias, com espera progressiva.
- Erro de chave/parâmetro exige correção; não deve gerar loop de tentativas.
- Para HTTP 429 e cota esgotada, adiar consultas e preservar o cache.
- Separar “não houve notícia” de “a consulta falhou”.

As respostas do provedor incluem códigos como `rateLimited` e `apiKeyExhausted`.
[Documentação de erros](https://newsapi.org/docs/errors).

## 7. Critérios de aceite propostos

- **BN01:** dois clientes interessados no mesmo assunto reutilizam uma coleta.
- **BN02:** repetir a rotina não duplica artigos nem alertas do mesmo fato/regra.
- **BN03:** reunião próxima e cache recente não geram chamada adicional.
- **BN04:** reunião próxima e cache antigo geram uma atualização prioritária,
  dentro do orçamento; pedidos concorrentes são consolidados.
- **BN05:** uma atualização malsucedida mantém o último resultado e sua data.
- **BN06:** cota esgotada interrompe novas chamadas e sinaliza indisponibilidade.
- **BN07:** preferência por assuntos exclusivamente financeiros exclui sugestões pessoais.
- **BN08:** eventual resumo de IA referencia artigos e não afirma fatos ausentes.
- **BN09:** cancelar/reagendar uma reunião evita disparos antigos.
- **BN10:** a interface distingue notícia, evento simulado e cache desatualizado.

## 8. Ordem sugerida de implementação futura

1. Fixar poucos assuntos de demonstração e parâmetros das consultas.
2. Definir armazenamento e contrato de retorno, incluindo data e origem.
3. Validar testes de cache, duplicidade e seleção por interesse com respostas fictícias.
4. Integrar uma consulta real do NewsAPI e tratar suas falhas.
5. Acrescentar agendamento diário e contexto de reuniões.
6. Acrescentar IA opcional após verificar pertinência e custo da coleta.

Para o pitch, a execução manual da mesma rotina pode demonstrar o fluxo sem
esperar um dia. Só declarar o agendamento automático implementado após verificá-lo.
