# Incremento 07 — radar de perfil do investidor (heurístico)

Demonstração para o hackathon. **Não é ML, não é suitability e não recomenda
investimentos.** Estimativa heurística sobre posições fictícias, calculada no
frontend, sem rota nova e sem persistência (`contracts.md` não muda).

## Regras

- **RN59.** O radar tem 5 eixos de 0 a 100, calculados só de `positions`
  (ativo, valor, vencimento): *Risco da carteira*, *Crédito privado*,
  *Liquidez* (valor vencendo em até 90 dias), *Horizonte* (prazo médio
  ponderado, teto de 5 anos) e *Diversificação* (1 − concentração por ativo).
- **RN60.** A data de referência é `generatedAt` (relógio do backend); a
  heurística é pura e não lê o relógio do navegador. Valores monetários são
  somados como centavos inteiros, nunca `float`.
- **RN61.** Ativo cujo tipo não é reconhecido não entra no eixo de risco e é
  listado como aviso. Sem posições, não há radar: mostra-se mensagem de ausência.
- **RN62.** O perfil declarado (`tags`) é exibido ao lado do perfil sugerido
  pela carteira; divergência é mostrada, nunca corrigida. Percepção e humor
  não entram no cálculo (RN06).
- **RN63.** Cada eixo expõe as fontes (posições `#id`) que o alimentaram, e o
  painel rotula "estimativa heurística · dados fictícios".

## Critérios de aceite

- **CA85.** Carteira só de Tesouro/CDB/LCI/LCA resulta em risco baixo e sugestão
  "Conservador"; com crédito privado dominante, risco e crédito privado sobem.
- **CA86.** Sem posições não há eixos nem sugestão; ativo desconhecido gera aviso.
- **CA87.** Posição vencida conta como prazo 0 e como liquidez imediata.
- **CA88.** Perfil declarado diferente do sugerido aparece como divergência.

## Limites

O tipo do ativo é a primeira palavra-chave reconhecida no nome (ex.: "Fundo de Tesouro" conta
como fundo). Posição com valor zero, negativo ou data inexistente é ignorada com aviso.

Pesos fixos e hard-coded em `frontend/src/lib/perfil-radar.ts`; é o ponto de
troca por um modelo de ML. Não valida perfil regulatório (API/suitability).
