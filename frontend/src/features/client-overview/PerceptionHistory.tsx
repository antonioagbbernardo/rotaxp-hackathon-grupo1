import { Panel } from '@/components/ui/Panel'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { capitalize, formatMonth } from '@/lib/format'
import type { PerceptionEntry, Sentiment } from '@/types/client'

const sentimentLabel: Record<Sentiment, string> = {
  positive: 'positiva',
  negative: 'negativa',
  neutral: 'neutra',
  unknown: 'não avaliada',
}

interface PerceptionHistoryProps {
  entries: PerceptionEntry[]
}

export function PerceptionHistory({ entries }: PerceptionHistoryProps) {
  return (
    <Panel className="px-5 py-5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-medium text-ink">Histórico de humor</h2>
          <p className="mt-1 text-[10px] text-ink-muted">
            Inferências registradas a partir das interações do investidor
          </p>
        </div>
      </div>

      {entries.length === 0 && (
        <p className="mt-4 text-xs text-ink-muted">Nenhuma interação analisada pela IA ainda.</p>
      )}

      <ol className="relative mt-6 flex flex-wrap justify-between gap-4">
        <span aria-hidden className="absolute inset-x-6 top-3.5 h-px bg-line" />
        {entries.map((entry) => {
          const month = capitalize(formatMonth(entry.month))
          const formattedDate = entry.date
            ? new Date(entry.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
            : month

          return (
            <li
              key={entry.id ?? entry.date ?? entry.month}
              title={entry.reason || `${month}: humor ${entry.label ?? sentimentLabel[entry.sentiment]}`}
              className="group relative flex w-16 cursor-help flex-col items-center gap-2"
            >
              <div className="relative transition-transform group-hover:scale-110">
                <SentimentFace
                  sentiment={entry.sentiment}
                  className="size-7"
                  label={`${formattedDate}: humor ${entry.label ?? sentimentLabel[entry.sentiment]}`}
                />
              </div>
              <span className="text-[10px] font-medium text-ink">{formattedDate}</span>
              {entry.label && (
                <span className="text-[9px] text-ink-muted transition-colors group-hover:text-brand">
                  {entry.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </Panel>
  )
}
