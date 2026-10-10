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
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function discard() {
    if (busy) return
    setBusy(true); setError('')
    try { await onDiscard(news.id, reason) }
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
        <details className="mt-4 border-t border-line pt-3 text-xs">
          <summary className="cursor-pointer text-ink-muted">Não é relevante para este cliente</summary>
          <form className="mt-3 space-y-2" onSubmit={(e) => { e.preventDefault(); void discard() }}>
            <label className="block">Motivo do feedback
              <textarea required maxLength={1000} value={reason} onChange={(e) => setReason(e.target.value)} disabled={busy}
                className="mt-2 block min-h-18 w-full rounded-lg border border-line bg-surface p-2 text-xs" />
            </label>
            <p className="text-[10px] text-ink-muted">Oculta esta notícia apenas para este cliente e preserva o interesse.</p>
            <Button type="submit" disabled={busy || !reason.trim()}>{busy ? 'Salvando…' : 'Salvar feedback'}</Button>
            {error && <p role="alert" className="text-negative">{error}</p>}
          </form>
        </details>
      </article>
    </Panel>
  )
}
