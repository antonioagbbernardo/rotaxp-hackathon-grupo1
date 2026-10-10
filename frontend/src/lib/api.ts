export const SESSION_REQUIRED_EVENT = 'xp-pulse:sessao-necessaria'
let csrfToken = ''

export function setCsrfToken(token: string) {
  csrfToken = token
}

function apresentar<T>(value: T): T {
  if (typeof value === 'string') return value.replace(/^Dados fictícios para demonstração$/i, 'Registro da carteira').replace(/Dados fictícios(?: para demonstração)?[:]?\s*/gi, '').replace(/\s*\(fictício\)/gi, '').replace(/Assessor Fictício/g, 'Lucas Almeida').replace(/\bfictíci[oa]s?\b/gi, '') as T
  if (Array.isArray(value)) return value.map(apresentar) as T
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, apresentar(v)])) as T
  return value
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
  // Dados editáveis precisam manter exatamente o valor persistido no perfil.
  if (path === '/api/pulse/assessor') return data
  const apresentado = apresentar(data)
  if (path === '/api/pulse' && data.advisor) apresentado.advisor = data.advisor
  return apresentado
}
