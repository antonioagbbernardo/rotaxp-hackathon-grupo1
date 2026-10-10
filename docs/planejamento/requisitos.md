# Requisitos e etapas de implementação do MVP

**Status:** planejamento para revisão da equipe; somente documentação nesta etapa.
**Referências:** [especificação](spec.md), [arquitetura](design.md) e [tarefas](tasks.md).
**Usuário principal proposto:** assessor de investimentos.
**Revisado em:** 10/10/2026. Inclui preparação de reunião (keynotes).

**Decisão posterior da equipe:** usar NewsAPI.org para notícias, com atualização
diária e possibilidade de atualização antecipada por reunião próxima. Política
de cache, limites e papel opcional de IA em [busca-noticias.md](../integracoes/busca-noticias.md).

## 1. Objetivo e recorte

Reunir o contexto financeiro e de relacionamento de cada investidor para o
assessor identificar prioridades, entender os motivos e registrar o próximo contato.

**Fluxo que deve orientar a implementação:**

Selecionar cliente → consultar contexto → analisar alertas → preparar reunião
com keynotes → registrar resultado e próximo passo → conferir o histórico.

| Primeiro recorte proposto | Evolução ou decisão pendente |
| --- | --- |
| Web responsiva para computador e celular | Aplicativo separado |
| Clientes e posições fictícios persistidos | Integração com sistemas financeiros |
| Registro manual dos quatro canais | Captura real de WhatsApp, e-mail e telefone |
| Resumo factual com evidências | Síntese por IA e respostas a perguntas iniciais |
| Alertas de vencimento e notícias pertinentes via NewsAPI; simulações identificadas para testes | Análises financeiras e tributárias aprofundadas |
| Preferências e avaliação do relacionamento | Gestão de vários assessores e acesso do investidor |
| Histórico e próximos passos | Revisão e envio de atas ao investidor |
| Registro mínimo de reuniões e keynotes de preparação | Sincronização com calendários externos |

As funcionalidades à direita continuam na visão do produto. A equipe deve
decidir quais cabem no hackathon antes de incluí-las como compromisso de entrega.

## 2. Requisitos funcionais

| ID | Comportamento esperado | Como implementar — proposta | Aceite |
| --- | --- | --- | --- |
| RF01 | Listar clientes e buscar por nome | Consulta na API; lista com identidade, perfil e pendências; filtro por prioridade | CA01 |
| RF02 | Consultar o detalhe de um cliente | Recuperar perfil, objetivos, posições, preferências e registros pelo identificador do cliente | CA02 |
| RF03 | Registrar uma interação | Formulário com canal, conteúdo e próximos passos opcionais; validar no backend e persistir | CA03, CA04 |
| RF04 | Consultar histórico cronológico | Ordenar por data da interação; mostrar canal, responsável e conteúdo; distinguir data da interação e do registro | CA02, CA03 |
| RF05 | Mostrar resumo da situação atual | Organizar objetivo, última interação, pendências e avaliação em campos com fontes e atualização | CA11 |
| RF06 | Identificar vencimentos próximos ou passados | Comparar a data de vencimento com a data de referência; gerar indicação com prazo e origem | CA05 |
| RF07 | Relacionar eventos pessoais aos interesses | Associar assuntos estruturados a interesses revisados, respeitando preferência de contato | CA06, CA07 |
| RF08 | Mostrar prioridade de acompanhamento | Calcular a maior prioridade das pendências ativas e apresentar os motivos | CA01, CA12 |
| RF09 | Registrar avaliação do relacionamento | Estado positivo, negativo ou atenção, com justificativa, autor e histórico | CA09 |
| RF10 | Manter preferências de relacionamento | Registrar canais, frequência e abertura a assuntos pessoais; permitir revisão | CA07 |
| RF11 | Marcar alerta como tratado | Persistir cliente, alerta, responsável e data; atualizar pendências sem apagar o histórico | CA08 |
| RF12 | Alternar visões | Lista, detalhe e reuniões próximas; calendário visual completo é expansão | CA10, CA12, CA19 |

### Requisitos candidatos para extensão

- **RF13 — Atas:** gerar rascunho a partir de notas presenciais, permitir revisão
  e registrar o resultado do envio. Rascunho, aprovado e enviado são estados distintos.
- **RF14 — Risco e tributação:** exibir análises somente após definir dados,
  fontes, fórmulas e cenários de teste. Vencimento isolado não representa análise completa de risco.
