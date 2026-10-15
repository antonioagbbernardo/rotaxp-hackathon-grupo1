import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

export function useApiResource<T>(path: string | null, revision: string) {
  const [result, setResult] = useState<{ path: string | null; revision: string; data: T | null; error: string }>({ path: null, revision: '', data: null, error: '' })
  const [pending, setPending] = useState(false)
  const generation = useRef(0)
  const refresh = useCallback(async () => {
    if (!path) return
    const request = ++generation.current
    setPending(true)
    try {
      const data = await api<T>(path)
      if (request === generation.current) setResult({ path, revision, data, error: '' })
    } catch (e) {
      if (request === generation.current) setResult((old) => ({ path, revision, data: old.path === path ? old.data : null, error: e instanceof Error ? e.message : 'Não foi possível consultar os registros.' }))
    } finally {
      if (request === generation.current) setPending(false)
    }
  }, [path, revision])
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    const request = ++generation.current
    api<T>(path, { signal: controller.signal }).then((data) => {
      if (!controller.signal.aborted && request === generation.current) {
        setResult({ path, revision, data, error: '' }); setPending(false)
      }
    }).catch((e: unknown) => {
      if (!controller.signal.aborted && request === generation.current) {
        setResult((old) => ({ path, revision, data: old.path === path ? old.data : null, error: e instanceof Error ? e.message : 'Não foi possível consultar os registros.' })); setPending(false)
      }
    })
    return () => controller.abort()
  }, [path, revision])
  const samePath = result.path === path
  return { data: samePath ? result.data : null, error: samePath ? result.error : '',
    loading: !!path && (pending || !samePath || result.revision !== revision), refresh }
}
