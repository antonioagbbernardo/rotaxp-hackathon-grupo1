# Contratos — T00

Status: fechado em 10/10/2026 com as regras de `spec.md`. Mudanças passam pela
equipe.

## Padrões

- Datas `YYYY-MM-DD`; instantes ISO 8601 com offset na API e UTC no banco.
- Entrada de instante sem fuso é interpretada como `America/Sao_Paulo`.
- "Hoje" vem do `Clock` injetável (fuso `America/Sao_Paulo`).
- Dinheiro em `Decimal`; serializado como string.
- Identificadores: inteiro.
- Erros: inexistente → 404; entrada inválida → 400; nenhum registro persistido
  em caso de erro. Não há `403` no MVP (sem autenticação).

## Entidades (campos mínimos)

| Entidade | Campos |
| --- | --- |
| Assessor | `id`, `nome` (um assessor fictício único, criado no seed) |
| Cliente | `id`, `nome`, `perfil`, `canal_preferido`, `intervalo_minimo_dias`, `permite_assuntos_pessoais` |
| AvaliacaoRelacionamento | `id`, `cliente_id`, `estado` (`positivo`\|`atencao`\|`negativo`), `justificativa`, `assessor_id`, `avaliada_em`. Estado atual = última avaliação; sem avaliação = "Não avaliado" |
| Posicao | `id`, `cliente_id`, `ativo`, `valor`, `vencimento`, `fonte` |
| Interacao | `id`, `cliente_id`, `canal`, `texto`, `ocorrida_em`, `registrada_em`, `proximos_passos` (opcional), `assessor_id` |
| DataImportante | `id`, `cliente_id`, `tipo` (`aniversario`), `vinculo` (`cliente`\|`familiar`), `descricao`, `dia`, `mes`, `fonte` |
| TratamentoAlerta | `chave_ocorrencia` (única), `cliente_id`, `tratado_em`, `assessor_id` |
| Alerta (calculado, não persistido) | `cliente_id`, `regra` (`vencimento`\|`aniversario`), `entidade_origem_id`, `ocorrencia`, `chave_ocorrencia`, `classificacao`, `rotulo`, `prioridade`, `motivo`, `fonte`, `estado` (`pendente`\|`tratado`) |

Canais: `whatsapp`, `email`, `telefone`, `presencial`.
`chave_ocorrencia`: `venc:{posicao_id}:{data_vencimento}` e
`aniv:{data_importante_id}:{data_da_ocorrencia}`.
`DataImportante`: não armazenar nome do familiar nem ano de nascimento.

### Resumo (RN08)

```
{"fatos": [{"texto": "CDB vence em 5 dias",
            "fonte": {"tipo_fonte": "posicao", "id_fonte": 1,
                      "data_referencia": "2026-10-15"}}]}
```

## Rotas

```
GET  /api/clientes                      lista (q, prioridade) ordenada por RN11
GET  /api/clientes/<id>                 detalhe: perfil, preferências, resumo, alertas, posições, histórico
POST /api/clientes/<id>/interacoes      registra interação
POST /api/clientes/<id>/relacionamento  nova avaliação (exige justificativa)
POST /api/alertas/tratar                trata alerta pela chave de ocorrência
```

O alerta não tem `id` persistido; a rota de tratamento recebe
`{"cliente_id": 1, "chave_ocorrencia": "venc:3:2026-10-15"}`.

## Formato JSON

- Respostas `application/json`; sucesso `200` (leitura) ou `201` (criação).
- Erro: `{"erro": {"codigo": "...", "campo": "...", "mensagem": "..."}}`.
- Corpo dos `POST` em JSON. Exemplo de `POST /api/clientes/1/interacoes`:
  `{"canal": "telefone", "texto": "...", "ocorrida_em": "2026-10-10T14:00:00-03:00", "proximos_passos": "..."}`
  (`ocorrida_em` omitido = agora; futuro → 400).
- `GET /` serve a página base; a interface lê os dados pelas rotas acima.