- **RF15 — Perguntas iniciais:** definir público, perguntas atendidas e fontes
  permitidas antes de incluir um assistente de perguntas e respostas.
- **RF16 — Integrações:** definir API e condições de acesso de cada canal;
  importação deve identificar origem e evitar registros repetidos.

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

## 3. Regras a validar com a equipe

As seguintes regras são **propostas de implementação**, não regras dos organizadores.
Os identificadores RN01–RN10 seguem `spec.md`.

> **Decisões de 10/10/2026 que prevalecem** (detalhes em `spec.md` e
> `contracts.md`; RN11–RN15 e CA26–CA31 são novos): vencimento Δ 1–7 alta,
> 8–30 média, vencido alta (RN03/RN04); prioridade do cliente só pelos alertas
> pendentes, e relacionamento manual **não** altera prioridade (RN11);
> alertas calculados sob demanda com tratamento persistido (RN14/RN15);
> preferências canal/intervalo/permissão pessoal (RN13); `ocorrida_em` e
> `registrada_em` (RN02); assessor único sem autenticação, só local, sem `403`.
> Os itens "Prioridade proposta", "Preferência pessoal" e "Deduplicação" abaixo
> ficam como contexto histórico onde divergirem.

- **RN01/RN02:** interação exige cliente existente, canal válido e conteúdo;
  ordenação deve ter desempate estável. Importações futuras podem chegar fora de ordem.
- **RN03/RN04:** alerta até 30 dias; alta prioridade até 7 dias; limites inclusivos;
  vencidos aparecem separadamente. Os dois períodos precisam de confirmação.
- **RN05:** evento deve ter origem, identificador, assunto e data. Janela de
  relevância, limite de alertas e validade do assunto precisam ser definidos.
- **RN06:** evento pessoal pode sugerir contato; mudanças no relacionamento
  exigem evidência. Não presumir humor nem modificar perfil financeiro por um resultado esportivo.
- **RN07:** avaliação exige justificativa e identificação do responsável.
- **RN08:** resumo aponta para registros de origem; dados ausentes ou antigos
  aparecem como tais. Novas interações tornam necessária sua atualização.
- **RN09:** alerta tratado sai das pendências, mas permanece consultável.
- **RN10:** informações persistem após recarregar e reiniciar a aplicação.
- **Prioridade proposta:** alta para vencidos, vencimento em até 7 dias ou
  relacionamento negativo; média para vencimento de 8 a 30 dias ou atenção;
  baixa para oportunidade pessoal. Cada cliente assume a maior prioridade ativa.
- **Preferência pessoal:** desativar sugestões pessoais deve impedir novas
  sugestões e retirar as já existentes das pendências de contato pessoal.
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

**Fazer:** escolher stack, recorte, períodos dos alertas, níveis de prioridade,
dados fictícios e responsabilidades. Definir campos compartilhados pela API e
interface, formato dos erros e fuso de referência (`America/Sao_Paulo`, proposto).

**Saída:** especificação revisada e contratos curtos para cliente, interação e alerta.
**Condição para avançar:** todos sabem qual fluxo será demonstrado e como verificar.

### Etapa 1 — Preparar ambiente e persistência

**Fazer:** criar base executável, configuração local, schema/migrations e carga
de dados fictícios. Usar um único backend. React, Python e Node.js são candidatos;
uma combinação ainda não foi aprovada. Banco SQL é a proposta inicial.

**Dados mínimos:** cliente, posição, interação, interesse/vínculo com cliente,
preferência, evento, alerta, reunião, pauta versionada e histórico de avaliação. Persistir dinheiro em
centavos ou tipo decimal apropriado, com unidade definida no contrato.

**Validar:** iniciar em outra máquina, carregar dados sem duplicação e testar
vínculos inválidos. Configuração e credenciais ficam fora do Git.
**Entrega:** dados consultáveis pela API e instruções reais de execução.

### Etapa 2 — Integrar lista e detalhe

**Fazer:** implementar RF01/RF02 e a primeira tela adaptada ao celular. Mostrar
estados de carregamento, ausência de resultados e erro. Combinar prioridade
provisória até o motor de alertas estar integrado.

**Validar:** busca, abertura do cliente correto e isolamento dos registros exibidos.
**Entrega:** primeiro fluxo completo de consulta, integrado cedo.

### Etapa 3 — Registrar interações e preferências

