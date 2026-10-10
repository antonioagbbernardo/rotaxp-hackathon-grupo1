# Requisitos e etapas de implementação do MVP

**Status:** React XP Pulse integrado ao Flask/SQLite, ingestão JSON fictícia e contexto/revisão implementados;
Gemini testado com simulação e uma amostra fictícia real. Fonte real,
lembranças derivadas, notícias e reuniões ainda planejadas.
**Referências:** [especificação](spec.md), [arquitetura](design.md) e [tarefas](tasks.md).
Integração do front: [incremento 03, RN33–RN39 e CA57–CA64](incrementos/03-front-pulse.md).
**Usuário principal proposto:** assessor de investimentos.
**Revisado em:** 10/10/2026. Fontes existentes, inferência de contexto, supervisão humana e feedback são o núcleo do produto.

**Decisão posterior da equipe:** usar NewsAPI.org para notícias, com atualização
diária e possibilidade de atualização antecipada por reunião próxima. Política
de cache, limites e papel opcional de IA em [busca-noticias.md](../integracoes/busca-noticias.md).

## 1. Objetivo e recorte

### Pressupostos confirmados pelo usuário

- Existe uma fonte com transcrições de ligações, e-mails e WhatsApp Business.
- O investidor já preencheu um formulário inicial, também disponível como fonte.
- Nosso produto consome esses materiais para extrair e inferir contexto.
- Sugestões e lembranças ficam sob decisão final do assessor.
- Feedback de relevância e correções deve influenciar o contexto e sugestões futuras.

A existência dessas fontes é premissa do produto. Formato, localização e acesso
técnico ainda não foram informados. Para demonstrar, podemos simular a fonte com
dados fictícios no mesmo contrato, sem afirmar que há uma conexão real pronta.
Detalhamento: [contexto e feedback](../integracoes/contexto-investidor.md).

### Fluxo e escopo

Transformar transcrições, e-mails, mensagens de WhatsApp Business e o formulário
inicial já existentes em contexto do investidor, lembranças pertinentes e pautas
de reunião. O assessor revisa as sugestões e fornece feedback que melhora a seleção futura.

**Fluxo que deve orientar a implementação:**

Receber dados existentes → extrair fatos e hipóteses com evidências → montar
contexto e sugestões → assessor aprova, corrige ou descarta → preparar contato
ou reunião → incorporar feedback e novas conversas.

| Primeiro recorte proposto | Evolução ou decisão pendente |
| --- | --- |
| Web responsiva para computador e celular | Aplicativo separado |
| Clientes e posições fictícios persistidos | Integração com sistemas financeiros |
| Consumo da fonte existente de transcrições, e-mails, WhatsApp Business e formulário | Construção dos sistemas de captura e do formulário, fora do escopo atual |
| Extração e inferência com evidências, contexto revisável e feedback | Respostas livres a perguntas, após definir limites e fontes |
| Alertas de vencimento e notícias pertinentes via NewsAPI; simulações identificadas para testes | Análises financeiras e tributárias aprofundadas |
| Preferências e avaliação do relacionamento | Gestão de vários assessores e acesso do investidor |
| Histórico importado, lembranças pessoais e próximos passos | Envio de atas ao investidor |
| Registro mínimo de reuniões e keynotes de preparação | Sincronização com calendários externos |

As funcionalidades à direita continuam na visão do produto. A equipe deve
decidir quais cabem no hackathon antes de incluí-las como compromisso de entrega.

## 2. Requisitos funcionais

