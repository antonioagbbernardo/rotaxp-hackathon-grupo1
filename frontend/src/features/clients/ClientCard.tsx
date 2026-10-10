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

      <div className="flex items-center gap-3">
        <Avatar name={client.name} src={client.photoUrl} />
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate text-sm font-medium" title={client.name}>{client.name}</p>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            {client.priority && (
              <Badge tone={priorityTone[client.priority]} className="shrink-0 px-1.5 py-0.5 text-[10px] whitespace-nowrap">
                {priorityLabel[client.priority]}
              </Badge>
            )}
            <span className="flex items-center gap-1 text-[10px] whitespace-nowrap text-ink-muted">
              <SentimentFace
                sentiment={client.sentiment}
                className="size-4"
                label={`Humor: ${sentimentLabel[client.sentiment]}`}
              />
              <span>{sentimentLabel[client.sentiment]}</span>
            </span>
          </div>
          <p className="truncate text-[10px]">
            {hasPositiveNews && <span className="font-medium text-positive">Notícia positiva</span>}
            {hasPositiveNews && hasNegativeNews && ' · '}
            {hasNegativeNews && <span className="font-medium text-negative">Notícia negativa</span>}
            {!hasPositiveNews && !hasNegativeNews && <span className="text-ink-muted">{client.news.length ? `${client.news.length} notícia(s) para revisar` : 'Sem notícias para revisar'}</span>}
          </p>
        </div>
      </div>
    </button>
  )
}
