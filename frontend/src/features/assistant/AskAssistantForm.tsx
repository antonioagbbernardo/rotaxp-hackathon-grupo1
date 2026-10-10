import { useState, type FormEvent } from 'react'
import { ArrowRightIcon } from '@/components/ui/icons'

interface AskAssistantFormProps {
  placeholder: string
  onAsk: (question: string) => void
  disabled?: boolean
}

export function AskAssistantForm({ placeholder, onAsk, disabled }: AskAssistantFormProps) {
  const [question, setQuestion] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || disabled) return
    onAsk(trimmed)
    setQuestion('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex h-12 items-center rounded-lg border border-line pr-2 pl-4 focus-within:border-brand/60"
    >
      <label htmlFor="assistant-question" className="sr-only">
        Pergunte ao assistente
      </label>
      <input
        id="assistant-question"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        maxLength={4000}
        disabled={disabled}
        className="min-w-0 flex-1 bg-transparent text-xs outline-none placeholder:text-ink-muted"
      />
      <button
        type="submit"
        aria-label="Enviar pergunta"
        disabled={disabled || !question.trim()}
        className="flex size-8 items-center justify-center rounded-md text-ink transition-colors hover:bg-surface-raised"
      >
        <ArrowRightIcon className="size-4.5" />
      </button>
    </form>
  )
}
