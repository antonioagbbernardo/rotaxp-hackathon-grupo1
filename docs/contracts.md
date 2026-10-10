# Contratos — T00

Status: rascunho para fechar em até 20 min pelo líder técnico e pelos
responsáveis de backend e frontend. Mudanças depois disso passam pela equipe.

## Padrões

- Datas `YYYY-MM-DD`; instantes ISO 8601 com offset.
- Prazos calculados em `America/Sao_Paulo`; "hoje" vem de um relógio injetável.
- Dinheiro em `Decimal` (nunca float); serializado como string.
- Identificadores: inteiro.
- Erros: inexistente → 404; entrada inválida → 400 com campo e motivo; nenhum
  registro persistido em caso de erro.

## Entidades (campos mínimos)

| Entidade | Campos |
| --- | --- |
| Cliente | `id`, `nome`, `perfil`, `permite_assuntos_pessoais`, `estado_relacionamento`, `justificativa` |
| Posicao | `id`, `cliente_id`, `ativo`, `valor`, `vencimento`, `fonte` |
| Interacao | `id`, `cliente_id`, `canal`, `texto`, `data_hora`, `proximos_passos` (opcional) |
| DataImportante | `id`, `cliente_id`, `tipo` (`aniversario`), `vinculo` (`cliente`\|`familiar`), `descricao`, `dia`, `mes`, `fonte` |
| Alerta | `id`, `cliente_id`, `tipo` (`vencimento`\|`vencido`\|`aniversario`), `prioridade` (`alta`\|`media`\|`baixa`), `motivo`, `fonte`, `estado` (`pendente`\|`tratado`), `chave_ocorrencia` |

Canais válidos: `whatsapp`, `email`, `telefone`, `presencial`.
Estados de relacionamento: `positivo`, `atencao`, `negativo`.
`DataImportante`: não armazenar nome do familiar nem ano de nascimento.

## Rotas

```
GET  /api/clientes              lista (q, prioridade) ordenada por RN11
GET  /api/clientes/<id>         detalhe: perfil, resumo, alertas, posições, histórico
POST /api/clientes/<id>/interacoes  registra interação
POST /api/clientes/<id>/relacionamento  altera estado (exige justificativa)
POST /api/alertas/<id>/tratar   marca alerta como tratado
```

## Formato JSON

- Respostas `application/json`; sucesso `200` (leitura) ou `201` (criação).
- Erro: `{"erro": {"codigo": "...", "campo": "...", "mensagem": "..."}}`.
- Corpo dos `POST` em JSON. Exemplo de `POST /api/clientes/1/interacoes`:
  `{"canal": "telefone", "texto": "...", "data_hora": "2026-10-10T14:00:00-03:00"}`.
- `GET /` serve a página base; a interface lê os dados pelas rotas acima.
