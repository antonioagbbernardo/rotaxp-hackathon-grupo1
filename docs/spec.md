# MVP — acompanhamento de investidores

Status: especificação adotada para o hackathon (decisões de 10/10/2026), sujeita
a ajuste da equipe. Escopo fechado: não ampliar após a tarefa T00.
Referência: `ideia-plataforma-assessores.md`, `design.md`, `contracts.md` e
instruções do evento.

## Objetivo

O assessor identifica quem precisa de atenção, entende o motivo com base em
fontes e registra o próximo contato em uma interface web utilizável no celular.

## Primeiro fluxo

Listar clientes (ordenados por prioridade) → abrir cliente → consultar resumo,
alertas e fontes → registrar interação → tratar alerta → consultar histórico e
prioridade atualizados após recarregar.

## Recorte do MVP

Obrigatório:

- Lista de clientes com busca, filtro e ordenação por prioridade.
- Detalhe com perfil, interesses, preferências de contato, posições, datas
  importantes e histórico.
- Resumo factual derivado das informações registradas, sem inferir humor.
- Alertas de vencimento e de aniversário (`DataImportante`).
- Registro manual de interações de WhatsApp, e-mail, telefone e presencial.
- Estado de relacionamento informado pelo assessor, com justificativa.
- Marcar alertas como tratados, com persistência.

Opcional (somente depois do fluxo completo validado): eventos pessoais externos
ou simulados ligados a interesses (esportes, Fórmula 1).

Fora do MVP: integrações reais de canais, envio de mensagens/atas, aplicativo
mobile separado, análise tributária automatizada, autenticação. Demonstração com
um único assessor e dados fictícios identificados.

## Regras

Os períodos abaixo são decisões da equipe, não regras dos organizadores.
"Hoje" é a data no fuso `America/Sao_Paulo`. Limites inclusivos.

RN01. Cada interação pertence a um único cliente existente e exige canal e texto.
RN02. O histórico é ordenado pela `data_hora` da interação, da mais recente para a
      mais antiga (empate: registro mais recente primeiro).
RN03. Posição com vencimento de 0 a 30 dias a partir de hoje gera alerta de
      vencimento: prioridade **alta** de 0 a 7 dias, **média** de 8 a 30. 31 dias
      ou mais não gera alerta.
RN04. Posição vencida (vencimento anterior a hoje) gera alerta próprio de
      prioridade **alta**.
RN05. Eventos externos/simulados (opcional) só se relacionam a interesses
      registrados e à permissão `permite_assuntos_pessoais`; o mesmo evento não
      gera alertas duplicados (chave de ocorrência única por cliente/regra/origem).
RN06. Um evento pessoal não modifica o perfil financeiro nem presume o humor.
RN07. Alterar o estado de relacionamento exige justificativa do assessor.
RN08. Resumos e alertas exibem suas fontes; ausência de dado não vira conclusão
      (exibe "não informado").
RN09. Um alerta tratado não permanece na contagem de pendências.
RN10. Dados persistem entre recargas e reinicializações do servidor.
RN11. A prioridade do cliente é a maior prioridade entre seus alertas não
      tratados; sem alertas, é **baixa**. Alertas tratados não influenciam.
      Empate de faixa: pendência mais próxima, depois nome. O estado de
      relacionamento (manual) não altera a prioridade.
RN12. Datas importantes (`DataImportante`, aniversário) registradas pelo assessor
      geram alerta recorrente de prioridade **média** com até 7 dias de
      antecedência, somente se `permite_assuntos_pessoais = true`. Cada
      ocorrência anual tem chave própria (sem duplicar; tratado não reaparece
      naquela ocorrência).

### Prioridade (resumo)

| Prioridade | Origem |
| --- | --- |
| Alta | Posição vencida ou vencimento em 0–7 dias |
| Média | Vencimento em 8–30 dias ou aniversário em 0–7 dias |
| Baixa | Nenhum alerta pendente |

## Critérios de aceite

- CA01: busca por nome e filtros retornam somente os clientes correspondentes.
- CA02: abrir um cliente mostra somente suas posições, interações e preferências.
- CA03: salvar interação válida atualiza o histórico e permanece após recarregar.
- CA04: canal inválido, texto vazio ou cliente inexistente não criam registros.
- CA05: vencimentos em 0, 7, 8 e 30 dias seguem RN03; 31 dias fica fora; vencido
  gera alerta alta (RN04).
- CA06 (opcional): evento associado a interesse aparece com fonte e não se repete
  no reprocessamento.
- CA07: cliente sem `permite_assuntos_pessoais` não recebe sugestões pessoais
  (aniversário ou evento).
- CA08: tratar um alerta atualiza a lista/contagem e persiste após recarregar.
- CA09: alterar relacionamento sem justificativa é recusado.
- CA10: o fluxo principal pode ser realizado em tela de celular sem rolagem
  horizontal da página.
- CA11: cliente com múltiplos alertas assume a maior prioridade, recalculada
  após tratar um alerta.
- CA12: um aniversário próximo gera apenas um alerta, respeita a preferência e
  não reaparece como pendência depois de tratado naquela ocorrência anual.
- CA13: histórico ordenado conforme RN02 (cobre RN02).
- CA14: dados ausentes aparecem como "não informado" e todo alerta exibe fonte
  (cobre RN06 e RN08).

## Validação

Testes de regras e persistência/API, seguidos de verificação do fluxo no
navegador em desktop e celular, a partir de um clone limpo do repositório.
Informar separadamente verificações executadas e limitações. Relógio injetável
nos testes e seed com datas relativas a "hoje".

## Decisões pendentes

- Controle de acesso antes de uso real ou publicação com dados pessoais.
