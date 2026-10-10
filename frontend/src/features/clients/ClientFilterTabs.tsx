import { cn } from '@/lib/cn'
import type { ClientFilter } from '@/hooks/useClientFilters'

interface ClientFilterTabsProps {
  value: ClientFilter
  counts: Record<ClientFilter, number>
  onChange: (filter: ClientFilter) => void
}

const options: { value: ClientFilter; label: string }[] = [
  { value: 'all', label: 'Todos' },
  { value: 'attention', label: 'Atenção' },
]

export function ClientFilterTabs({ value, counts, onChange }: ClientFilterTabsProps) {
  return (
    <div role="group" aria-label="Filtrar clientes" className="flex gap-2">
      {options.map((option) => {
        const isActive = option.value === value
        const isAttention = option.value === 'attention'

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(option.value)}
            className={cn(
              'rounded-md px-2.5 py-1.5 text-[11px] font-medium transition-colors',
              'focus-visible:outline-2 focus-visible:outline-brand',
              isAttention ? 'bg-negative-soft text-negative' : 'text-ink',
              isActive && (isAttention ? 'ring-1 ring-negative/50' : 'bg-surface-raised'),
            )}
          >
            {option.label} {counts[option.value]}
          </button>
        )
      })}
    </div>
  )
}
