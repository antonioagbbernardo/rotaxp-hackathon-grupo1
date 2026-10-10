@AGENTS.md

## Notas para o Claude Code
- Responda e documente em português do Brasil.
- Edite com as ferramentas de arquivo; rode comandos direto no bash, via `uv run`
  para Python, dentro de `backend/`.
- Antes de concluir, rode `uv run --locked pytest` e relate o resultado real.
- Peça autorização antes de ações externas (push, PR, mensagens, remoto).
- Subagentes só quando houver paralelismo real; quem escreve não revisa.
- Actions (ver "CI" no AGENTS.md): rode o pytest local antes de cada push, agrupe
  commits em um push por entrega e não dispare re-execuções do CI à toa. Não
  crie nem amplie workflows sem pedido; consulte falhas com `gh run view
  --log-failed` em vez de reexecutar.
