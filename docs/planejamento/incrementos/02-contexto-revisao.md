# Incremento 02 — contexto por IA e revisão humana

Data: 10/10/2026. RF05, RF26, RF28 e RF30; revisão e bloqueio por cliente de RF29.
SDD: especificação → contrato → teste em falha → código → validação/documentação.

## Resultado esperado

Preparar o assessor com menos busca manual e mais contexto útil; preservar
sua decisão profissional. Nenhum processamento de IA age no lugar dele.

O assessor processa as fontes do cliente, vê fatos extraídos e hipóteses com
trechos/campos de origem e decide aprovar, corrigir, descartar ou adiar.
Correções ficam preservadas. Uma fonte nova pode gerar outra proposta, nunca
sobrescrever a decisão humana. Possíveis contradições aparecem para revisão.

Integração real proposta: Gemini, modelo configurável, inicialmente
`gemini-3.5-flash-lite`, via REST `generateContent` com saída JSON estruturada.
Formato atual: `generationConfig.responseFormat.text` com `APPLICATION_JSON`
e `schema`, conforme a referência REST; sem campos antigos de formato simultâneos.
Usuário escolheu integrar IA agora e vai fornecer chave local. Plano gratuito
e disponibilidade do modelo dependem do projeto; não ativar faturamento.
[Preços](https://ai.google.dev/gemini-api/docs/pricing),
[cotas](https://ai.google.dev/gemini-api/docs/rate-limits),
[referência REST](https://ai.google.dev/api/generate-content).

## Regras e limites

- RN24: só documentos atuais e com cliente resolvido entram na IA. Cada lote
  novo agrupa documentos ainda não processados para o modelo/versão do prompt.
  A fonte é dado, nunca uma instrução para executar ações. Sem ferramentas externas.
- RN25: todo item contém categoria, assunto estável, sujeito, valor, tipo
  `fato`/`hipotese` e evidências. Trecho deve existir literalmente no documento
  indicado; formulário exige campo válido. Validar tudo antes de salvar qualquer item.
  O esquema enviado ao Gemini usa seu subconjunto suportado de JSON Schema;
  formato de slug e limites de texto permanecem obrigatórios na validação local.
  Não depender de palavras-chave de schema que o provedor não suporta.
  No teste real, limites de arrays no esquema completo foram recusados; enviar
  esses limites como instrução e aplicar 0–30 itens / 1–5 evidências no backend.
- RN26: o modelo não confirma fatos, interesses, humor, aniversário ou preferência.
  Novos itens começam pendentes. Não alterar campos do cliente nem alertas da base.
  Sujeito `familiar`/`terceiro`/`incerto` permanece separado do investidor.
- RN27: cache por conjunto de documentos novos, modelo e versão do prompt.
  Repetir sem novidades não chama IA. Processamento concorrente do mesmo cliente
  é recusado; tentativa abandonada pode ser retomada após dois minutos.
  Timeout de 30 segundos, até 40 mil caracteres de fontes e 30 itens por resposta;
  sem truncamento silencioso ou retry automático de cota/chave.
- RN28: falha, resposta inválida ou fonte mudando durante a chamada preserva
  todo contexto anterior. Mostrar erro explícito; não produzir fallback simulado.
- RN29: revisão persiste ação, motivo, assessor, data e versão da revisão.
  Correção muda valor revisado, mantendo valor extraído e evidência. Adiar exige
  data futura; item volta à fila quando a data chega, sem apagar o histórico.
- RN30: uma nova extração não sobrescreve aprovação/correção/descarte. Itens
  distintos com mesma categoria/assunto/sujeito e valores divergentes são marcados
  como possível conflito, inclusive com revisão anterior de evidência antiga.
  Diferença textual não prova contradição semântica; o assessor decide.
- RN31: bloquear um assunto para um cliente preserva o interesse/contexto e
  afeta somente elegibilidade para contato desse cliente; permitir novamente
  também fica registrado. Descartar um item não bloqueia o assunto.
- RN32: contexto confirmado continua separado do resumo por template da base.
  Não há lembrete automático, envio, notícias ou keynotes neste incremento.

## Aceite definido antes do código

| ID | Cenário e resultado |
| --- | --- |
| CA48 | Processar fontes do cliente correto produz fatos/hipóteses pendentes com evidências, sem fontes de outro cliente ou identidades pendentes |
| CA49 | Reprocessar sem novidades não chama provedor; fonte nova é processada uma vez e decisões anteriores permanecem |
| CA50 | Fonte inexistente, trecho inventado, campo errado ou estrutura inválida: 502, sem salvar parte dos itens |
| CA51 | Aprovar/corrigir/descartar/adicionar adiamento persiste ao reiniciar; correção mantém valor original e evidência; silêncio não conta como decisão |
| CA52 | Novo dado conflitante preserva a correção anterior e sinaliza possível conflito; familiar não vira dado do investidor |
| CA53 | Bloqueio por cliente preserva interesse e não afeta outro cliente; descarte só afeta o item escolhido |
| CA54 | Chave ausente, timeout, cota, resposta truncada ou erro externo preserva contexto anterior e informa a causa sem expor chave/conteúdo bruto |
| CA55 | Revisão inválida, cliente/item incorreto ou versão de revisão desatualizada não escreve; fonte alterada durante chamada exige novo processamento |
| CA56 | Interface distingue pendentes/revisados, sujeito, evidência e conflito; permite as quatro ações com erro/retry e bloqueio explícito de assunto |

## Componentes e prova de entrega

Backend: provedor REST isolado, validação pura de saída, serviço de processamento,
cache/controle de concorrência, itens e histórico de revisão/bloqueio em SQLite.
Frontend: botão processar no cliente, fila de revisão, campo de correção, motivo,
adiamento, indicação de fonte e lista de contexto revisado.

Testes automatizados usam provedor injetado e transporte HTTP simulado; não
medem qualidade do modelo. Chamada real exige chave e avaliação manual de uma
amostra fictícia. Registrar separadamente testes, chamada real e validação visual
no [registro para apresentação](../../registro-desenvolvimento.md).

## Fora desta entrega

Lembretes derivados de datas, relevância de notícias, reuniões/keynotes e
reconciliação das identidades pendentes. O contexto e as preferências de assunto
são a base para esses incrementos, sem apresentá-los como prontos.
