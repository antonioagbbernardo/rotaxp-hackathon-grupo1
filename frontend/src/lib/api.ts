export const SESSION_REQUIRED_EVENT = 'xp-pulse:sessao-necessaria'
let csrfToken = ''

export function setCsrfToken(token: string) {
  csrfToken = token
}

export async function api<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers: Record<string, string> = options.body === undefined ? {} : { 'Content-Type': 'application/json' }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers['X-CSRF-Token'] = csrfToken
  const response = await fetch(path, {
    method, signal: options.signal, credentials: 'same-origin', headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
  const data = await response.json().catch(() => { throw new Error('Resposta inválida do servidor. Confira se o backend está disponível.') })
  if (!response.ok) {
    const error = data.erro
    if (response.status === 401 && error?.codigo === 'sessao_necessaria') {
      setCsrfToken('')
      globalThis.dispatchEvent?.(new Event(SESSION_REQUIRED_EVENT))
    }
    throw new Error(error?.mensagem ? `${error.campo ? error.campo + ': ' : ''}${error.mensagem}` : `Erro ${response.status}`)
  }
  return data
}
