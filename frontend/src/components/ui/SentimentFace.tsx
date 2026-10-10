import type { Sentiment } from '@/types/client'
import { cn } from '@/lib/cn'
import { Smile, Meh, Frown, HelpCircle } from 'lucide-react'

interface SentimentFaceProps {
  sentiment: Sentiment
  className?: string
  /** Texto para leitores de tela. Quando omitido, o ícone é decorativo. */
  label?: string
}

const icons: Record<Sentiment, typeof Smile> = {
  positive: Smile,
  neutral: Meh,
  negative: Frown,
  unknown: HelpCircle,
}

export function SentimentFace({ sentiment, className, label }: SentimentFaceProps) {
  const Icon = icons[sentiment] ?? Meh
  const isUnknown = sentiment === 'unknown'

  return (
    <Icon
      className={cn(
        'size-6 shrink-0',
        isUnknown ? 'text-ink-muted' : 'text-[#FFD43B]',
        className,
      )}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  )
}
