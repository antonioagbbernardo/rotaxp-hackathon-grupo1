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
  em caso de erro. Incremento 06: sessão ausente/vencida → 401; CSRF inválido → 403.

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
- `GET /` serve a página base após login; a interface lê os dados pelas rotas acima.

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

## Incremento 05 — notícias NewsAPI

`GET /api/clientes/<id>/noticias`: `{configurado, catalogo, interesses, vinculos,
assuntos, artigos, limite_diario, chamadas_hoje}`. Catálogo: `{id, nome}`;
interesses elegíveis: `{id, revisao, valor, fontes: [texto]}`;
vínculos atuais: `{id, item_id, revisao, assunto, interesse, fontes}`.
Assuntos: `{id, nome, estado: nunca|atualizado|desatualizado|falhou|processando,
ultima_coleta: ISO|null, ultima_tentativa: ISO|null, erro: null|{codigo,mensagem}}`.
Sem coleta: artigos vazio; GET nunca consulta NewsAPI. O adaptador Pulse inclui
`news` com artigos e `newsState` com os demais campos desta consulta.

Artigo adaptado: `{id: URL normalizada, sentiment: "unknown", title,
whyItMatters, relevance, scenario: "NewsAPI", updatedMinutesAgo,
url, source, publishedAt, collectedAt, topic, description}`. Link não comprova
o conteúdo; descrição é apenas o trecho recebido. Até três notícias elegíveis,
com fonte e publicação nos últimos sete dias; feedback ocultado por cliente.

`POST /api/clientes/<id>/noticias/vinculos`: `{item_id: inteiro positivo,
assunto: id do catálogo}`. Resposta 201 `{vinculo_id}`; repetições do vínculo
ativo/revisão retornam 200 e mesmo ID. Vínculos anteriores permanecem como
histórico. 400 (campo inválido/extra/item inelegível), 404 (cliente/item alheio).

`POST /api/clientes/<id>/noticias/atualizar`, **sem corpo**: resposta 200
`{resultados: [{assunto, estado: atualizado|reutilizado|erro,
erro?: {codigo,campo,mensagem,status}}]}`. Cada assunto é independente; falha
parcial é visível e preserva cache. Sem vínculos elegíveis: 400. Erros por assunto:
409 (processando/intervalo), 502 (saída inválida), 503 (chave/provedor/cota).
Nenhuma consulta arbitrária/chave é aceita do navegador.

`POST /api/clientes/<id>/noticias/descartar`: `{artigo_id: URL recebida,
motivo: texto 1–1000}`. Resposta 200 `{descartado: true}`. Artigo deve estar
na seleção atual do cliente; repetição de descarte já próprio é idempotente.
404 se artigo alheio/inexistente, 400 para entrada inválida. Registro com assessor
e data; nenhuma alteração automática em contexto, alerta ou relacionamento.

Configuração: `NEWSAPI_API_KEY`, `NEWSAPI_LIMITE_DIARIO` (1–100, padrão 20).
Novas tabelas: `vinculo_noticia` (histórico de associação/revisão),
`coleta_noticia` (tentativas/versão/estado/erros), `artigo_noticia` (URL única),
`coleta_artigo_noticia` (fontes da coleta), `descarte_noticia` (cliente/URL única).
CLI diário usa o mesmo serviço; instalação de agendador e antecipação por reunião
permanecem pendentes. Contagem conservadora considera toda reserva com chave.

Perguntas básicas sobre notícias passam a listar apenas artigos da seleção atual
do cliente, com publicação/link/estado da coleta, sem HTTP adicional. Não respondem
resultados esportivos nem análise de mercado em tempo real. Sem artigos, mantém
ausência explícita. Notícias ainda não integram a síntese OpenAI do incremento 04.

## Incremento 06 — login e sessão

[Regras/aceites](incrementos/06-login.md). `/login` serve a interface React pública;
`/` e `/legacy` redirecionam para `/login` sem sessão. `/login` com sessão válida
redireciona para `/`. Compilar `frontend/dist` para disponibilizar a tela no Flask.

```
GET  /api/auth/sessao  estado atual e token CSRF (público, 200)
POST /api/auth/login   credenciais em JSON + X-CSRF-Token (200)
POST /api/auth/logout  sessão válida + X-CSRF-Token (200)
```

Sessão: `{"autenticado": false, "usuario": null, "csrf_token": "..."}`; com
acesso, `autenticado: true` e `usuario: "admin"`. GET não retorna senha, cookie
ou chave de assinatura. Cookie HttpOnly/SameSite=Lax; expiração absoluta de oito
horas e revogação no servidor. HTML/APIs usam `Cache-Control: no-store`.

