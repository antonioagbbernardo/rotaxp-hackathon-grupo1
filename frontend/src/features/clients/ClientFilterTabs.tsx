import { cn } from '@/lib/cn'
import type { ClientFilter } from '@/hooks/useClientFilters'
import { Smile, Meh, Frown } from 'lucide-react'

interface ClientFilterTabsProps {
  value: ClientFilter
  counts: Record<ClientFilter, number>
  onChange: (filter: ClientFilter) => void
}

const options: {
  value: Exclude<ClientFilter, 'all'>
  label: string
  icon: typeof Smile
  activeClass: string
}[] = [
  {
    value: 'positive',
    label: 'Feliz',
    icon: Smile,
    activeClass: 'bg-positive/15 text-positive ring-1 ring-positive/40',
  },
  {
    value: 'neutral',
    label: 'Neutro',
    icon: Meh,
    activeClass: 'bg-surface-raised text-ink ring-1 ring-line',
  },
  {
    value: 'negative',
    label: 'Triste',
    icon: Frown,
    activeClass: 'bg-negative-soft text-negative ring-1 ring-negative/40',
  },
]

export function ClientFilterTabs({ value, counts, onChange }: ClientFilterTabsProps) {
  return (
    <div role="group" aria-label="Filtrar clientes por emoção" className="flex flex-wrap gap-1.5">
      {options.map((option) => {
        const isActive = option.value === value
        const Icon = option.icon

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(isActive ? 'all' : option.value)}
            className={cn(
              'flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors text-ink-muted hover:text-ink',
              'focus-visible:outline-2 focus-visible:outline-brand',
              isActive ? option.activeClass : 'hover:bg-surface-raised/60',
            )}
          >
            <Icon className="size-3.5 shrink-0" />
            <span>{option.label}</span>
            <span className="text-[10px] opacity-75">{counts[option.value]}</span>
          </button>
        )
      })}
    </div>
  )
}