| ID | Comportamento esperado | Como implementar — proposta | Aceite |
| --- | --- | --- | --- |
| RF01 | Listar clientes e buscar por nome | Consulta na API; lista com identidade, perfil e pendências; filtro por prioridade | CA01 |
| RF02 | Consultar o detalhe de um cliente | Recuperar perfil, objetivos, posições, preferências e registros pelo identificador do cliente | CA02 |
| RF03 | Ingerir interações existentes | Adaptador de leitura da fonte disponível; identificar cliente, canal, origem e versão; notas manuais são complemento | CA03, CA04, CA26 |
| RF04 | Consultar histórico cronológico | Ordenar por data da interação; mostrar canal, responsável e conteúdo; distinguir data da interação e do registro | CA02, CA03 |
| RF05 | Mostrar contexto extraído e inferido | Combinar formulário e conversas; separar fatos de hipóteses, exibir fontes, conflitos e revisão humana | CA11, CA27, CA28 |
| RF06 | Identificar vencimentos próximos ou passados | Comparar a data de vencimento com a data de referência; gerar indicação com prazo e origem | CA05 |
| RF07 | Relacionar eventos pessoais aos interesses | Associar assuntos estruturados a interesses revisados, respeitando preferência de contato | CA06, CA07 |
| RF08 | Mostrar prioridade de acompanhamento | Calcular a maior prioridade das pendências ativas e apresentar os motivos | CA01, CA12 |
| RF09 | Registrar avaliação do relacionamento | Estado positivo, negativo ou atenção, com justificativa, autor e histórico | CA09 |
| RF10 | Manter preferências de relacionamento | Extrair formulário/conversas e permitir confirmação ou correção; silêncio não equivale a aceitar assuntos pessoais | CA07, CA28 |
| RF11 | Marcar alerta como tratado | Persistir cliente, alerta, responsável e data; atualizar pendências sem apagar o histórico | CA08 |
| RF12 | Alternar visões | Lista, detalhe e reuniões próximas; calendário visual completo é expansão | CA10, CA12, CA19 |

### Conexão à fonte existente

- **RF16 — Conexão à fonte existente:** definir o contrato de leitura do local
  que já reúne as conversas e o formulário. Gravação/transcrição de chamadas,
  captura direta nos canais e criação do formulário ficam fora do recorte atual.

### Requisitos candidatos para extensão

- **RF13 — Atas:** gerar rascunho a partir de notas presenciais, permitir revisão
  e registrar o resultado do envio. Rascunho, aprovado e enviado são estados distintos.
- **RF14 — Risco e tributação:** exibir análises somente após definir dados,
  fontes, fórmulas e cenários de teste. Vencimento isolado não representa análise completa de risco.
- **RF15 — Perguntas iniciais:** definir público, perguntas atendidas e fontes
  permitidas antes de incluir um assistente de perguntas e respostas.

### Novos requisitos de busca definidos pela direção da equipe

- **RF17 — Notícias:** integrar NewsAPI.org por assunto compartilhado, com
  armazenamento de fonte, publicação e última coleta. Reutilizar resultados entre clientes.
- **RF18 — Atualização diária:** executar coleta agendada com deduplicação,
  cota controlada e manutenção do último resultado em caso de falha.
- **RF19 — Preparação de reunião:** antecipar coleta dos assuntos pertinentes
  quando uma reunião estiver próxima e o cache estiver antigo. Janelas propostas
  de 24h para reunião e 2h para cache ainda precisam de validação.
- **RF20 — Contexto rastreável:** exibir os artigos usados e distinguir atualização
  de busca de atualidade da notícia; o atraso depende do plano do NewsAPI.

Esses requisitos detalham a nova direção; agendamento e integração ainda não
foram implementados. Se usados, o papel e o provedor do especialista de IA
permanecem decisões pendentes.

### Preparação de reuniões — keynotes

**Keynotes** são uma pauta breve para o assessor consultar antes da reunião.
A ata registra o que ocorreu depois do encontro.

| ID | Comportamento esperado | Como implementar — proposta | Aceite |
| --- | --- | --- | --- |
| RF21 | Registrar reuniões | Cliente, responsável, objetivo, início/fuso e estado agendada/cancelada/concluída; permitir reagendamento | CA19, CA23 |
| RF22 | Preparar keynotes quando a reunião se aproxima | Disparo na janela configurada; reunir contexto, pendências e notícias filtradas | CA20, CA21 |
| RF23 | Consultar e revisar a pauta | Mostrar fontes e atualização; guardar observações do assessor separadas do conteúdo gerado | CA21, CA22 |
| RF24 | Registrar resultado da reunião | Criar interação vinculada, próximos passos e conclusão, sem duplicação por retry | CA24 |

Conteúdo proposto da pauta:

1. Objetivo, data e participantes registrados.
2. Resumo do cliente e objetivo financeiro conhecido.
3. Últimos combinados, dúvidas abertas e pontos de atenção do relacionamento.
4. Vencimentos e alertas com regras já validadas.
5. Até três notícias pertinentes com fonte/data e respeito às preferências pessoais.
6. Perguntas sugeridas e informações a confirmar, identificadas como sugestões.
7. Observações e prioridades anotadas pelo assessor.

Ausência de dados deve ser indicada. A pauta continua útil com informações
internas quando notícias ou IA estiverem indisponíveis.

