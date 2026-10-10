# Incremento SDD 08 — lembranças confirmadas pelo assessor

RF27–RF29; complementa CA29–CA32. Recorte para concluir o MVP:

- RN67. Mostrar candidatos de contexto nas categorias data_importante/compromisso:
  somente fatos confirmados/corrigidos, fonte atual, sem conflito/bloqueio, sobre
  o cliente ou familiar. Não interpretar texto ambíguo como data automaticamente.
  O assessor confirma descrição, tipo (aniversario/compromisso) e data ISO.
  Aniversário usa dia/mês recorrente; compromisso usa a data exata. Fonte/revisão
  preservadas e sujeito exibido (cliente/familiar), sem cadastrar nome de familiar.
- RN68. Lembrança é anotação vinculada ao item/revisão; uma por item e cliente.
  Fonte ou revisão alterada impede exibição até nova confirmação. Revalidar
  permissão pessoal e bloqueio a cada consulta. Ocorrência anual calcula próximo
  dia/mês; 29/02 vira 28/02 em ano não bissexto, como RN12.
- RN69. Mostrar pendências nos próximos sete dias, ou compromisso vencido, com
  motivo/fonte/data. Respeitar intervalo de contato para sugerir abordagem pessoal,
  sem presumir que lembrança autoriza contato. Não alterar alertas/prioridade RN14.
  Assessor pode consultar todas as anotações elegíveis, mesmo fora da janela.
- RN70. Feedback por ocorrência: concluir/descartar/adiar, com motivo obrigatório.
  Adiamento exige data futura. Repetição idêntica não duplica; próxima ocorrência
  anual volta à avaliação. Não apagar contexto ou afetar outros clientes.
  Alterar tipo/descrição/data cria nova versão da anotação e não reaplica uma
  decisão tomada sobre a anotação anterior.

## Aceites mínimos

- CA91. Apenas item revisado elegível do cliente/familiar vira lembrança; data
  explícita e fonte/revisão preservadas; terceiros/hipóteses recusados.
- CA92. Aniversário recorrente, compromisso vencido e janela sete dias corretos.
- CA93. Fonte/revisão/bloqueio/permissão retiram elegibilidade; feedback e adiamento
  persistem por ocorrência, sem duplicação, alteração do perfil ou prioridade.
- CA94. Tela para confirmar e tratar, com fonte e decisão humana, build aprovado.