Login aceita apenas `{"usuario": "admin", "senha": "admin"}`; campos obrigatórios
textuais (usuário 1–80 após trim; senha 1–256 sem trim). Login bem-sucedido retorna
estado autenticado e novo `csrf_token`. Logout revoga a sessão e retorna estado
anônimo com novo token, sem apagar dados de clientes.

Toda escrita `/api/...` exige header `X-CSRF-Token` obtido em GET de sessão ou
login. APIs de dados, inclusive rotas não existentes, primeiro validam sessão;
sem acesso retornam 401 sem executar regra/serviço. Leitura não exige CSRF.

| Status | `erro.codigo` | `erro.campo` | Caso |
| --- | --- | --- | --- |
| 400 | `entrada_invalida` | `corpo`, `usuario`, `senha` ou campo extra | Entrada inválida no login |
| 401 | `credenciais_invalidas` | null | Usuário ou senha incorretos (mensagem genérica) |
| 401 | `sessao_necessaria` | null | API protegida sem sessão válida |
| 403 | `csrf_invalido` | `csrf_token` | Escrita sem token correspondente à sessão |

`SECRET_KEY` pode ser definido no `.env`/ambiente. Ausente, gerar chave aleatória
em `session.key`, ao lado do banco local, permissão 0600 e fora do Git. SQLite
armazena `sessao_acesso(token_hash, expira_em)`; somente hash do identificador.
CLI permanece disponível sem login. Não há perfis/permissões multiassessor.

## Incremento 07 — reuniões e keynotes

[Regras](incrementos/07-agenda-keynotes.md). Sessão/CSRF do incremento 06.

```
GET  /api/reunioes                         lista geral (até 100, por início)
GET  /api/clientes/<id>/reunioes            lista do cliente
POST /api/clientes/<id>/reunioes            {objetivo,inicio_em} → 201
GET  /api/reunioes/<id>                     detalhe/pauta atual
PATCH /api/reunioes/<id>                    {objetivo?,inicio_em?,notas?} → 200
POST /api/reunioes/<id>/cancelar            sem corpo → 200
POST /api/reunioes/<id>/preparar             sem corpo → 200
POST /api/reunioes/<id>/revisar              {pauta_id} → 200
POST /api/reunioes/<id>/concluir             {resumo,proximos_passos?} → 201/200
```

Reunião: id, cliente_id/nome, objetivo, inicio_em (UTC), estado, notas, proxima,
interacao_id, resultado (texto/proximos_passos/ocorrida_em ou null), pauta (ou null),
pauta_desatualizada, revisada. Pauta: id, gerada_em,
secoes[{titulo,itens[{texto,fontes[],url?}]}], avisos[]. Dados novos ocultam pauta
antiga até preparar novamente; notas persistem. Conclusão repetida diferente →409.
Entrada/campo inválido→400; inexistente→404; estado/versão incompatível→409.
Erros usam `entrada_invalida`, `nao_encontrado` e `conflito`, sempre com campo.
Notas até 4.000 caracteres. GET nunca chama NewsAPI/IA. Preparação próxima pode
renovar assuntos com cache >=2h, sob o orçamento compartilhado já existente.
CLI `acompanhar-agenda`: ciclo de coleta diária + pautas próximas; `--uma-vez`
para executar só um ciclo. Processo local contínuo com intervalo de 60s por padrão.
Falha de antecipação fica nos avisos da pauta, mesmo com cache anterior disponível.
Pergunta básica sobre agenda/reunião consulta registros com fontes; não coleta.

## Incremento 08 — lembranças com confirmação de data

[Regras](incrementos/08-lembrancas.md). Sessão/CSRF do incremento 06.

```
GET  /api/clientes/<id>/lembrancas          {candidatos[],lembrancas[]}
POST /api/clientes/<id>/lembrancas          {item_id,revisao,tipo,descricao,data} →201/200
POST /api/clientes/<id>/lembrancas/<id>/feedback
      {acao:concluir|descartar|adiar,motivo,adiado_ate?} →200
```

Data `YYYY-MM-DD`; aniversário armazena dia/mês, compromisso data inteira.
Descrição até 500 caracteres. Revisão inteira atual; terceiro/hipótese/conflito/
fonte antiga/bloqueio/permissão ausente recusados (400/409); identidade errada→404.
Candidato inclui id/revisao/valor/sujeito/fontes. Lembrança inclui id/descricao/tipo/
sujeito/ocorrencia/estado/adiado_ate/proxima/pode_contatar/fontes/versao/motivo_feedback.
Motivo 1–1.000;
adiar exige data futura e só essa ação aceita `adiado_ate`. Feedback por ocorrência
é idempotente. Não cria tabela/cópia de alerta financeiro nem altera prioridade.
Mudança de tipo/descrição/data incrementa versão da anotação; feedback antigo não
se aplica a essa versão. Pergunta sobre lembranças usa a mesma seleção com fontes.