### Extração, lembranças e aprendizado com revisão

| ID | Requisito | Implementação proposta | Aceite |
| --- | --- | --- | --- |
| RF25 | Consumir formulário existente | Ler campos/respostas e versões, preservando identificação e datas | CA26 |
| RF26 | Extrair e inferir contexto das fontes | Saída estruturada com categoria, valor, pessoa referida, evidência, validade e estado de revisão | CA27, CA28 |
| RF27 | Sugerir lembranças pertinentes | Datas, aniversários e combinados com destinatário correto, justificativa e validade | CA29 |
| RF28 | Submeter sugestões à decisão humana | Aprovar, editar, descartar ou adiar; correções geram histórico e não alteram a fonte original | CA30 |
| RF29 | Registrar feedback e aplicá-lo | Motivo e escopo por sugestão/assunto/cliente; reduzir repetição e ajustar seleção futura | CA31, CA32 |
| RF30 | Renovar contexto sem perder revisão | Processar novos registros, preservar correções e encaminhar contradições para revisão | CA28, CA33 |

RF25–RF30 complementam RF03/RF05/RF10 e constituem o núcleo do recorte revisado.

## 3. Regras da base e propostas de evolução

Síntese legível com OpenAI autorizada após a integração do painel:
[incremento SDD 04](incrementos/04-resumo-openai.md), RN40–RN45 e CA65–CA71.
Organiza fatos em Visão geral, Pontos de atenção e Antes do contato, com
fontes/cache e decisão final do assessor. Preserva RN08 e avaliações humanas.

As regras da base foram definidas pela equipe e estão em `spec.md`; não são regras dos organizadores. As regras de inferência, notícias e reuniões abaixo continuam propostas de implementação.

> **Decisões de 10/10/2026 que prevalecem** (detalhes em `spec.md` e
> `contracts.md`; RN11–RN15 e CA34–CA39 detalham a base): vencimento Δ 0–7 alta,
> 8–30 média, vencido alta (RN03/RN04); prioridade do cliente só pelos alertas
> pendentes, e relacionamento manual **não** altera prioridade (RN11);
> alertas calculados sob demanda com tratamento persistido (RN14/RN15);
> preferências canal/intervalo/permissão pessoal (RN13); `ocorrida_em` e
> `registrada_em` (RN02); assessor único sem autenticação, só local, sem `403`.

- **RN01/RN02:** interação exige cliente existente, canal válido e conteúdo;
  ordenação deve ter desempate estável. Importações futuras podem chegar fora de ordem.
- **RN03/RN04:** alerta até 30 dias; alta prioridade até 7 dias; limites inclusivos;
  vencidos permanecem de prioridade alta. Períodos definidos na base.
- **RN05:** evento deve ter origem, identificador, assunto e data. Janela de
  relevância, limite de alertas e validade do assunto precisam ser definidos.
- **RN06:** evento pessoal pode sugerir contato; mudanças no relacionamento
  exigem evidência. Não presumir humor nem modificar perfil financeiro por um resultado esportivo.
- **RN07:** avaliação exige justificativa e identificação do responsável.
- **RN08:** resumo aponta para registros de origem; dados ausentes ou antigos
  aparecem como tais. Novas interações tornam necessária sua atualização.
- **RN09:** alerta tratado sai das pendências, mas permanece consultável.
- **RN10:** informações persistem após recarregar e reiniciar a aplicação.
- **Prioridade da base (RN11/RN12):** alta para vencidos e vencimento em 0–7 dias;
  média para vencimento em 8–30 dias ou aniversário em 0–7 dias; sem pendências,
  baixa. A maior prioridade pendente prevalece; relacionamento manual não interfere.
- **Preferência pessoal (RN13):** exige permissão explícita e intervalo mínimo
  desde a última interação em qualquer canal (7, 14 ou 30 dias). Desativar a
  permissão oculta pendências pessoais, mantendo alertas financeiros. Sem histórico,
  o intervalo não bloqueia. Regras adicionais de feedback pertencem à evolução.
- **Deduplicação:** mesmo evento e mesma regra não devem gerar duas pendências
  para o mesmo cliente, inclusive se o processamento for repetido.
- **Pauta:** uma versão por reunião/conjunto de dados; repetir disparo sem
  mudanças reutiliza o resultado. Novos dados relevantes geram nova versão.
