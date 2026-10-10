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

`id_fonte` é inteiro ou, em fatos agregados (ex.: "2 posições cadastradas"),
lista de ids. Ausências vão em `ausencias` (sem fonte), nunca como fato.

```
{"ausencias": ["Nenhuma interação registrada"],
 "fatos": [{"texto": "CDB vence em 5 dias",
            "fonte": {"tipo_fonte": "posicao", "id_fonte": 1,
                      "data_referencia": "2026-10-15"}}]}
```

## Rotas

```
GET  /api/clientes                      lista (q, prioridade) ordenada por RN11
GET  /api/clientes/<id>                 detalhe: perfil, preferências, resumo, alertas, posições, histórico
POST /api/clientes/<id>/interacoes      registra interação
POST /api/clientes/<id>/relacionamento  nova avaliação (exige justificativa)
PATCH /api/clientes/<id>/preferencias  canal_preferido, intervalo_minimo_dias, permite_assuntos_pessoais
POST /api/alertas/tratar                trata alerta pela chave de ocorrência (200 se já tratado)
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

## Incremento 01 — contrato de fontes fictícias

Especificação e aceites: [01-fontes.md](incrementos/01-fontes.md).
Este contrato é interno; não confirma integração a WhatsApp, telefonia ou e-mail.

```
POST /api/fontes/importar                   importa um lote fictício (200)
GET  /api/fontes/pendencias                 documentos sem identidade resolvida
GET  /api/clientes/<id>/fontes              todas as versões de fontes do cliente
```

Lote: `origem` (texto), `ficticio: true`, `documentos` (1–100 objetos).
Documento: `registro_id` (texto), `versao` (inteiro > 0), `cliente_id`
(inteiro > 0 ou null; inteiros limitados a 64 bits com sinal), `tipo` (`interacao` ou `formulario`), `ocorrida_em`
(ISO 8601, não futuro), `conteudo`. Interação exige `canal` (`whatsapp`,
`email`, `telefone` ou `presencial`) e conteúdo textual não vazio. Formulário
exige conteúdo como objeto não vazio de respostas textuais, sem `canal`.
Campos desconhecidos são recusados para não perder dados silenciosamente.

```json
{
  "origem": "fonte-demo",
  "ficticio": true,
  "documentos": [{
    "registro_id": "ana-whatsapp-01",
    "versao": 1,
    "cliente_id": 1,
    "tipo": "interacao",
    "canal": "whatsapp",
    "ocorrida_em": "2026-10-09T10:00:00-03:00",
    "conteudo": "Dados fictícios: acompanho Fórmula 1."
  }]
}
```

Sucesso: `{"importados": 1, "reutilizados": 0, "pendentes": 0}`. Contadores
referem-se ao lote; pendentes conta documentos sem vínculo, inclusive reutilizados.
Erro segue `erro.codigo/campo/mensagem`; 400 para validação e 409 para conflito
de versão ou identidade. `erro.campo` inclui índice do documento.

Documento persistido: `id`, `origem`, `registro_id`, `versao`, `cliente_referencia`
(ID recebido), `cliente_id` (vínculo resolvido ou null), `tipo`, `canal`,
`conteudo`, `ocorrida_em`, `importada_em`, `interacao_id` (quando resolvida),
`atual` (maior versão conhecida). Conteúdo mantém o original; instantes são
normalizados em UTC. Respostas de consulta: `{"fontes": [...]}` e
`{"pendencias": [...]}`. Ordenação: ocorrência decrescente, origem/registro,
versão decrescente. ID de cliente inexistente na consulta retorna 404.

Interações importadas entram no histórico cronológico atual. Uma nova versão
mantém seu `interacao_id` e `registrada_em`, atualizando canal/texto/ocorrência.
As versões de evidência permanecem em `documento_fonte`. Formulários não
alteram automaticamente campos do cliente. Pendências ficam fora de todos os
históricos de cliente até existir uma rotina explícita de reconciliação.

## Incremento 02 — contexto e revisão

Especificação: [02-contexto-revisao.md](incrementos/02-contexto-revisao.md).

```
POST /api/clientes/<id>/contexto/processar     processa fontes novas (200)
GET  /api/clientes/<id>/contexto               itens, revisões e atualidade
POST /api/clientes/<id>/contexto/<item>/revisar decisão humana
POST /api/clientes/<id>/assuntos/<assunto>     bloqueio/permissão de contato
```

Processar não exige corpo; não recebe chave/modelo pelo navegador. Sucesso:
`{"novos": N, "documentos_processados": N, "reutilizado": false}`; sem novidades,
`novos: 0`, `documentos_processados: 0`, `reutilizado: true`. Sem fontes resolvidas:
400. Em processamento ou fontes alteradas durante chamada: 409. Sem chave ou
erro externo/cota: 503. Saída inválida/truncada: 502, sem itens parciais.

Saída do modelo: `{"itens": [...]}` (0–30), cada item exige:

| Campo | Contrato |
| --- | --- |
| `categoria` | objetivo, interesse, preferencia, data_importante, compromisso, ponto_atencao |
| `assunto` | slug estável de 1–80 caracteres `[a-z0-9-]`, para agrupar o mesmo assunto entre fontes |
| `sujeito` | cliente, familiar, terceiro ou incerto |
| `tipo` | fato (explícito na fonte) ou hipotese; ambos aguardam revisão |
| `valor` | texto de 1–500 caracteres; não inventar precisão de datas |
| `evidencias` | 1–5 objetos com documento_id inteiro, trecho literal não vazio, campo (nome do campo para formulário; null para conversa) |

Consultar retorna `{"itens": [...], "modelo": "...", "configurado": true/false,
"fontes_novas": N}`. Cada item acrescenta `id`, `cliente_id`, `valor_original`,
`valor_revisado`, `estado` (pendente, confirmado, corrigido, descartado, adiado),
`revisao` (inteiro), `adiado_ate`, `gerado_em`, `modelo`, `evidencia_atual`,
`conflitos` (IDs com possível divergência), `bloqueado`, `elegivel_contato` e
`historico_revisoes`. Evidências incluem origem/registro/versão/data da fonte.
`elegivel_contato` só é verdadeiro se revisado, com sujeito cliente, fontes
atuais, sem conflito, sem bloqueio e respeitando permissão/intervalo pessoal.
Não representa envio ou alerta gerado. Item adiado volta a ser exibido como
pendente na data local combinada; o evento original permanece no histórico.

Revisar: `{"acao": "aprovar|corrigir|descartar|adiar", "motivo": "...",
"revisao": 0, "valor": "...", "adiado_ate": "YYYY-MM-DD"}`. `valor` só para
corrigir; `adiado_ate` só para adiar e deve ser futuro. Campos extras recusados.
Versão de revisão divergente: 409; item de outro cliente: 404. Sucesso retorna
`{"item_id": N, "revisao": N, "estado": "..."}`. Fonte original imutável.

Assunto: `{"bloqueado": true/false, "motivo": "..."}`. Exige assunto existente
no contexto do cliente. Persiste cada alteração com assessor/data, sem remover
o fato ou afetar outros clientes. Retorna assunto/bloqueado. Consulta do contexto
inclui a preferência atual; histórico de alterações fica persistido.

Configuração local: `GEMINI_API_KEY` e `GEMINI_MODEL` em `backend/.env` ou
variáveis de ambiente (que prevalecem). Provedor usa `x-goog-api-key`, HTTPS,
timeout de 30 s e nenhum segredo na resposta ao frontend ou nos logs de erro.
Esquema do provedor limitado às palavras-chave suportadas no REST. O backend
continua validando slug, texto e evidências conforme o contrato acima.
Limites de arrays ficam na instrução e no validador local; o schema enviado não
inclui `minItems/maxItems` devido à rejeição observada na chamada real.
Formato REST: `generationConfig.responseFormat.text.mimeType: APPLICATION_JSON`
e `schema`; não combinar com `responseMimeType/responseJsonSchema` legados.

## Incremento 03 — visão XP Pulse

`GET /api/pulse`: `{advisor: {name, role}, generatedAt: ISO,
clients: [...]}`. Ordem de prioridade da base. Cada cliente usa ID decimal como
string para seleção no React e traz os campos do painel: nome, perfil/tags,
prioridade (`priority`), status de fila, relacionamento humano (`relationshipLabel`),
interesses revisados, último contato, carteira, resumo, fontes, contexto e alertas.
Dinheiro em `portfolio.total` como texto, ou null se não houver posições;
distribuição vazia quando não cadastrada. `updatedMinutesAgo` considera
interações, avaliações, extrações e revisões; `lastContactDays` depende só da
última interação. Campos sem data são null. Interesses revisados podem continuar
como conhecimento após bloqueio; bloqueio impede uso em contato, não apaga fatos.
Data de cadastro/telefone/email ausentes ficam null/texto vazio, sem invenção.
`news` vazio enquanto não houver coleta. `assistant` contém resumo por template,
insights factuais de alertas/revisão e rascunhos de abertura com fontes textuais.
`context` mantém o contrato do incremento 02; `sourceDocuments`, `alerts`,
`interactions`, `preferences` e `summaryFacts` mantêm os campos das rotas da base.
Sem dados: clients vazio. Não chama provedor de IA.

`POST /api/pulse/clientes/<id>/perguntar`: `{pergunta: texto de 1–500 caracteres}`.
Retorna `{resposta: texto, fontes: [referências textuais], modo: "consulta_contexto"}`.
Consulta limitada aos registros existentes; não dispara IA, notícias ou envio.
Temas: perfil, carteira/vencimentos, contato, preferências, interesses/contexto e
preparação/resumo. Tema não suportado retorna limite explícito sem fonte inventada.
Nomes de canal em perguntas de preferência/histórico não implicam pedir número
de contato. Números/endereço e notícias ausentes retornam ausência.
Objeto/campos inválidos: 400; cliente inexistente: 404. Não persiste a pergunta.

### Síntese OpenAI (incremento 04)

`assistant.summary` factual passa a separar os registros com quebras de linha;
`assistant.summaryItems` contém as linhas para apresentação (inclui ausências).
`assistant.aiSummary` = `{configurado: boolean, modelo: texto, assinatura: texto,
resumo: null | {...}}`. GET apenas lê cache válido; não chama OpenAI.

`POST /api/pulse/clientes/<id>/resumo-ia`, **sem corpo**. Fontes e modelo vêm
do servidor. Retorna `{reutilizado: boolean, resumo: {...}}`. O resumo inclui
`visao_geral: {texto, fontes: [referências textuais]}`, `pontos_atencao` e
`antes_contato` (arrays de até três objetos do mesmo formato), `modelo`,
`gerado_em` (UTC), `assinatura` e `uso` (contadores de tokens, se disponíveis).
As referências textuais são resolvidas pelo backend a partir de IDs permitidos;
não se aceitam fontes livres do modelo. Visão geral: até 450 caracteres;
demais trechos: até 300; de uma a cinco fontes por trecho.

Cache em `resumo_ia` por cliente, assinatura dos dados/data/modelo/prompt e
tentativa. Dados alterados invalidam leitura e persistência em andamento.
400: corpo indevido/entrada muito grande; 404: cliente ausente; 409: geração
em andamento/dados alterados; 502: saída inválida, recusada ou incompleta;
503: configuração ou provedor indisponível. Envelope `erro` com campo
`resumo_ia`, sem corpo bruto do provedor ou credenciais. Sem alterações nos
registros originais e sem envio de contato.

`GET /` serve `frontend/dist/index.html` quando compilado; `/assets/<arquivo>`
serve seus assets e `/favicon.svg` o ícone do build. Sem build, `/` usa a interface
anterior. `/legacy` mantém essa interface. Em desenvolvimento,
Vite em 127.0.0.1:5173 encaminha `/api` ao Flask em 127.0.0.1:5001.
