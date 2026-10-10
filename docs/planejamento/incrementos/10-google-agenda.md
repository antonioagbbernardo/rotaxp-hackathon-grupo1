# Incremento SDD 10 — sincronização com Google Agenda

Autorizado pelo usuário em 10/10/2026. RF32; complementa RF18–RF24 sem alterar
as regras de pauta, notas ou conclusão do incremento 07.

## Regras

- **RN76.** Um assessor conecta sua própria conta por OAuth. O painel é a fonte
  da verdade e envia eventos somente ao calendário principal (`primary`). Não
  importa eventos nem alterações do Google, não inclui convidados e não envia
  convites. O consentimento pede acesso a eventos e e-mail para identificar a
  conta conectada.
- **RN77.** Reunião criada no painel vira evento com título “Reunião com”
  seguido do nome do cliente, objetivo na descrição, início de `inicio_em`, fuso
  `America/Sao_Paulo` e duração fixa de uma hora. Alterar objetivo/horário
  atualiza o evento; cancelar o remove. Concluir conserva o evento passado.
- **RN78.** O painel salva primeiro. Falha ou ausência de conexão não perde a
  reunião: expõe estado/erro e oferece ação para nova tentativa. IDs
  determinísticos tornam criação e repetição idempotentes. Reuniões já existentes
  antes da conexão só são enviadas por nova tentativa explícita. GET não chama
  Google.
- **RN79.** Client ID/secret/redirect URI vêm de ambiente ou `.env` local,
  nunca do frontend/Git. Token OAuth fica apenas na base SQLite local. State
  OAuth é validado; rotas de API exigem a sessão do painel e escritas exigem
  CSRF. Desconectar revoga/remover credenciais locais; não apaga reuniões.

## Critérios de aceite

- **CA99.** Configuração ausente é identificada; OAuth conecta a conta e expõe
  somente estado/e-mail, sem retornar tokens.
- **CA100.** Criação, reagendamento e cancelamento sincronizam evento primário
  com duração, fuso e conteúdo definidos; notas não atualizam evento.
- **CA101.** Falha Google mantém dados locais e mostra estado/erro; retry funciona
  sem duplicar eventos.
- **CA102.** Rotas respeitam sessão/CSRF; leituras de reunião não fazem chamadas
  externas; configuração e limitações estão documentadas.

## Limites

Integração local para demonstração. Requer um projeto Google Cloud, API Google
Calendar habilitada, tela de consentimento OAuth configurada e usuário de teste
autorizado. Não é sincronização bidirecional, agenda compartilhada, gerenciamento
de participantes ou política de produção/LGPD.
