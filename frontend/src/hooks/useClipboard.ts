import { useCallback, useEffect, useRef, useState } from 'react'

const RESET_DELAY_MS = 2000

export function useClipboard() {
  const [hasCopied, setHasCopied] = useState(false)
  const [copyError, setCopyError] = useState('')
  const timeoutRef = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timeoutRef.current), [])

  const copy = useCallback(async (text: string) => {
    try {
      setCopyError('')
      await navigator.clipboard.writeText(text)
      setHasCopied(true)
      window.clearTimeout(timeoutRef.current)
      timeoutRef.current = window.setTimeout(() => setHasCopied(false), RESET_DELAY_MS)
    } catch {
      setHasCopied(false)
      setCopyError('Não foi possível copiar. Selecione o rascunho e copie manualmente.')
    }
  }, [])

  return { copy, hasCopied, copyError }
}