- **Notas manuais:** atualização preserva observações do assessor em campo separado.
  Uma pauta revisada deve sinalizar quando surgirem informações novas.
- **Reagendamento:** cancelar desativa disparos; reagendar recalcula a janela;
  concluir mantém o histórico e encerra a preparação automática.
- **Atualização interna:** nova interação pode renovar a pauta sem buscar novas
  notícias. Cache de notícias e versão da pauta têm controles independentes.
- **Evidência:** fato extraído tem trecho/campo de origem. Hipótese deve ser
  identificada e não vira fato confirmado apenas por pontuação do modelo.
- **Datas e sujeitos:** distinguir aniversário do cliente, familiar e outra pessoa.
  Expressões relativas usam data da conversa como referência; ambiguidades exigem revisão.
- **Supervisão:** sugestões podem aparecer na fila interna, mas envio externo e
  uso no contato dependem da decisão do assessor. Silêncio não é aprovação.
- **Feedback:** descartar uma notícia não remove automaticamente o interesse;
  o assessor escolhe o alcance da decisão. Ausência de clique não significa rejeição.
- **Correção:** informação nova que contradiz dado revisado vira pendência;
  reprocessamento não sobrescreve silenciosamente uma correção humana.

## 4. Requisitos não funcionais

| ID | Necessidade | Implementação e verificação propostas |
| --- | --- | --- |
| RNF01 | Persistência e integridade | Banco com vínculos e restrições; testar gravação e reabertura, incluindo erro sem registro parcial |
| RNF02 | Uso no celular | Layout responsivo; verificar fluxo a 360 px e desktop, com campos identificados e navegação por teclado |
| RNF03 | Custo controlado | Consultar assuntos compartilhados uma vez, usar cache e filtrar antes da IA; contar chamadas e registrar limites |
| RNF04 | Privacidade | Dados fictícios na demo; minimizar conteúdo; evitar dados pessoais nos logs; definir finalidade, acesso e retenção antes de uso real |
| RNF05 | Acesso por cliente | Se houver usuários reais, validar autorização no backend em leitura e escrita; um filtro de interface não basta |
| RNF06 | Transparência | Identificar fontes, atualização, eventos simulados e falhas de consulta; não mostrar dado antigo como atualizado |
| RNF07 | Reprodução | Documentar versões, configuração, carga inicial, execução e verificações com comandos realmente testados |

Esses requisitos orientam o desenvolvimento. A conformidade com a LGPD depende
de validação específica; esta documentação não a declara atendida.

## 5. Etapas de implementação

### Etapa 0 — Fechar decisões e contratos

**Fazer:** definir o contrato da fonte existente e a identificação de clientes;
definir recorte de evolução, dados de demonstração e responsabilidades. Stack,
períodos de alertas, fuso `America/Sao_Paulo` e contratos da base já estão definidos
em `spec.md`, `design.md` e `contracts.md`. Contratos de importação e revisão ainda precisam ser fechados.

**Saída:** especificação revisada e contratos curtos para cliente, interação e alerta.
**Condição para avançar:** todos sabem qual fluxo será demonstrado e como verificar.

### Etapa 1 — Preparar ambiente e persistência

**Base integrada:** Python 3.13 + Flask + SQLite, gerenciados com `uv`;
interface React/TypeScript/Tailwind em `frontend/`, build Vite via Node.js.
Ambiente, schema e seed fictício já existem. Node é ferramenta da interface,
não segundo backend; interface JS anterior permanece em `/legacy`.

**Dados da base:** assessor, cliente/preferências, posição, interação, data
importante, avaliação e tratamento de alerta. Alertas são calculados sob demanda;
não há tabela de alertas. Dinheiro usa Decimal/texto.

**Dados adicionais planejados:** documento de origem, formulário versionado,
extração, feedback, lembrança, interesse/vínculo, evento, reunião e pauta versionada.
Detalhar schema e migração antes de implementar; não misturar sugestão inferida
com o tratamento dos alertas da base.

**Validar:** iniciar em outra máquina, carregar dados sem duplicação e testar
vínculos inválidos. Configuração e credenciais ficam fora do Git.
**Entrega:** dados consultáveis pela API e instruções reais de execução.

### Etapa 2 — Integrar lista e detalhe

**Fazer:** implementar RF01/RF02 e a primeira tela adaptada ao celular. Mostrar
estados de carregamento, ausência de resultados e erro. Combinar prioridade
calculada pelo motor de alertas da base (RN11).

