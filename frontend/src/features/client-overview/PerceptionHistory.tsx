import { Panel } from '@/components/ui/Panel'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { capitalize, formatMonth } from '@/lib/format'
import type { PerceptionEntry, Sentiment } from '@/types/client'

const sentimentLabel: Record<Sentiment, string> = {
  positive: 'positiva',
  negative: 'negativa',
  neutral: 'neutra',
}

interface PerceptionHistoryProps {
  entries: PerceptionEntry[]
}

export function PerceptionHistory({ entries }: PerceptionHistoryProps) {
  return (
    <Panel className="px-5 py-5">
      <h2 className="text-sm font-medium">Histórico de percepção</h2>
      <p className="mt-1.5 text-[10px] text-ink-muted">Registrado pelo assessor após os contatos</p>

      <ol className="relative mt-6 flex justify-between">
        <span aria-hidden className="absolute inset-x-6 top-3.5 h-px bg-line" />
        {entries.map((entry) => {
          const month = capitalize(formatMonth(entry.month))
          return (
            <li key={entry.month} className="relative flex w-14 flex-col items-center gap-4">
              <SentimentFace
                sentiment={entry.sentiment}
                className="size-7"
                label={`${month}: percepção ${sentimentLabel[entry.sentiment]}`}
              />
              <span className="text-[9px] text-ink-muted">{month}</span>
            </li>
          )
        })}
      </ol>
    </Panel>
  )
}
