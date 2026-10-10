import { DotLabel } from '@/components/ui/DotLabel'
import { Panel } from '@/components/ui/Panel'
import { formatCurrency } from '@/lib/format'
import type { AssetClass, Portfolio } from '@/types/client'

const assetStyles: Record<AssetClass, { label: string; bar: string; text: string }> = {
  fixedIncome: { label: 'Renda fixa', bar: 'bg-[#9d9da3]', text: 'text-ink' },
  funds: { label: 'Fundos', bar: 'bg-brand', text: 'text-brand' },
  other: { label: 'Outros ativos', bar: 'bg-[#777780]', text: 'text-ink-muted' },
  stocks: { label: 'Ações', bar: 'bg-[#4a4a50]', text: 'text-ink-muted' },
}

interface InvestmentProfileProps {
  portfolio: Portfolio
}

export function InvestmentProfile({ portfolio }: InvestmentProfileProps) {
  const slices = portfolio.allocation.filter((slice) => slice.percent > 0)

  return (
    <Panel className="px-5 py-5">
      <h2 className="text-sm font-medium">Perfil de investimento</h2>
      {portfolio.profile && <p className="mt-2 text-xs text-brand">{portfolio.profile}</p>}

      <div className="mt-1 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <p className="text-2xl font-semibold">{formatCurrency(portfolio.total)}</p>
        <p className="text-[10px] text-ink-muted">Posições cadastradas · dados fictícios</p>
      </div>

      {slices.length > 0 ? <div
        className="mt-4 flex h-2.5 overflow-hidden rounded-full bg-surface-raised"
        role="img"
        aria-label={slices
          .map((slice) => `${assetStyles[slice.asset].label} ${slice.percent}%`)
          .join(', ')}
      >
        {slices.map((slice) => (
          <span
            key={slice.asset}
            className={assetStyles[slice.asset].bar}
            style={{ width: `${slice.percent}%` }}
          />
        ))}
      </div> : <p className="mt-4 text-[11px] text-ink-muted">Nenhuma posição cadastrada para calcular a distribuição.</p>}

      <ul className="mt-4 flex justify-between gap-3 text-[10px]">
        {slices.map((slice) => {
          const style = assetStyles[slice.asset]
          return (
            <li key={slice.asset} className={style.text}>
              <DotLabel>
                {style.label} {slice.percent}%
              </DotLabel>
            </li>
          )
        })}
      </ul>

      {slices.length > 0 && <p className="mt-3 text-[10px] text-ink-muted">Distribuição por valor, agrupada pelo tipo dos ativos cadastrados.</p>}
      <p className="mt-3 text-[10px] text-ink-muted">Objetivo: {portfolio.goal}</p>
    </Panel>
  )
}
