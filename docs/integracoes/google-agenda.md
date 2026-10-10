# Configurar Google Agenda (incremento 10)

A conexão usa OAuth com a conta Google do assessor. Eventos são criados somente
no calendário principal dessa conta; o painel continua sendo a fonte da verdade.
Não há importação, convidados ou convites. Cada reunião dura uma hora.

## Google Cloud

1. Em um projeto Google Cloud, habilite **Google Calendar API**.
2. Configure a tela de consentimento OAuth e adicione a conta Google do assessor
   como usuário de teste, se o app estiver em modo de teste.
3. Crie um cliente OAuth do tipo **Aplicativo da Web**.
4. Cadastre como URI de redirecionamento autorizada:
   `http://localhost:5001/api/integracoes/google-agenda/retorno`
5. Configure as variáveis localmente em `backend/.env` (arquivo ignorado pelo Git):

```dotenv
GOOGLE_CALENDAR_CLIENT_ID=seu-client-id
GOOGLE_CALENDAR_CLIENT_SECRET=seu-client-secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5001/api/integracoes/google-agenda/retorno
```

Reinicie o Flask, entre no painel e use **Conectar Google Agenda**. A conta
conectada, o estado da sincronização e a opção de tentar novamente aparecem na
seção de reuniões. Sem credenciais a agenda local continua utilizável, com estado
de integração indisponível. O token OAuth permanece na base local
`backend/instance/app.db`; não compartilhe essa base nem use dados reais.

Para desconectar, use a ação no painel. A autorização local é removida e o token
é revogado quando possível; eventos já criados no Google permanecem lá.

Detalhes de rotas e aceites: [incremento 10](../planejamento/incrementos/10-google-agenda.md)
e [contratos](../planejamento/contracts.md).
