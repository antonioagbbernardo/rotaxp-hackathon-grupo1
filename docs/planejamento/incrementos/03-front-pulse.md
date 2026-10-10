# Incremento 03 — integrar o frontend XP Pulse

10/10/2026. Pedido: atualizar o repositório e adaptar a aplicação ao frontend
React recebido em `5eac9c5`, preservando o layout e as decisões humanas.

## Comportamento definido antes do código

- RN33: React/TypeScript em `frontend/` passa a ser a interface principal.
  Flask/SQLite e rotas anteriores continuam responsáveis por regras e gravações.
  Adaptador de leitura entrega o formato do painel sem alterar IDs do banco.
- RN34: lista e prioridade vêm dos alertas pendentes; relacionamento vem da
  avaliação humana. Emoji não representa impacto de notícia nem humor inferido.
- RN35: totais são somados com Decimal e enviados como texto. Não inventar
  distribuição, contato, data de cadastro ou interesses; ausências são explícitas.
  Interesses exibidos como revisados exigem revisão humana e sujeito cliente.
- RN36: carregamento, troca de cliente, busca/filtro, erro/retry e base vazia
  funcionam sem usar os mocks estáticos como fallback. Nenhuma consulta inicial
  chama IA. Processamento e revisão continuam ações explícitas do assessor.
- RN37: assistente responde perguntas básicas por consulta/templates com fontes
  existentes (perfil, posições/vencimentos, contatos, contexto e preferências).
  Explicar esse modo; não apresentar como conversa generativa nem recomendar
  compra/venda. Perguntas fora desses temas retornam limite explícito.
  Mencionar WhatsApp/telefone numa pergunta de preferência ou último contato
  consulta esses registros; pedir número/endereço retorna ausência.
  Atualização do cartão considera também revisões humanas; último contato é
  uma data independente, sem converter “hoje” em “há zero minutos”.
- RN38: abertura é rascunho por template para revisão/cópia, sem envio.
  Não usar interesses pessoais bloqueados, incertos ou inelegíveis. Notícias
  reais ainda não coletadas aparecem como ausência, sem notícias fixas misturadas.
- RN39: Vite usa proxy local `/api`; build pode ser servido pelo Flask na mesma
  origem. Chaves só no backend. UI anterior fica em `/legacy` para comparação.

## Aceite

| ID | Verificação |
| --- | --- |
| CA57 | Painel usa clientes/IDs/ordenação reais da base; nenhuma consulta chama IA |
| CA58 | Perfil, posições, total exato, contato e relacionamento têm dados/fontes; ausências não viram valores fictícios |
| CA59 | Revisar/processar/bloquear/tratar alerta pela UI atualiza leitura e persiste; cliente incorreto não recebe dados |
| CA60 | Pergunta básica retorna resposta com fontes do cliente; assunto não disponível ou entrada inválida tem erro/limite claro |
| CA61 | Nova fonte pendente não aparece como interesse confirmado nem altera relacionamento/abertura pessoal |
| CA62 | Lista vazia, falha e troca rápida de cliente não exibem outro cliente como selecionado; retry funciona |
| CA63 | Build TypeScript/Vite, lint, testes de API e assets servidos pelo Flask passam; segredo ausente do bundle |
| CA64 | Desktop/celular: layout preservado, ações acessíveis e sem rolagem horizontal; registrar verificação e qualquer limite |

Notícias/NewsAPI, cadastro de novos clientes, app nativo e integrações dos canais
continuam fora deste incremento. Documentar front/back e validação no registro.