**Validar:** busca, abertura do cliente correto e isolamento dos registros exibidos.
**Entrega:** primeiro fluxo completo de consulta, integrado cedo.

### Etapa 3 — Consumir as fontes existentes

Primeiro incremento implementado: importação JSON fictícia, versões,
identidade/pendências e histórico. Contrato interno e testes em
[incremento SDD 01](incrementos/01-fontes.md). O acesso à fonte real permanece pendente.

**Fazer:** implementar RF03/RF04/RF16/RF25. Ler a fonte por adaptador, validar
identificação do cliente e manter origem, data e versão. Importação incremental
e idempotente deve evitar duplicação. Separar registros de identidade ambígua
para revisão, sem atribuir conversas por semelhança de nomes.

**Validar:** identidade ausente/ambígua, versão repetida ou corrigida, canal inválido,
datas inválidas e persistência após recarregar. Dados inválidos ficam sinalizados
sem contaminar o contexto confirmado.
**Entrega:** formulário e histórico existentes consultáveis por cliente, com origem rastreável.

### Etapa 4 — Extrair contexto, propor lembranças e receber feedback

**Fazer:** implementar RF05/RF09/RF10/RF26–RF30. Extrair informações estruturadas
com referência ao trecho de origem; classificar fatos, hipóteses e conflitos.
Sugerir interesses, datas, compromissos e preferências para revisão. Processar
novas versões dos dados e preservar correções humanas. Gemini e revisão
implementados no [incremento 02](incrementos/02-contexto-revisao.md); testes com
simulação não comprovam qualidade do modelo. Na indisponibilidade, manter contexto
anterior e sinalizar que os novos registros aguardam processamento.

**Validar:** fonte correta, negação, terceiros, aniversário ambíguo, conflitos,
correção humana preservada e feedback com alcance explícito. Alteração de estado
sem justificativa é recusada.
**Entrega:** contexto inferido revisável, fila de sugestões e feedback persistido.

### Etapa 5 — Implementar alertas financeiros

**Fazer:** implementar RF06/RF08/RF11 com uma função de regra independente da
interface. Usar data de referência controlável nos testes e identificador estável
por posição/regra. Separar conteúdo do alerta, prioridade e estado de tratamento.

**Validar:** ontem, hoje, 7, 8, 30 e 31 dias; posição sem data; limites de mês/ano;
alerta tratado persiste e não reaparece apenas por recarga.
**Entrega:** vencimentos com motivo, prioridade e ação de acompanhamento.

### Etapa 6 — Associar eventos pessoais sem aumentar custos por cliente

**Fazer:** implementar RF07. Receber um evento, normalizar assunto, verificar
unicidade, encontrar clientes interessados, aplicar preferências e gerar alertas.
Usar evento fictício identificado para validar o fluxo antes de uma fonte real.

Para a fonte escolhida, implementar RF17–RF20 conforme `../integracoes/busca-noticias.md`:
coleta por assunto, cache e orçamento, atualização diária e antecipação por
reunião. Registrar reunião/data/estado para sustentar o novo gatilho.

**Validar:** repetir o processamento, evento sem interessados, preferência
desativada, evento fora da janela e fonte indisponível. Um evento compartilhado
deve alcançar vários clientes sem uma consulta externa por cliente.
**Entrega:** oportunidade pertinente com fonte; sem alteração automática do perfil financeiro.

### Etapa 7 — Preparar reuniões e keynotes

**Fazer:** implementar RF21–RF24. Criar registro mínimo de reunião e lista das
próximas reuniões. O agendador identifica a janela; o backend reúne contexto,
verifica cache de notícias e prepara tópicos com fontes. Uma estrutura
determinística atende ao primeiro fluxo; IA opcional pode ajudar na redação.

Persistir reunião, versão dos dados, fontes, pauta gerada, observações manuais,
data de geração e revisão. Ao concluir o encontro, registrar interação vinculada
e próximos passos, preservando a pauta utilizada.

**Validar:** reunião próxima, distante, cancelada e reagendada; alteração de
interação; cache recente; falha externa; notas preservadas e cliente correto.
**Entrega:** o assessor abre a reunião, revisa a pauta e registra o resultado.

### Etapa 8 — Integrar, revisar e entregar

**Fazer:** combinar visualizações, revisar critérios, resolver impedimentos do
fluxo completo, atualizar instruções e preparar pitch de até 5 minutos.

