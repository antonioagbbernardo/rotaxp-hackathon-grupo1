import { api, setCsrfToken } from './api.ts'

export interface Sessao {
  autenticado: boolean
  usuario: string | null
  csrf_token: string
}

function guardar(sessao: Sessao): Sessao {
  if (typeof sessao?.autenticado !== 'boolean' || typeof sessao?.csrf_token !== 'string' || !sessao.csrf_token
    || (sessao.autenticado && typeof sessao.usuario !== 'string')) {
    throw new Error('Não foi possível verificar a sessão. Tente novamente.')
  }
  setCsrfToken(sessao.csrf_token)
  return sessao
}

export async function consultarSessao(signal?: AbortSignal): Promise<Sessao> {
  return guardar(await api<Sessao>('/api/auth/sessao', { signal }))
}

export async function entrar(usuario: string, senha: string): Promise<Sessao> {
  await consultarSessao() // atualiza nonce caso outra aba tenha alterado a sessão
  return guardar(await api<Sessao>('/api/auth/login', { method: 'POST', body: { usuario, senha } }))
}

export async function sair(): Promise<Sessao> {
  const atual = await consultarSessao()
  if (!atual.autenticado) return atual
  return guardar(await api<Sessao>('/api/auth/logout', { method: 'POST' }))
}
