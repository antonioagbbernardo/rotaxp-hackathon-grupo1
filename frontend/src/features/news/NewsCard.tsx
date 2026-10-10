import { Badge, type BadgeTone } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { cn } from '@/lib/cn'
import { formatElapsed } from '@/lib/format'
import { sentimentTextColor } from '@/lib/sentiment'
import type { NewsItem, Pronoun, Sentiment } from '@/types/client'

const sentimentBadge: Record<Sentiment, { label: string; tone: BadgeTone }> = {
  positive: { label: 'Positiva', tone: 'positive' },
  negative: { label: 'Negativa', tone: 'negative' },
  neutral: { label: 'Neutra', tone: 'neutral' },
}

interface NewsCardProps {
  news: NewsItem
  pronoun: Pronoun
}

export function NewsCard({ news, pronoun }: NewsCardProps) {
  const badge = sentimentBadge[news.sentiment]

  return (
    <Panel className="px-5 py-4">
      <article>
        <header className="flex items-start justify-between gap-4">
          <Badge tone={badge.tone} uppercase className="rounded-sm py-1.5 text-[10px]">
            {badge.label}
          </Badge>
          <SentimentFace sentiment={news.sentiment} className="size-6.5" />
        </header>

        <h3 className="mt-3 text-lg">{news.title}</h3>

        <p className="mt-5 text-[9px] font-medium tracking-wide text-ink-muted uppercase">
          Por que importa para {pronoun}
        </p>
        <p className="mt-2 text-xs text-ink-muted">{news.whyItMatters}</p>

        <p className={cn('mt-5 text-[11px] font-medium', sentimentTextColor[news.sentiment])}>
          {news.relevance}
        </p>
        <p className="mt-1.5 text-[9px] text-ink-subtle">
          {news.scenario} · Atualizado {formatElapsed(news.updatedMinutesAgo)}
        </p>
      </article>
    </Panel>
  )
}
