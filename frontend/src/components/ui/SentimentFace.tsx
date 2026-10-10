import type { Sentiment } from '@/types/client'
import { cn } from '@/lib/cn'

interface SentimentFaceProps {
  sentiment: Sentiment
  className?: string
  /** Texto para leitores de tela. Quando omitido, o ícone é decorativo. */
  label?: string
}

const mouthPath: Record<Sentiment, string> = {
  positive: 'M8 14.5c1.2 1.6 2.6 2.3 4 2.3s2.8-.7 4-2.3',
  negative: 'M8 16.8c1.2-1.6 2.6-2.3 4-2.3s2.8.7 4 2.3',
  neutral: 'M8.5 15.5h7',
  unknown: 'M8.5 15.5h7',
}

export function SentimentFace({ sentiment, className, label }: SentimentFaceProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn('size-6 shrink-0', className)}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <circle cx="12" cy="12" r="11" fill={sentiment === 'unknown' ? '#a1a1aa' : '#FFD43B'} />
      <circle cx="8.6" cy="9.6" r="1.1" fill="#3a2e00" />
      <circle cx="15.4" cy="9.6" r="1.1" fill="#3a2e00" />
      <path
        d={mouthPath[sentiment]}
        fill="none"
        stroke="#3a2e00"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  )
}
