import { Check, Copy } from 'lucide-react'
import { useClipboard } from '@/hooks/useClipboard'
import type { OpeningMessage } from '@/types/client'

interface OpeningSuggestionProps {
  openings: OpeningMessage[]
}

export function OpeningSuggestion({ openings }: OpeningSuggestionProps) {
  const { copy, hasCopied, copyError } = useClipboard()
  const [opening] = openings

  if (!opening) return <p className="text-xs text-ink-muted">Nenhum rascunho disponível.</p>

  return (
    <section aria-labelledby="opening-title">
      <h3
        id="opening-title"
        className="text-[10px] font-medium tracking-wide text-ink-muted uppercase"
      >
        Rascunho de abertura · revisar antes de usar
      </h3>

      <div className="relative mt-2.5 rounded-lg border border-brand/40 bg-brand-soft">
        <blockquote className="px-4 py-4 pr-12 text-xs leading-relaxed">“{opening.text}”</blockquote>
        <button
          type="button"
          onClick={() => copy(opening.text)}
          aria-label={hasCopied ? 'Mensagem copiada' : 'Copiar mensagem'}
          title={hasCopied ? 'Copiada' : 'Copiar mensagem'}
          className="absolute top-2.5 right-2.5 flex size-7 items-center justify-center rounded-md text-brand transition-colors hover:bg-brand/15 focus-visible:outline-2 focus-visible:outline-brand"
        >
          {hasCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
        </button>
        <span aria-live="polite" className="sr-only">
          {hasCopied ? 'Mensagem copiada' : ''}
        </span>
      </div>

      <p className="mt-2 text-[10px] text-ink-muted">Rascunho por template com registros da base. Nenhuma mensagem é enviada.</p>
      {copyError && <p role="alert" className="mt-2 text-xs text-negative">{copyError}</p>}
    </section>
  )
}
