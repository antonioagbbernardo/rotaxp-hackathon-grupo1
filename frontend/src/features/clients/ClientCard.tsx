import { Avatar } from '@/components/ui/Avatar'
import { DotLabel } from '@/components/ui/DotLabel'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { cn } from '@/lib/cn'
import { formatElapsed } from '@/lib/format'
import { sentimentTextColor } from '@/lib/sentiment'
import type { Client } from '@/types/client'

interface ClientCardProps {
  client: Client
  isSelected: boolean
  onSelect: (clientId: string) => void
}

export function ClientCard({ client, isSelected, onSelect }: ClientCardProps) {
  const impact = `Relacionamento: ${client.relationshipLabel ?? 'Não avaliado'}`

  return (
    <button
      type="button"
      onClick={() => onSelect(client.id)}
      aria-current={isSelected || undefined}
      className={cn(
        'relative w-full rounded-xl border px-3 py-3.5 text-left transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        isSelected
          ? 'border-brand/60 bg-brand-soft'
          : 'border-transparent hover:bg-surface-raised/60',
      )}
    >
      {isSelected && (
        <span aria-hidden className="absolute inset-y-3 left-0 w-0.5 rounded-full bg-brand" />
      )}

      <div className="flex items-start gap-3">
        <Avatar name={client.name} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{client.name}</p>
          <p className="mt-0.5 truncate text-[10px] text-ink-muted">
            {client.interests.join(' · ') || 'Sem interesses revisados'}
          </p>
        </div>
        <SentimentFace sentiment={client.sentiment} label={impact} />
      </div>

      <p className={cn('mt-3 text-[11px] font-medium', sentimentTextColor[client.sentiment])}>
        <DotLabel>{impact}</DotLabel>
      </p>
      <p className="mt-1.5 text-[10px] text-ink-muted">
        Prioridade de atendimento: {client.priority === 'alta' ? 'Alta' : client.priority === 'media' ? 'Média' : 'Baixa'}<br />
        {client.headline} • {formatElapsed(client.updatedMinutesAgo)}
      </p>
    </button>
  )
}
