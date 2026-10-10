# Plano de execução — seis pessoas

Status: plano adotado em 10/10/2026. Referências: `spec.md`, `design.md`,
`contracts.md`. Responsáveis definidos pela equipe.

## Sequência de trabalho

| Tarefa | Resultado verificável | Depende de | Aceite | Responsável |
| --- | --- | --- | --- | --- |
| T00 — Contratos | `contracts.md` fechado (campos, rotas, erros, formatos); stack e responsáveis registrados; `Clock` e seed relativo definidos; primeiro lote de testes (vencimento, `Clock`, identidade e persistência do tratamento, permissões pessoais) escrito antes das rotas | Equipe (≤ 20 min, testes em seguida) | CA05, CA07, CA15 | Líder técnico + backend + frontend |
| T01 — Base | Projeto roda em ≥ 2 máquinas com lockfile; banco, assessor e clientes fictícios persistidos; seed idempotente e reset explícito | T00 | CA02, CA15 | Pessoa 2 |
| T02 — Consulta | Lista (busca, filtro, ordenação) abre detalhe com dados da base | T00 (usar contrato/seed enquanto T01 termina) | CA01, CA02, CA10 | Pessoas 2 e 4 |
| T03 — Histórico | Registrar interação (`ocorrida_em` e `registrada_em`) e consultar após recarregar | T00 | CA03, CA04, CA13 | Pessoa 5 |
| T04 — Alertas e prioridade | Alertas calculados sob demanda, tratamento persistido, RN11 e resumo com fontes (RN08) | T00 | CA05, CA07, CA08, CA11, CA12, CA14, CA16 | Pessoa 3 |
| T05 — Relacionamento | Preferências (RN13) e avaliação com justificativa, responsável e data | T00 | CA07, CA09 | Pessoas 4 e 5 |
| T06 — Integração | Fluxo completo revisado, inclusive falhas e celular | T01–T05 | Todos | Pessoa 6 + autores |
| T07 — Entrega | README testado em clone limpo, pitch ≤ 5 min, push | T06 | Demo reproduzível | Pessoas 1 e 6 + equipe |
| Opcional | Eventos externos/simulados (CA06) | T06 concluída | CA06 | Quem estiver livre |

Pessoa 1 mantém a especificação e apoia testes. Pessoa 6 integra desde a base.
Cada autor verifica sua entrega. Quem escreve não revisa o próprio trabalho.
Implementação paralela após T00: integrar assim que a base permitir, sem manter
duas implementações incompatíveis.

## Cronograma — 10/10/2026 (São Paulo)

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
2. Lista priorizada; abrir um cliente e mostrar resumo com fontes.
3. Vencimento (alta) e aniversário (média, respeitando permissão).
4. Registrar interação, tratar alerta e ver prioridade/histórico atualizados.
5. Privacidade (dados fictícios), limitações, benefícios e evolução.

## Quando faltar tempo

Preservar o fluxo completo. Cortar nesta ordem: eventos opcionais, visualizações
extras, polimento visual. Não cortar persistência, regras essenciais nem a
validação em clone limpo.
