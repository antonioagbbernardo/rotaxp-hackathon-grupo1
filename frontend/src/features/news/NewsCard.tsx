import { useState } from 'react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { formatDate, formatElapsed } from '@/lib/format'
import type { NewsItem, Pronoun } from '@/types/client'

interface NewsCardProps {
  news: NewsItem
  pronoun: Pronoun
  onDiscard: (id: string, motivo: string) => Promise<void>
}

export function NewsCard({ news, pronoun, onDiscard }: NewsCardProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function discard() {
    if (busy) return
    setBusy(true); setError('')
    try { await onDiscard(news.id, 'Removida pelo assessor: não pertinente para este cliente.') }
    catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível salvar o feedback.') }
    finally { setBusy(false) }
  }

  return (
    <Panel className="min-w-0 px-5 py-4">
      <article>
        <header className="flex items-start justify-between gap-4">
          <Badge uppercase className="rounded-sm py-1.5 text-[10px]">
            Notícia · {news.topic ?? 'Para revisar'}
          </Badge>
        </header>

        <h3 className="mt-3 break-words text-base font-medium leading-relaxed">
          {news.url ? <a href={news.url} target="_blank" rel="noopener noreferrer" className="underline decoration-brand/50 underline-offset-4 hover:text-brand">{news.title}</a> : news.title}
        </h3>
        {news.source && <p className="mt-2 text-[11px] text-ink-muted">{news.source} · Publicada {news.publishedAt ? formatDate(news.publishedAt) : 'sem data'}</p>}
        {news.description && <p className="mt-3 break-words text-xs leading-relaxed text-ink-muted">Trecho da fonte: {news.description}</p>}

        <p className="mt-5 text-[9px] font-medium tracking-wide text-ink-muted uppercase">
          Por que foi selecionada para {pronoun}
        </p>
        <p className="mt-2 break-words text-xs leading-relaxed text-ink-muted">{news.whyItMatters}</p>

        <p className="mt-5 text-[11px] font-medium text-ink-muted">
          {news.relevance}
        </p>
        <p className="mt-1.5 text-[9px] text-ink-subtle">
          {news.scenario} · Coletada {news.collectedAt ? formatDate(news.collectedAt) : formatElapsed(news.updatedMinutesAgo)}
        </p>
        <div className="mt-4 border-t border-line pt-3 text-xs">
          <Button disabled={busy} onClick={() => { void discard() }}>{busy ? 'Removendo…' : 'Remover notícia'}</Button>
          {error && <p role="alert" className="mt-2 text-negative">{error}</p>}
        </div>
      </article>
    </Panel>
  )
}
