import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

export function useApiResource<T>(path: string, revision: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const generation = useRef(0)
  const refresh = useCallback(async (signal?: AbortSignal) => {
    const request = ++generation.current
    try {
      const result = await api<T>(path, { signal })
      if (!signal?.aborted && request === generation.current) { setData(result); setError('') }
    } catch (e) {
      if (!signal?.aborted && request === generation.current) setError(e instanceof Error ? e.message : 'Não foi possível consultar os registros.')
      throw e
    } finally {
      if (!signal?.aborted && request === generation.current) setLoading(false)
    }
  }, [path])
  useEffect(() => {
    const controller = new AbortController()
    const request = ++generation.current
    api<T>(path, { signal: controller.signal }).then((result) => {
      if (!controller.signal.aborted && request === generation.current) { setData(result); setError('') }
    }).catch((e: unknown) => {
      if (!controller.signal.aborted && request === generation.current) setError(e instanceof Error ? e.message : 'Não foi possível consultar os registros.')
    }).finally(() => {
      if (!controller.signal.aborted && request === generation.current) setLoading(false)
    })
    return () => controller.abort()
  }, [path, revision])
  // Falha de releitura aparece no banner; não repetir uma gravação já concluída.
  const updated = () => refresh().catch(() => {})
  return { data, error, loading, refresh: updated }
}
