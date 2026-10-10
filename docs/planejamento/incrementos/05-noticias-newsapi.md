# Incremento SDD 05 — notícias compartilhadas com revisão

Recorte de T08: RF17/RF20 e feedback RF29, CA16/CA18/CA31/CA32.
O usuário autorizou continuar o desenvolvimento. Implementar primeiro a coleta
manual e o comando diário; agendamento automático, reuniões/keynotes e síntese
de notícias por IA permanecem para outro incremento.

## Regras definidas antes do código

- RN46. O assessor associa explicitamente um interesse revisado a uma consulta
  do catálogo: Fórmula 1, Palmeiras ou Corinthians. Não inferir essa associação
  do texto. Apenas fatos confirmados/corrigidos do próprio cliente, com fonte
  atual, sem conflito/bloqueio e elegíveis para contato (RN13). Guardar a revisão
  do item e o autor/data; nova revisão invalida o vínculo até reassociação.
- RN47. Consultas fixas por assunto (`q`, português, publicação decrescente,
  últimos sete dias, primeira página de dez artigos). Nada de nome, carteira,
  transcrição ou texto do cliente no NewsAPI. GET não chama o provedor.
- RN48. Cache persistente compartilhado por consulta/versionamento e dia local.
  POST e CLI reutilizam sucesso do mesmo dia, inclusive resultado vazio. No
  máximo 20 tentativas HTTP por dia local para esta instalação, contando erros.
  Configurável no backend, entre 1 e 100. Sem chave não reservar chamada.
- RN49. Reservar cada tentativa em transação antes do HTTP; lease de dois minutos
  por assunto. Tentativa abandonada pode ser retomada; a antiga não salva saída.
  Sem retries automáticos. Falha tem intervalo mínimo de 15 minutos; 429 bloqueia
  novas consultas por 30 minutos e cota externa esgotada bloqueia pelo dia local.
  Não segurar transação durante HTTP; contar conservadoramente reservas abandonadas.
- RN50. Persistir coleta, artigos e referências das coletas; deduplicar URLs
  removendo fragmento e parâmetros de rastreamento conhecidos. Somente HTTP(S),
  sem credenciais. Validar formato, origem, título e publicação antes de salvar;
  resposta inválida inteira é recusada. Não buscar página/imagem/artigo completo.
  Resultados anteriores sobrevivem a falhas, identificados pela coleta original.
  Exibir até três artigos por cliente, publicados nos últimos sete dias.
- RN51. Aplicar elegibilidade/bloqueio/revisão a cada leitura, mesmo com cache.
  Feedback “Não é relevante” exige motivo e oculta aquela URL só para o cliente,
  sem apagar interesse ou cache de outros. Persistência e repetição idempotente.
- RN52. Mostrar assunto, interesse/evidência que motivaram a associação, veículo,
  link, publicação, coleta e estado da atualização. Não classificar humor,
  risco, tributo ou recomendação de produto; notícia não vira alerta RN14.
  Falha difere de busca vazia. Chave só no backend via `X-Api-Key`; timeout
  15 segundos, resposta até 1 MB e mensagem de erro sem corpo bruto/segredos.

## Aceites / TDD

- CA72. Vínculo só aceita interesse elegível do cliente e assunto do catálogo;
  campos extras, hipótese, proposta, terceiro, fonte antiga e bloqueio recusados.
  Mudança de revisão/preferência/contato oculta associação e resultados.
- CA73. Dois clientes com o mesmo assunto usam uma chamada; GET zero chamadas;
  recarga/reinício/CLI reutilizam cache; vazio também é sucesso; novo dia coleta.
- CA74. Erro, ausência de chave, timeout, JSON inválido, 401 e 429 são explícitos;
  cache anterior mantém publicação/coleta. Cota/intervalo impedem HTTP adicional.
- CA75. Limite diário inclui falhas e reservas; clientes não multiplicam chamadas;
  concorrência e retomada não deixam tentativa antiga sobrescrever a nova.
- CA76. URL duplicada não duplica notícia; artigos removidos/fora da janela são
  omitidos. Saída malformada não persiste artigo parcial. Link inseguro recusado.
- CA77. Descartar notícia exige motivo, afeta só o cliente, permanece após reinício
  e não muda prioridade/relacionamento/interesse. Repetição mantém registro único.
- CA78. Interface permite associar, coletar e descartar com estados de espera/erro;
  mostra fontes/datas e funciona em desktop e viewport móvel. Sem assunto elegível
  há explicação; nenhum preenchimento fictício disfarçado de notícia real.

## Contrato

Detalhes em [contracts.md](../contracts.md). Novas tabelas são aditivas;
reset explícito conhece suas dependências. Regras puras, transporte REST e
coordenação/cache separados. React utiliza as mesmas rotas e atualiza o painel.
CLI `uv run --locked flask --app app coletar-noticias` processa somente assuntos
elegíveis vinculados, uma vez por dia; não instala cron nem worker.

## Referências oficiais conferidas em 10/10/2026

[Everything](https://newsapi.org/docs/endpoints/everything),
[autenticação](https://newsapi.org/docs/authentication),
[erros](https://newsapi.org/docs/errors), [planos](https://newsapi.org/pricing).
Developer: 100 requisições/dia, atraso de 24h, somente desenvolvimento/testes.
Uma coleta recente não elimina o atraso da publicação disponibilizada.
Orçamento local não contabiliza outros sistemas usando a mesma chave.

## Resultado da implementação

41 testes novos aprovados, total 329 backend; cinco frontend, lint/build.
Uma coleta real compartilhada e feedback por cliente demonstrados. CLI diário
verificado com provedor simulado/cache. Desktop conferido; largura DOM móvel
390/390 px, inspeção visual dos cartões em celular parcial. Evidências/limites
no [registro de desenvolvimento](../../registro-desenvolvimento.md).
Chave local anterior `NEWSAPI_KEY` aceita como alias de `NEWSAPI_API_KEY`.
