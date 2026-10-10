# Incremento 01 — fontes existentes simuladas

Data: 10/10/2026. Requisitos: RF03, RF04, RF16 e RF25. Recorte de CA26.
Fluxo SDD: especificação → contrato → testes em falha → implementação → validação.
Status: backend/CLI e interface implementados; 34 testes de fontes aprovados.
Fluxo visual completo e celular pendentes. Evidências no
[registro para apresentação](../../registro-desenvolvimento.md).

## Problema e resultado

A base só registra conversas manualmente. Precisamos consumir o formulário e
as conversas que já existem, mantendo evidências para a futura extração.
Neste incremento, um JSON fictício simula essa fonte. O assessor importa o arquivo,
consulta o histórico e vê formulário, canal, origem e versões no cliente correto.

Não há extração por IA, confirmação de interesses ou lembretes derivados do
formulário nesta entrega. O conteúdo original não autoriza ações. A fonte real
ainda precisa de acesso e contrato externo; o contrato interno abaixo será reutilizável.

## Regras

- RN16: aceitar somente lote marcado `ficticio: true`, de até 100 documentos.
  Origem, identificador de registro e versão positiva identificam o documento.
- RN17: resolver identidade exclusivamente por `cliente_id` conhecido, nunca
  por nome. Identidade ausente ou desconhecida fica em pendência persistida,
  sem interação ou alteração de contexto. Resolução manual fica para outro incremento.
- RN18: repetir origem/registro/versão e conteúdo não duplica nada. A mesma versão
  com conteúdo diferente retorna 409. Corrigir exige nova versão.
- RN19: versões são inteiros ordenáveis. Arquivar cada versão sem sobrescrever
  a evidência. Só a maior versão conhecida atualiza a interação importada;
  versões antigas que chegam depois não substituem o histórico atual.
- RN20: um registro mantém tipo e vínculo de cliente entre versões. Mudança
  exige reconciliação posterior; recusar 409, sem reassociação silenciosa.
- RN21: lote inválido ou conflitante não persiste nenhum dos seus documentos.
  Instantes seguem o Clock e RN02; ocorrência futura é recusada.
- RN22: formulário importado permanece como fonte. Não sobrescrever perfil,
  preferências, aniversário ou avaliações humanas com respostas não revisadas.
- RN23: notas/interações manuais não são alteradas por importação. Texto de
  fonte é exibido como texto, nunca interpretado como HTML ou instrução executável.

## Critérios de aceite antes da implementação

| ID | Cenário e resultado |
| --- | --- |
| CA40 | Importar formulário e conversas dos três clientes fictícios; consultar apenas as fontes do cliente aberto, com origem, versão e datas |
| CA41 | Repetir o lote, inclusive após reiniciar: contagens e IDs de interações não mudam |
| CA42 | Cliente ausente/desconhecido: documento fica pendente, sem aparecer em cliente por nome parecido |
| CA43 | Versão nova corrige a interação importada sem duplicá-la; versão anterior continua consultável; versão antiga recebida depois não reverte a atual |
| CA44 | Mesma versão com outro conteúdo ou tentativa de mudar cliente/tipo: 409, com campo identificado e lote sem gravações parciais |
| CA45 | Canal, data, tipo, conteúdo ou versão inválidos, lote vazio/excessivo ou sem indicação fictícia: 400 e nenhuma gravação parcial |
| CA46 | Importação preserva notas manuais, preferências e avaliações; formulário não cria aniversários nem confirma hipóteses |
| CA47 | Interface importa JSON com resultado/erro visível, mantém possibilidade de tentar novamente e mostra versões atuais/anteriores e fontes em texto seguro |

## Implementação derivada da especificação

| Camada | Entrega |
| --- | --- |
| Backend | Validação pura do lote; serviço transacional de importação; tabela adicional de documentos versionados; API de fontes/pendências; comando CLI |
| Frontend atual | Importação de arquivo na lista, pendências de identidade e consulta de fontes no detalhe; indicação de evidência sem inferência |
| Dados | `backend/dados/fonte-demo.json`, três clientes do seed, formulário e telefone/e-mail/WhatsApp, mais identidades não resolvidas |
| Testes | API, atomicidade, reimportação, reinício, versões fora de ordem, isolamento e preservação de decisões humanas |

Contrato: [contracts.md](../contracts.md). A alteração de banco é aditiva e
inicializada por `CREATE TABLE IF NOT EXISTS`; não exige reset da base existente.
Validação visual em desktop/celular deve ser registrada separadamente dos testes de API.

## Próximo incremento

Extrair fatos e hipóteses com evidências; permitir revisão e feedback. Só depois
usar contexto revisado para lembranças, notícias e keynotes. Escolher modelo,
orçamento e contrato de saída antes de implementar IA.