**Validar:** executar em outra máquina ou instalação limpa, testar celular,
registrar interação, recarregar, tratar alerta, repetir processamento de evento
e preparar/concluir uma reunião.
**Entrega:** demonstração reproduzível e código enviado antes da clonagem às 17h30.

## 6. API implementada e extensões propostas

A base tem as seis rotas abaixo. Histórico, resumo e alertas vêm no detalhe do
cliente; não existem rotas separadas para essas consultas. Extensões posteriores
precisam de contrato aprovado e não são endpoints disponíveis hoje.

> Os caminhos e formatos efetivos do MVP estão em [contracts.md](contracts.md)
> (`/api/...`, JSON, tratamento por `chave_ocorrencia`, sem `403`).

| Operação | Rota implementada | Resultado |
| --- | --- | --- |
| Listar clientes | GET /api/clientes, com busca e filtro | Identidade, perfil, prioridade e contagem de pendências |
| Consultar cliente | GET /api/clientes/{id} | Perfil, preferências, resumo e fontes |
| Gravar interação | POST /api/clientes/{id}/interacoes | Confirmação com identificador; histórico no detalhe |
| Alterar preferências | PATCH /api/clientes/{id}/preferencias | Preferências atualizadas |
| Avaliar relacionamento | POST /api/clientes/{id}/relacionamento | Avaliação com justificativa e autoria |
| Tratar alerta | POST /api/alertas/tratar | Recebe cliente_id e chave_ocorrencia; repetir mantém o resultado |

**Extensões propostas, não implementadas:**

| Operação | Caminho ilustrativo a definir | Resultado |
| --- | --- | --- |
| Receber evento | POST /events | Evento persistido; duplicata reconhecida |
| Listar/agendar reuniões | GET/POST /meetings | Cliente, início, objetivo e estado |
| Reagendar/cancelar | PATCH /meetings/{id} | Estado/data atualizados e disparos reconciliados |
| Consultar pauta | GET /meetings/{id}/brief | Pauta, fontes, versão e atualização |
| Preparar/atualizar pauta | POST /meetings/{id}/brief/refresh | Resultado reutilizado, atualizado ou estado de processamento |
| Revisar observações | PATCH /meetings/{id}/brief/notes | Notas do assessor preservadas separadamente |
| Concluir encontro | POST /meetings/{id}/complete | Interação vinculada e reunião concluída em operação idempotente |
| Sincronizar fonte existente | POST /source-syncs | Resultado/estado da ingestão incremental, controlada no backend |
| Consultar contexto | GET /clients/{id}/context | Fatos, hipóteses, fontes, conflitos e revisão |
| Consultar sugestões | GET /clients/{id}/suggestions | Lembranças e inferências com justificativa e estado |
| Revisar sugestão | POST /clients/{id}/suggestions/{suggestionId}/feedback | Ação, correção/motivo e alcance persistidos |

Definir antes de implementar: representação de valores, datas, identificadores,
paginação se necessária e respostas para entrada inválida e ausência. Acesso
negado só se aplica quando autenticação/autorização forem implementadas; a base
local não tem `403`. Os caminhos ilustrativos de extensões devem ser alinhados
aos nomes em português dos contratos atuais antes da implementação.

## 7. Aceite e plano de testes

CA01–CA10 e CA34–CA39 estão em `spec.md`. CA06 e os cenários de importação,
notícias, reuniões e lembretes derivados ainda dependem da evolução. Fontes e
contexto/revisão têm CA40–CA56 nos incrementos; testes simulados não comprovam
qualidade do modelo real. CA26–CA33 publicados na main foram
preservados; critérios da branch com IDs coincidentes passaram para CA34–CA39.
Complementos:

- **CA11:** ao ingerir nova conversa, o resumo atualizado mostra o novo registro como fonte;
  não inclui informações de outro cliente e sinaliza dados ausentes.
- **CA12:** ao tratar a última pendência alta, filtros, contagens e prioridade
  do cliente são recalculados conforme as pendências restantes.
- **CA13:** repetir o mesmo evento mantém apenas um alerta correspondente por cliente.
- **CA14:** preferências financeiras exclusivas retiram sugestões pessoais das pendências.
- **CA15:** falha ao salvar mostra erro e preserva o texto para nova tentativa.
- **CA16:** clientes com o mesmo assunto reutilizam a coleta do NewsAPI.
- **CA17:** reunião próxima com cache recente reutiliza dados; com cache antigo
  solicita atualização dentro da cota e sem disparos concorrentes duplicados.
