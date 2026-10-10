import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { useClipboard } from '@/hooks/useClipboard'
import type { NewsItem, OpeningMessage } from '@/types/client'

interface OpeningSuggestionProps {
  openings: OpeningMessage[]
  sources: NewsItem[]
}

export function OpeningSuggestion({ openings, sources }: OpeningSuggestionProps) {
  const [toneIndex, setToneIndex] = useState(0)
  const [showSources, setShowSources] = useState(false)
  const { copy, hasCopied } = useClipboard()

  const opening = openings[toneIndex]
  const canAdjustTone = openings.length > 1

  const cycleTone = () => setToneIndex((index) => (index + 1) % openings.length)

  return (
    <section aria-labelledby="opening-title">
      <h3
        id="opening-title"
        className="text-[10px] font-medium tracking-wide text-ink-muted uppercase"
      >
        Sugestão de abertura · WhatsApp
        {canAdjustTone && <span className="normal-case"> · tom {opening.tone.toLowerCase()}</span>}
      </h3>

      <blockquote
        aria-live="polite"
        className="mt-2.5 min-h-32 rounded-lg border border-brand/40 bg-brand-soft px-4 py-4 text-xs leading-relaxed"
      >
        “{opening.text}”
      </blockquote>

      {showSources && (
        <ul className="mt-3 space-y-1 rounded-lg bg-surface-raised px-4 py-3 text-[11px] text-ink-muted">
          {sources.map((source) => (
            <li key={source.id}>
              {source.scenario} — {source.title}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-3 grid grid-cols-[1.4fr_1fr_1fr] gap-2.5">
        <Button variant="primary" onClick={() => copy(opening.text)}>
          {hasCopied ? 'Mensagem copiada' : 'Copiar mensagem'}
        </Button>
        <Button onClick={cycleTone} disabled={!canAdjustTone} className="disabled:opacity-40">
          Ajustar tom
        </Button>
        <Button aria-pressed={showSources} onClick={() => setShowSources((value) => !value)}>
          {showSources ? 'Ocultar base' : 'Ver base'}
        </Button>
      </div>
    </section>
  )
}