**Fazer:** implementar RF03/RF04/RF10. Separar validação da interface e validação
obrigatória no backend. Definir limites de conteúdo e impedir envio repetido
enquanto salva; se houver retries, avaliar chave de operação no backend.

**Validar:** sucesso, conteúdo vazio, canal inválido, cliente inexistente,
datas inválidas e persistência após recarregar. Preferências alteradas precisam
afetar as sugestões pessoais.
**Entrega:** histórico utilizável com registro e próximo passo.

### Etapa 4 — Construir resumo e avaliação

**Fazer:** implementar RF05/RF09. Primeiro construir resumo determinístico a
partir dos dados; atualizar após nova interação. Manter histórico das avaliações.
Se a equipe escolher IA, adicioná-la atrás de uma interface substituível, com
cache por versão dos registros e retorno factual em caso de indisponibilidade.

**Validar:** resumo só usa fontes do cliente, evidencia atualização e não inventa
informações. Alteração de estado sem justificativa é recusada.
**Entrega:** contexto explicável e avaliação rastreável.

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

## 6. Contrato de API sugerido

Este contrato descreve responsabilidades; os caminhos podem ser ajustados em equipe.

> Os caminhos e formatos efetivos do MVP estão em [contracts.md](contracts.md)
> (`/api/...`, JSON, tratamento por `chave_ocorrencia`, sem `403`).

| Operação | Proposta | Resultado |
| --- | --- | --- |
| Listar clientes | GET /clients, com busca e filtro | Identidade, perfil, prioridade e contagem de pendências |
| Consultar cliente | GET /clients/{id} | Perfil, preferências, resumo e fontes |
| Consultar/gravar interações | GET/POST /clients/{id}/interactions | Histórico ou confirmação com identificador do registro |
| Alterar preferências | PATCH /clients/{id}/preferences | Preferências atualizadas |
| Avaliar relacionamento | POST /clients/{id}/relationship-evaluations | Avaliação com justificativa e autoria |
| Consultar alertas | GET /clients/{id}/alerts | Motivos, prioridades, fontes e estados |
| Tratar alerta | PATCH /clients/{id}/alerts/{alertId} | Estado atualizado; repetir mantém o resultado |
| Receber evento | POST /events | Evento persistido; duplicata reconhecida |
| Listar/agendar reuniões | GET/POST /meetings | Cliente, início, objetivo e estado |
| Reagendar/cancelar | PATCH /meetings/{id} | Estado/data atualizados e disparos reconciliados |
| Consultar pauta | GET /meetings/{id}/brief | Pauta, fontes, versão e atualização |
| Preparar/atualizar pauta | POST /meetings/{id}/brief/refresh | Resultado reutilizado, atualizado ou estado de processamento |
| Revisar observações | PATCH /meetings/{id}/brief/notes | Notas do assessor preservadas separadamente |
| Concluir encontro | POST /meetings/{id}/complete | Interação vinculada e reunião concluída em operação idempotente |

Definir antes de implementar: representação de valores, datas, identificadores,
paginação se necessária e respostas para entrada inválida, ausência e acesso negado.

## 7. Aceite e plano de testes

CA01–CA10 estão em `spec.md`. Complementos propostos:

- **CA11:** ao registrar nova conversa, o resumo mostra o novo registro como fonte;
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

**TDD por tarefa:** derivar cenários do requisito → escrever teste → revisar
resultado esperado → observar falha pelo motivo correto → implementar → executar
testes relevantes → revisar diff. Testes de integração devem demonstrar persistência
e restrições reais; testes unitários não substituem essa evidência.

## 8. Divisão e ordem de integração

| Frente | Responsabilidade inicial | Primeiro ponto de integração |
| --- | --- | --- |
| Pessoa 1 | Requisitos, contratos e roteiro; depois apoio em testes | Especificação e casos de aceite |
| Pessoa 2 | API de consulta e persistência | Lista e detalhe com pessoa 4 |
| Pessoa 3 | Vencimentos, NewsAPI, cache e testes | Dados de posições, interesses e preferências |
| Pessoa 4 | Lista, detalhe, pauta e telas responsivas | Primeiro fluxo de consulta |
| Pessoa 5 | Interações, preferências, avaliação e cadastro de reunião | Formulários com gravação e leitura |
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
persistida, alerta demonstrável, pauta com fontes, limitações registradas e execução reproduzível.
