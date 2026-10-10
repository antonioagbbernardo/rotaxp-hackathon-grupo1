import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { useClipboard } from '@/hooks/useClipboard'
import type { OpeningMessage } from '@/types/client'

interface OpeningSuggestionProps {
  openings: OpeningMessage[]
  sources: string[]
}

export function OpeningSuggestion({ openings, sources }: OpeningSuggestionProps) {
  const [toneIndex, setToneIndex] = useState(0)
  const [showSources, setShowSources] = useState(false)
  const { copy, hasCopied, copyError } = useClipboard()

  const opening = openings[toneIndex] ?? openings[0]
  const canAdjustTone = openings.length > 1

  const cycleTone = () => setToneIndex((index) => (index + 1) % openings.length)

  if (!opening) return <p className="text-xs text-ink-muted">Nenhum rascunho disponível.</p>

  return (
    <section aria-labelledby="opening-title">
      <h3
        id="opening-title"
        className="text-[10px] font-medium tracking-wide text-ink-muted uppercase"
      >
        Rascunho de abertura · revisar antes de usar
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
            <li key={source}>
              {source}
            </li>
          ))}
        </ul>
      )}

      <p className="mt-2 text-[10px] text-ink-muted">Rascunho por template com registros da base. Nenhuma mensagem é enviada.</p>
      {copyError && <p role="alert" className="mt-2 text-xs text-negative">{copyError}</p>}
      <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-[1.4fr_1fr_1fr]">
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
