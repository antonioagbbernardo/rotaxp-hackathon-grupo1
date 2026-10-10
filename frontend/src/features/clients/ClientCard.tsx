import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { priorityLabel, priorityTone, sentimentLabel } from '@/lib/sentiment'
import { cn } from '@/lib/cn'
import type { Client } from '@/types/client'

interface ClientCardProps {
  client: Client
  isSelected: boolean
  onSelect: (clientId: string) => void
}

export function ClientCard({ client, isSelected, onSelect }: ClientCardProps) {
  const hasPositiveNews = client.news?.some((n) => n.sentiment === 'positive')
  const hasNegativeNews = client.news?.some((n) => n.sentiment === 'negative')

  return (
    <button
      type="button"
      onClick={() => onSelect(client.id)}
      aria-current={isSelected || undefined}
      className={cn(
        'relative w-full rounded-xl border px-3 py-3 text-left transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        isSelected
          ? 'border-brand/60 bg-brand-soft'
          : 'border-transparent hover:bg-surface-raised/60',
      )}
    >
      {isSelected && (
        <span aria-hidden className="absolute inset-y-3 left-0 w-0.5 rounded-full bg-brand" />
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <Avatar name={client.name} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{client.name}</p>
            {client.priority && (
              <Badge tone={priorityTone[client.priority]} className="mt-1 px-1.5 py-0.5 text-[10px]">
                Prioridade {priorityLabel[client.priority]}
              </Badge>
            )}
            <div className="mt-1 flex flex-wrap items-center gap-2">
              {hasPositiveNews && (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-positive">
                  <span className="size-1.5 rounded-full bg-positive" />
                  Notícia positiva
                </span>
              )}
              {hasNegativeNews && (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-negative">
                  <span className="size-1.5 rounded-full bg-negative" />
                  Notícia negativa
                </span>
              )}
              {!hasPositiveNews && !hasNegativeNews && (
                <span className="text-[10px] text-ink-muted">
                  Sem notícias novas
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-center gap-0.5">
          <SentimentFace
            sentiment={client.sentiment}
            className="size-6"
            label={`Humor: ${sentimentLabel[client.sentiment]}`}
          />
          <span className="text-[9px] text-ink-muted">{sentimentLabel[client.sentiment]}</span>
        </div>
      </div>
    </button>
  )
}
