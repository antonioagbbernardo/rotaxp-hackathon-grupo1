import { cn } from '@/lib/cn'
import type { ClientFilter } from '@/hooks/useClientFilters'
import { SentimentFace } from '@/components/ui/SentimentFace'
import type { Sentiment } from '@/types/client'

interface ClientFilterTabsProps {
  value: ClientFilter
  counts: Record<ClientFilter, number>
  onChange: (filter: ClientFilter) => void
}

const options: {
  value: Exclude<ClientFilter, 'all'>
  label: string
  face: Sentiment
  activeClass: string
}[] = [
  {
    value: 'positive',
    label: 'Feliz',
    face: 'positive',
    activeClass: 'bg-positive/15 text-positive ring-1 ring-positive/40',
  },
  {
    value: 'neutral',
    label: 'Neutro',
    face: 'neutral',
    activeClass: 'bg-surface-raised text-ink ring-1 ring-line',
  },
  {
    value: 'negative',
    label: 'Triste',
    face: 'negative',
    activeClass: 'bg-negative-soft text-negative ring-1 ring-negative/40',
  },
  {
    value: 'unknown',
    label: 'Sem avaliação',
    face: 'unknown',
    activeClass: 'bg-surface-raised text-ink ring-1 ring-line',
  },
]

export function ClientFilterTabs({ value, counts, onChange }: ClientFilterTabsProps) {
  return (
    <div role="group" aria-label="Filtrar clientes por emoção" className="grid grid-cols-2 gap-1.5">
      {options.map((option) => {
        const isActive = option.value === value

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(isActive ? 'all' : option.value)}
            className={cn(
              'flex min-w-0 items-center justify-center gap-1 whitespace-nowrap rounded-md px-1.5 py-1 text-[11px] font-medium transition-colors text-ink-muted hover:text-ink',
              'focus-visible:outline-2 focus-visible:outline-brand',
              isActive ? option.activeClass : 'hover:bg-surface-raised/60',
            )}
          >
            <SentimentFace sentiment={option.face} className="size-4" />
            <span>{option.label}</span>
            <span className="text-[10px] opacity-75">{counts[option.value]}</span>
          </button>
        )
      })}
    </div>
  )
}
