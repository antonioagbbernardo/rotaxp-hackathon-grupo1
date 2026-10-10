# Plano de execução — proposta para seis pessoas

Status: planejamento, sem implementação autorizada nesta etapa.
Referências: `spec.md`, `requisitos.md` e `design.md`. Os responsáveis serão definidos pela equipe.

## Sequência de trabalho

| Tarefa | Resultado verificável | Depende de | Aceite relacionado | Responsável proposto |
| --- | --- | --- | --- | --- |
| T01 — Alinhamento | Fluxo, exclusões, regras e stack registrados | Decisão da equipe | Todos | Pessoa 1 + equipe |
| T02 — Fonte e dados | Adaptador da fonte existente e formulário; identidade e versões persistidas | T01 | CA02–CA04, CA26 | Pessoa 2 |
| T03 — Primeiro fluxo | Lista abre detalhe com dados da base | T02 e contrato de dados | CA01, CA02, CA10 | Pessoas 2 e 4 |
| T04 — Contexto inferido | Extrair fatos, hipóteses e datas com fontes e sujeitos corretos | T02 | CA27–CA29 | Pessoa 5 |
| T05 — Alertas | Vencimentos e eventos aparecem com motivo e fonte | T02 e regras validadas | CA05–CA08 | Pessoa 3 |
| T06 — Supervisão e feedback | Revisar contexto, lembranças e preferências; aplicar feedback | T03 e T04 | CA07, CA09, CA30–CA33 | Pessoas 4 e 5 |
| T09 — Reuniões e keynotes | Reunião agendada com pauta, fontes, notas preservadas e conclusão | T04–T06; contratos combinados em T01 | CA19–CA25 | Pessoas 4, 5 e 6 |
| T07 — Integração | Fluxo completo revisado, inclusive falhas | T04–T06 e T09 | Todos | Pessoa 6 + autores |
| T08 — Entrega | README, repositório atualizado e pitch de até 5 min | T07 | Demonstração reproduzível | Pessoas 1 e 6 + equipe |

Pessoa 1 mantém a especificação e apoia testes após o alinhamento. Pessoa 6
acompanha a integração desde a base, sem esperar o final. Cada autor verifica
sua entrega. A divisão deve acompanhar as competências reais do grupo.

## Referência de tempo — 6h30 totais

- 0h–0h30: alinhamento, regras, stack, contratos e responsáveis.
- 0h30–1h15: base executável e primeiro fluxo de consulta integrado.
- 1h15–3h30: extração, revisão/feedback, lembranças, alertas e pauta mínima, com integrações frequentes.
- 3h30–4h30: testes essenciais e correções.
- 4h30–5h30: revisão do fluxo completo e documentação de execução.
- 5h30–6h30: envio final, ensaio e margem para imprevistos.

Ajustar ao tempo efetivamente restante. O repositório será clonado às **17h30**,
segundo as instruções do evento; o código da demonstração precisa estar enviado
antes desse horário.

## SDD e TDD na prática

Para cada tarefa, registrar a regra e o critério de aceite antes do código.
Escrever e revisar testes de comportamento, observar a falha esperada,
implementar e executar novamente. Não alterar um resultado correto só para passar.

Priorizar testes dos limites de vencimento, associação de interesses,
preferências de contato, duplicidade de importações/eventos, sujeito de datas,
correções preservadas e efeito do feedback.
Complementar com teste do fluxo completo e da interface no celular.

## Roteiro proposto para demonstração

1. Explicar a dificuldade de reunir contexto e priorizar contatos.
2. Abrir formulário/conversa existentes e mostrar contexto extraído com evidências.
3. Revisar lembrança, corrigir inferência e marcar sugestão irrelevante; mostrar o efeito do feedback.
4. Abrir os keynotes da próxima reunião e revisar fontes e pendências.
5. Registrar o resultado do encontro e conferir o histórico atualizado.
6. Explicar custo, privacidade, limitações e evolução.

## Quando faltar tempo

Preservar o fluxo completo. Adiar visualizações extras, integrações de canais e
aplicativo separado antes de cortar persistência, regras essenciais ou validação.
