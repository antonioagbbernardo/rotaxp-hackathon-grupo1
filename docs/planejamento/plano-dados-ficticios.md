# Plano de dados fictícios e testes

Status: proposta documental para a fonte simulada e testes de inferência/feedback,
ainda não criados. A base já possui seed fictício (`app/seed.py`) e testes de
regras/API; esse seed não simula formulário versionado nem extração das conversas.

## Objetivo

Simular a fonte existente para testar extração de contexto, revisão humana,
feedback, lembranças e keynotes sem conectar canais reais ou consumir NewsAPI.

Proposta: arquivos JSON locais lidos por um adaptador substituível. Quando o
contrato da fonte real estiver disponível, ajustar o formato e trocar a leitura,
mantendo o contrato interno utilizado pelo restante do sistema.

## Conjunto inicial proposto

Três clientes inteiramente fictícios, cada um com:

- Formulário inicial e versão/data da resposta.
- Transcrição de ligação, e-mails e mensagens de WhatsApp Business.
- Identificadores estáveis de cliente e registro, canal, autoria e datas.
- Reunião próxima ou distante, conforme o cenário.
- Notícias simuladas, identificadas como tais, com assunto e data.
- Resultados esperados de extração e decisões de revisão/feedback.

## Cenários e expectativas

| Cenário | Resultado esperado |
| --- | --- |
| Aniversário explícito e interesse por Fórmula 1 | Extrair com evidência e apresentar o interesse para revisão |
| Aniversário da filha mencionado na conversa | Identificar a filha; não atribuir data ao investidor |
| Formulário e conversa contraditórios | Sinalizar conflito, sem sobrescrever correção humana |
| Preferência por assuntos exclusivamente financeiros | Excluir sugestões pessoais do contato |
| Notícia descartada nesta ocasião | Evitar repetição do item e preservar o interesse |
| Assunto bloqueado para um cliente | Respeitar o bloqueio sem afetar outros clientes |
| Importação repetida da mesma versão | Não duplicar registros, inferências ou alertas |
| Reunião próxima | Preparar pauta com contexto, fontes e dúvidas a confirmar |
| Fonte externa indisponível | Manter contexto interno e indicar limitação |

## Como validar depois

1. A equipe escreve e revisa os resultados esperados antes de executar a inferência.
2. Testar importação, identidade, datas e deduplicação com verificações determinísticas.
3. Comparar extrações com os fatos esperados, sujeitos e evidências; aceitar variações
   de redação sem aceitar fatos inventados.
4. Aplicar aprovação, correção, descarte e bloqueio; verificar persistência e alcance.
5. Reprocessar dados e conferir que as correções são preservadas.
6. Abrir a reunião e verificar a pauta no fluxo completo.

Regras e critérios correspondentes: [requisitos](requisitos.md), especialmente
CA19–CA33. Não considerar o mock como evidência de conexão aos provedores reais.
