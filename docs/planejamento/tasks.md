# Plano de execução — seis pessoas

Status: plano reconciliado em 10/10/2026. React XP Pulse integrado ao Flask/SQLite;
ingestão JSON fictícia e contexto/revisão implementados; Gemini real testado em
amostra fictícia. Conexão aos canais, notícias e keynotes ainda pendentes.
Referências: `spec.md`, `design.md`,
`requisitos.md`, `contracts.md`. Responsáveis definidos pela equipe.

## Sequência de trabalho

| Tarefa | Resultado verificável | Depende de | Aceite | Responsável |
| --- | --- | --- | --- | --- |
| T00 — Contratos | `contracts.md` fechado (campos, rotas, erros, formatos); stack e responsáveis registrados; `Clock` e seed relativo definidos; primeiro lote de testes (vencimento, `Clock`, identidade e persistência do tratamento, permissões pessoais) escrito antes das rotas | Equipe (≤ 20 min, testes em seguida) | CA05, CA07, CA38 | Líder técnico + backend + frontend |
| T01 — Base | Projeto roda em ≥ 2 máquinas com lockfile; banco, assessor e clientes fictícios persistidos; seed idempotente e reset explícito | T00 | CA02, CA38 | Pessoa 2 |
| T02 — Consulta | Lista (busca, filtro, ordenação) abre detalhe com dados da base | T00 (usar contrato/seed enquanto T01 termina) | CA01, CA02, CA10 | Pessoas 2 e 4 |
| T03 — Histórico | Registrar interação (`ocorrida_em` e `registrada_em`) e consultar após recarregar | T00 | CA03, CA04, CA36 | Pessoa 5 |
| T04 — Alertas e prioridade | Alertas calculados sob demanda, tratamento persistido, RN11 e resumo com fontes (RN08) | T00 | CA05, CA07, CA08, CA34, CA35, CA37, CA39 | Pessoa 3 |
| T05 — Relacionamento | Preferências (RN13) e avaliação com justificativa, responsável e data | T00 | CA07, CA09 | Pessoas 4 e 5 |
| T09 — Fonte, inferência e feedback | Formulário/conversas importados com identidade, contexto com evidências, revisão e efeito do feedback | T00–T05; contrato da fonte | CA26–CA33 | Pessoas 2, 4 e 5 (atribuição a confirmar) |
| T08 — Notícias, reuniões e keynotes | Reunião agendada com pauta, fontes, notas preservadas e conclusão; NewsAPI com cache | T01–T05; contratos em T00 | CA16–CA25 | Pessoas 3, 4, 5 e 6 |
| T06 — Integração | Fluxo completo revisado, inclusive falhas e celular | T01–T05, T08 e T09 | Todos | Pessoa 6 + autores |
| T07 — Entrega | README testado em clone limpo, pitch ≤ 5 min, push | T06 | Demo reproduzível | Pessoas 1 e 6 + equipe |
| Opcional | Eventos externos/simulados (CA06) | T06 concluída | CA06 | Quem estiver livre |

Pessoa 1 mantém a especificação e apoia testes. Pessoa 6 integra desde a base.
Cada autor verifica sua entrega. Quem escreve não revisa o próprio trabalho.
Implementação paralela após T00: integrar assim que a base permitir, sem manter
duas implementações incompatíveis.

## Cronograma de referência — 10/10/2026 (São Paulo)

T09 dividida em incrementos SDD:

- **T09.1 — implementado:** fonte JSON fictícia, identidade/pendências, histórico,
  versões e tela de fontes. CA40–CA46 automatizados; CA47 visual parcial, fluxo
  completo e celular pendentes.
- **T09.2/T09.3 — implementados no incremento 02:** extração estruturada,
  evidências, fatos/hipóteses, revisão, correções e bloqueio por cliente, sem
  perder decisões. 125 testes aprovados com provedor/transporte simulados;
  chamada real com quatro fontes/sete propostas e cache verificado.
  Fluxos principais passaram a ser conferidos no painel React do incremento 03;
  cobertura visual e limites no registro abaixo.

- **T06 — incremento 03 implementado:** layout React com dados/IDs da API,
  revisão, bloqueio, alertas, contatos, relacionamento, preferências e consulta
  por templates. 143 testes backend, cinco frontend, build/lint; navegador
  desktop e viewport móvel de 390 × 844. T08 permanece pendente.

Detalhes em [incremento 01](incrementos/01-fontes.md) e
[registro para apresentação](../registro-desenvolvimento.md).

Horários herdados do plano da branch; ajustar ao tempo realmente restante.
A integração da base não comprova execução em duas máquinas nem conclusão
de T08/T09. O fluxo alvo e suas prioridades são os definidos em requisitos.

| Horário | Entrega |
| --- | --- |
| 11h20–11h40 | T00: contratos, regras, stack e responsáveis |
| 11h40–12h30 | Base executável, banco e dados fictícios |
| 12h30–14h40 | Implementação paralela com integrações frequentes |
| 14h40–15h45 | Integração completa e testes |
| 15h45–16h20 | Correções, experiência de uso e demonstração |
| 16h20–16h45 | README, ensaio e verificação do fluxo em clone limpo |
| 16h45 | Primeiro push da versão final candidata |
| 17h00 | Congelamento definitivo do código |
| 17h00–17h15 | Conferência do commit remoto e da demonstração |
| 17h30 | Clone previsto pela organização |

Depois das 17h não assumir que alterações serão aceitas. Falha crítica antes do
congelamento: corrigir, testar e enviar até o limite. Um representante confirma
com a organização o horário do pitch e se o código pode mudar após o clone; o
plano não depende da resposta (apresentação pronta até 17h).

## SDD e TDD

Registrar regra e critério de aceite antes do código. Escrever e revisar testes
de comportamento, observar a falha esperada, implementar e rodar novamente. Não
alterar um resultado correto só para passar. Priorizar limites de vencimento
(0, 7, 8, 30, 31, vencido), prioridade (RN11), aniversário e permissão,
idempotência de alertas e persistência. Fluxo completo e celular na integração.

## Roteiro da demonstração (≤ 5 min)

1. Problema e quem é impactado; como é hoje.
2. Lista priorizada e resumo com fontes da base. Quando T09 estiver pronta,
   mostrar origem existente, inferência, correção e efeito do feedback.
3. Vencimento (alta) e aniversário (média, respeitando permissão).
4. Se T08 estiver pronta, abrir keynotes e revisar fontes; caso contrário,
   apresentar como evolução planejada.
5. Registrar o resultado, tratar alerta e ver prioridade/histórico atualizados.
6. Privacidade (dados fictícios), custo, limitações, benefícios e evolução.

## Quando faltar tempo

Preservar o ciclo central esclarecido pelo usuário: fonte existente → contexto
com evidências → revisão/feedback. Reduzir visualizações extras, polimento,
quantidade de assuntos/notícias e escopo da pauta antes de descartar esse ciclo.
Uma fonte fictícia pode demonstrar o contrato sem conexão real. Não cortar
persistência, regras essenciais ou validação. Nunca apresentar T08/T09 como prontas
apenas porque a base manual já funciona.
