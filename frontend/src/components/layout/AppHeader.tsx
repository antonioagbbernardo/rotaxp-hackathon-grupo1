import { Avatar } from '@/components/ui/Avatar'
import { DotLabel } from '@/components/ui/DotLabel'

interface Advisor {
  name: string
  role: string
}

interface AppHeaderProps {
  advisor: Advisor
  isDemo?: boolean
}

export function AppHeader({ advisor, isDemo = false }: AppHeaderProps) {
  return (
    <header className="flex h-19 shrink-0 items-center justify-between gap-6 bg-header px-6">
      <div className="flex items-center gap-4">
        <span className="flex size-10 items-center justify-center rounded-lg bg-brand text-xl font-bold tracking-tight text-black">
          xp
        </span>
        <div>
          <p className="text-lg leading-tight font-bold tracking-wide">PULSE</p>
          <p className="text-[11px] text-ink-muted">Inteligência de relacionamento</p>
        </div>
      </div>

      <div className="flex items-center gap-5">
        {isDemo && (
          <span className="hidden w-55 rounded-md bg-surface-raised px-2.5 py-1.5 text-[11px] text-ink-muted md:block">
            <DotLabel>Dados de demonstração</DotLabel>
          </span>
        )}
        <div className="flex items-center gap-3">
          <Avatar name={advisor.name} size="md" className="bg-surface-raised" />
          <div className="hidden sm:block">
            <p className="text-xs font-medium">{advisor.name}</p>
            <p className="text-[10px] text-ink-muted">{advisor.role}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
