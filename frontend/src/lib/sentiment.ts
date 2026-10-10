import type { Pronoun, Sentiment } from '@/types/client'

export function describeImpact(sentiment: Sentiment, pronoun: Pronoun) {
  if (sentiment === 'positive') return `Positiva para ${pronoun}`
  if (sentiment === 'negative') return `Negativa para ${pronoun}`
  return 'Impacto neutro'
}

export const sentimentTextColor: Record<Sentiment, string> = {
  positive: 'text-positive',
  negative: 'text-negative',
  neutral: 'text-ink-muted',
  unknown: 'text-ink-muted',
}
