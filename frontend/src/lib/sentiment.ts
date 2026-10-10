import type { Pronoun, Sentiment } from '@/types/client'

export function describeImpact(sentiment: Sentiment, pronoun: Pronoun) {
  if (sentiment === 'positive') return `Notícia positiva para ${pronoun}`
  if (sentiment === 'negative') return `Notícia negativa para ${pronoun}`
  return 'Notícia neutra'
}

export const sentimentTextColor: Record<Sentiment, string> = {
  positive: 'text-positive',
  negative: 'text-negative',
  neutral: 'text-ink-muted',
  unknown: 'text-ink-muted',
}

export const sentimentLabel: Record<Sentiment, string> = {
  positive: 'positivo',
  negative: 'negativo',
  neutral: 'neutro',
  unknown: 'sem avaliação',
}

export const priorityLabel = { alta: 'Alta', media: 'Média', baixa: 'Baixa' } as const

export const priorityTone = { alta: 'negative', media: 'brand', baixa: 'neutral' } as const
