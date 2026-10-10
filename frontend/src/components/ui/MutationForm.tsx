import { useState, type FormEvent, type ReactNode } from 'react'
import { Button } from './Button'

export const controlClass = 'w-full min-w-0 rounded-lg border border-line bg-canvas p-2 text-xs text-ink'

export function MutationForm({ onSave, label, children, reset = false }: {
  onSave: (data: FormData) => Promise<void>; label: string; children: ReactNode; reset?: boolean
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const form = event.currentTarget
    setBusy(true); setError(''); setSaved(false)
    try {
      await onSave(new FormData(form))
      setSaved(true)
      if (reset) form.reset()
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível salvar. Tente novamente.') }
    finally { setBusy(false) }
  }
  return <form onSubmit={submit} className="mt-3 space-y-3">
    <fieldset disabled={busy} className="min-w-0 space-y-3">{children}</fieldset>
    <Button type="submit" disabled={busy}>{busy ? 'Aguarde…' : label}</Button>
    {error && <p role="alert" className="text-xs text-negative">{error}</p>}
    {saved && <p role="status" className="text-xs text-positive">Registro atualizado.</p>}
  </form>
}
