export async function api<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const response = await fetch(path, {
    method: options.method ?? 'GET', signal: options.signal,
    headers: options.body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
  const data = await response.json().catch(() => { throw new Error('Resposta inválida do servidor. Confira se o backend está disponível.') })
  if (!response.ok) {
    const error = data.erro
    throw new Error(error?.mensagem ? `${error.campo ? error.campo + ': ' : ''}${error.mensagem}` : `Erro ${response.status}`)
  }
  return data
}
