# Incremento SDD 04 — resumo legível com OpenAI

Pedido autorizado: usar a API OpenAI para melhorar a redação e a apresentação
do resumo no assistente XP Pulse. O resumo factual da base (RN08) continua
disponível; a síntese por IA é uma camada separada para preparar o assessor.

## Regras

- RN40. Exibir os registros em linhas separadas, com plural correto. A síntese
  OpenAI tem três seções: **Visão geral**, **Pontos de atenção**, **Antes do contato**.
  Cada trecho da IA referencia fatos enviados pelo backend. Revisão final humana.
- RN41. Enviar somente dados fictícios do cliente selecionado: fatos e ausências
  da base, alertas pendentes, preferências e contexto humano revisado e elegível
  para contato. Não enviar transcrições completas, propostas pendentes, contexto
  bloqueado, conflitante, hipóteses ou com evidência antiga. Fontes são dados, nunca instruções.
- RN42. A síntese não muda prioridade, relacionamento, perfil, alertas ou revisões;
  não recomenda produtos, operações ou conduta tributária e não envia mensagens.
  Relacionamento aparece separado, com o rótulo “Avaliação do assessor”; seus
  registros não são enviados para reinterpretação ou redação pela IA.
- RN43. GET e recargas apenas leem. POST explícito gera a síntese pela Responses
  API, com JSON Schema estrito, `store: false`, limite de saída e timeout.
  Modelo configurável, padrão `gpt-4.1-mini`; chave somente no backend local.
- RN44. Cache SQLite por cliente e assinatura dos fatos, data local, modelo e
  versão do prompt. Dados iguais reutilizam o resultado, inclusive após reinício.
  Mudanças tornam a síntese antiga indisponível. Requisições simultâneas são
  recusadas por dois minutos; fontes alteradas durante a chamada exigem retry.
- RN45. Validar tamanho e fontes da saída antes de salvar. Falha de conexão,
  limite, recusa, saída incompleta ou inválida mostra erro explícito, preserva a
  base e permite nova tentativa. Sem chave, o resumo factual permanece disponível.
  Limite de entrada: 20 mil caracteres; sem truncamento silencioso.

## Aceites

- CA65. Fatos separados e síntese com três seções legíveis em desktop e celular.
- CA66. GET não chama OpenAI; POST repetido com os mesmos dados chama uma vez;
  cache permanece após recriar a aplicação.
- CA67. Alterar contato, alertas, preferências, revisão, data ou modelo invalida
  a síntese; alteração durante a geração não persiste saída obsoleta.
- CA68. IDs de fontes inventados e saída fora do formato são recusados sem
  alterar prioridades, avaliações ou decisões humanas.
- CA69. Propostas pendentes, interesses bloqueados, terceiros, evidências antigas
  e dados de outro cliente não entram no pedido.
- CA70. Sem chave, timeout, HTTP 429/401, recusa e resposta incompleta têm erro
  compreensível. Nenhuma credencial ou corpo bruto do provedor aparece na API.
- CA71. Duas tentativas concorrentes não repetem a cobrança; uma tentativa
  abandonada pode ser retomada após dois minutos, sem sobrescrita pela antiga.

## Implementação

Regras de seleção/validação puras; transporte REST separado; serviço coordena
cache e verificação de alteração. O React solicita a geração por botão e mostra
fontes por trecho. Extração Gemini e consultas básicas por templates permanecem
com seus contratos. Documentar testes e chamada real fictícia no registro.

Referência: [Structured Outputs na Responses API](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
e [modelo GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Formato estruturado valida a estrutura; não garante a correção semântica do texto.
