import { SearchIcon } from '@/components/ui/icons'

interface ClientSearchProps {
  value: string
  onChange: (value: string) => void
}

export function ClientSearch({ value, onChange }: ClientSearchProps) {
  return (
    <label className="flex h-10 flex-1 items-center gap-2.5 rounded-lg bg-surface-raised px-3 focus-within:ring-1 focus-within:ring-brand/60">
      <SearchIcon className="size-4.5 text-ink-muted" />
      <span className="sr-only">Pesquisar cliente</span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Pesquisar cliente..."
        className="w-full bg-transparent text-xs text-ink outline-none placeholder:text-ink-muted"
      />
    </label>
  )
}
