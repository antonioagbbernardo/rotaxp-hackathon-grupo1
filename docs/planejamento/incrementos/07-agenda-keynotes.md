# Incremento SDD 07 — reuniões, keynotes e atualização automática

Autorizado pelo usuário: concluir as demandas SDD restantes, com verificações
mínimas. RF18–RF24; complementa CA17/CA19–CA25. Decisões antes do código:

- RN59. Reunião pertence a cliente existente e ao assessor da demonstração.
  Objetivo obrigatório (até 500 caracteres), início ISO com fuso (sem fuso =
  São Paulo), estados agendada/cancelada/concluída. Reagendar/cancelar apenas
  agendada. Registro pode representar encontro já ocorrido. Na entrega do
  incremento 07, calendário externo ainda não era sincronizado; a integração
  posterior está especificada no incremento 10.
- RN60. Pauta determinística com fatos/fontes, contexto factual revisado do cliente,
  combinados, pendências, avaliação humana e até três notícias elegíveis. Perguntas
  são sugestões. Não chamar IA para gerar pauta; ausência/falha externa sinalizada.
  Falha na antecipação (inclusive cota/ausência de chave) fica registrada na reunião
  e na pauta, mesmo se o cache compartilhado anterior ainda estiver disponível.
- RN61. Versões persistidas por assinatura dos dados + objetivo/início/dia local.
  Repetição reutiliza versão. Notas manuais separadas; revisão aponta para versão
  exata. Dados novos/reagendamento/bloqueio tornam pauta desatualizada e retiram
  aprovação anterior. GET não gera pauta nem busca notícias. Versões antigas
  ficam preservadas no banco; interface não reutiliza conteúdo inelegível.
- RN62. Reunião próxima = início entre agora e 24h (limites inclusivos). Preparação
  próxima pode renovar notícias com idade >=2h, por assunto compartilhado. Cota,
  intervalos, erro/cache e lease do incremento 05 continuam valendo. Reunião
  distante não antecipa coleta; cancelada/concluída não dispara preparação.
- RN63. Concluir exige resumo (até 4.000 caracteres), próximos passos opcionais
  (até 1.000). Em transação, criar uma interação presencial na hora do Clock e
  vincular à reunião. Repetição idêntica reutiliza; alteração em retry retorna 409.
  Decisão humana pode concluir encontro realizado antes do horário previsto.
- RN64. CLI `acompanhar-agenda --uma-vez` executa ciclo; sem flag, processo local
  a cada 60 segundos: coleta diária compartilhada e pautas de reuniões próximas.
  Sem cron na requisição web. Só funciona enquanto o comando está em execução.
  Coleta não cria alerta, muda humor/relacionamento ou envia mensagem.
- RN65. Painel oferece reunião por cliente, lista geral de próximas reuniões,
  criar/reagendar/cancelar, preparar/revisar pauta, guardar notas e concluir.
  Datas/fontes/atualização visíveis; falhas preservam formulário e notas.
- RN66. Todas as rotas herdam sessão/CSRF. Não alterar seed existente nem simular
  reunião real automaticamente; fonte externa de canais continua como premissa.

## Aceites mínimos

- CA85. Criar/listar/detalhar por cliente, validar corpo/datas/identidade e isolar dados.
- CA86. Preparar/reutilizar/revisar, invalidar com dados novos e preservar notas.
- CA87. Cancelamento/reagendamento e conclusão idempotente; uma única interação.
- CA88. Janela 24h/2h, cache compartilhado e falha de notícias mantendo pauta interna.
- CA89. Ciclo CLI prepara só reuniões próximas/agendadas e não duplica versões.
- CA90. Integração frontend compila e apresenta estados de gravação/erro/fontes.
