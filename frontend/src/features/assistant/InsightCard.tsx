import { cn } from '@/lib/cn'
import type { Insight } from '@/types/client'

interface InsightCardProps {
  insight: Insight
  position: number
}

const kindClasses: Record<Insight['kind'], string> = {
  opportunity: 'bg-positive-soft text-positive',
  concern: 'bg-negative-soft text-negative',
}

export function InsightCard({ insight, position }: InsightCardProps) {
  return (
    <article className={cn('rounded-lg px-4 py-3.5', kindClasses[insight.kind])}>
      <h3 className="text-xs font-medium">
        {String(position).padStart(2, '0')} {insight.title}
      </h3>
      <p className="mt-2 text-xs leading-relaxed text-ink">{insight.body}</p>
    </article>
  )
}