- **CA18:** erro/cota esgotada preserva fontes anteriores, sinalizando que a
  atualização falhou. Ver cenários BN01–BN10 em `../integracoes/busca-noticias.md`.
- **CA19:** reunião cadastrada aparece no cliente e na lista de reuniões próximas,
  com data/fuso corretos; entradas inválidas são recusadas.
- **CA20:** reunião agendada dentro da janela recebe pauta do cliente correto;
  reunião distante não dispara preparação antecipada.
- **CA21:** fatos da pauta têm fonte; perguntas são identificadas como sugestões;
  dados ausentes não geram afirmações inventadas.
- **CA22:** atualizar após nova interação preserva notas manuais; com os mesmos
  dados reutiliza o resultado e evita chamadas desnecessárias.
- **CA23:** cancelamento impede novos disparos; reagendamento recalcula a janela
  sem duplicar processamento.
- **CA24:** concluir uma reunião registra uma única interação vinculada, persiste
  próximos passos e mantém a pauta usada como histórico.
- **CA25:** falha de notícias/IA mantém a pauta com contexto interno e sinaliza
  quais informações não puderam ser atualizadas.
- **CA26:** reimportar a mesma origem/versão não duplica interações ou formulário;
  fonte sem identificação segura de cliente fica pendente, sem associação automática.
- **CA27:** cada informação extraída aponta para evidência do cliente correto;
  inferências aparecem como hipóteses, sem inventar campos ausentes.
- **CA28:** conflito entre formulário, conversa ou correção humana é sinalizado;
  confiança alta de IA não substitui revisão.
- **CA29:** uma data de familiar não aparece como aniversário do investidor;
  datas ambíguas não viram lembrete confirmado.
- **CA30:** sugestão pode ser aprovada, editada, adiada ou descartada; ações são
  persistidas e não causam envio automático ao investidor.
- **CA31:** feedback de notícia irrelevante reduz sua repetição sem apagar o
  interesse; bloqueio de assunto só afeta o alcance explicitamente escolhido.
- **CA32:** bloquear um assunto para um cliente não afeta outros; ausência de
  resposta não é contabilizada como aprovação nem rejeição.
- **CA33:** reprocessar as mesmas fontes preserva correções; evidência nova e
  conflitante gera revisão e atualiza o indicador de atualidade da pauta.

**TDD por tarefa:** derivar cenários do requisito → escrever teste → revisar
resultado esperado → observar falha pelo motivo correto → implementar → executar
testes relevantes → revisar diff. Testes de integração devem demonstrar persistência
e restrições reais; testes unitários não substituem essa evidência.

## 8. Divisão e ordem de integração

| Frente | Responsabilidade inicial | Primeiro ponto de integração |
| --- | --- | --- |
| Pessoa 1 | Requisitos, contratos e roteiro; depois apoio em testes | Especificação e casos de aceite |
| Pessoa 2 | Adaptador da fonte, identidade, persistência e API | Formulário e conversas consultáveis |
| Pessoa 3 | Vencimentos, NewsAPI, cache e testes | Dados de posições, interesses e preferências |
| Pessoa 4 | Lista, detalhe, pauta e telas responsivas | Primeiro fluxo de consulta |
| Pessoa 5 | Extração de contexto, lembranças e feedback | Evidências da fonte e revisão na interface |
| Pessoa 6 | Integração, preparação de keynotes e revisão | Ambiente reproduzível e contrato de contexto/reunião |

Os números são espaços para atribuição, não membros já definidos. Combinar
arquivos/áreas e contratos antes de trabalhar em paralelo. Integrar a consulta
primeiro, depois escrita e resumo, depois alertas e preparação de reunião.
Cada pessoa valida sua entrega.

## 9. Prioridade no prazo

As 6h30 são a duração informada originalmente, não uma medição do tempo restante.
Usar o cronograma de `tasks.md` como referência e recalibrar ao horário real.

Se for necessário cortar: agenda extra, aplicativo separado, integrações de canais
e IA generativa são candidatos antes de comprometer o fluxo demonstrável.

**Pronto para apresentar:** cliente consultável, fonte explicável, interação
importada, sugestão com evidência e revisão, feedback aplicado, alerta demonstrável,
pauta com fontes, limitações registradas e execução reproduzível.
