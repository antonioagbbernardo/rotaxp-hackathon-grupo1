import { useEffect, useState } from 'react'
import { LoaderCircle } from 'lucide-react'
import { Dashboard } from '@/Dashboard'
import { AuthShell, LoginPage } from '@/features/auth/LoginPage'
import { Button } from '@/components/ui/Button'
import { consultarSessao, entrar, sair } from '@/lib/auth'
import type { Sessao } from '@/lib/auth'
import { SESSION_REQUIRED_EVENT, setCsrfToken } from '@/lib/api'

function atualizarRota(autenticado: boolean, limparSelecao = false) {
  const caminho = autenticado ? '/' : '/login'
  const hash = limparSelecao ? '' : location.hash
  if (location.pathname !== caminho || (limparSelecao && location.hash)) {
    history.replaceState(null, '', `${caminho}${hash}`)
  }
}

export function App() {
  const [sessao, setSessao] = useState<Sessao | null>(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [loggingOut, setLoggingOut] = useState(false)
  const [logoutError, setLogoutError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    consultarSessao(controller.signal).then((result) => {
      if (controller.signal.aborted) return
      setSessao(result)
      setReady(true)
      atualizarRota(result.autenticado)
    }).catch((e: unknown) => {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Não foi possível verificar seu acesso.')
    })
    return () => controller.abort()
  }, [attempt])

  useEffect(() => {
    const expirou = () => {
      setCsrfToken('')
      setSessao(null)
      setReady(true)
      setNotice('Sua sessão foi encerrada. Entre novamente para continuar.')
      atualizarRota(false)
    }
    window.addEventListener(SESSION_REQUIRED_EVENT, expirou)
    return () => window.removeEventListener(SESSION_REQUIRED_EVENT, expirou)
  }, [])

  useEffect(() => {
    const rotear = () => { if (ready) atualizarRota(Boolean(sessao?.autenticado)) }
    window.addEventListener('popstate', rotear)
    return () => window.removeEventListener('popstate', rotear)
  }, [ready, sessao])

  async function login(usuario: string, senha: string) {
    const result = await entrar(usuario, senha)
    if (!result.autenticado) throw new Error('Não foi possível confirmar seu acesso. Tente novamente.')
    setSessao(result)
    setNotice('')
    setLogoutError('')
    atualizarRota(true)
  }

  async function logout() {
    if (loggingOut) return
    setLoggingOut(true)
    setLogoutError('')
    try {
      const result = await sair()
      setSessao(result)
      setNotice('')
      atualizarRota(false, true)
    } catch (e) {
      setLogoutError(e instanceof Error ? e.message : 'Não foi possível sair. Tente novamente.')
    } finally {
      setLoggingOut(false)
    }
  }

  if (!ready) return <AuthShell>
    <div className="flex flex-col items-center gap-4 text-center">
      {error ? <><p role="alert" className="text-sm leading-6 text-negative">{error}</p>
        <Button onClick={() => { setError(''); setAttempt((current) => current + 1) }}>Tentar novamente</Button></>
        : <><LoaderCircle aria-hidden="true" size={24} className="animate-spin text-brand" />
          <p role="status" className="text-sm text-ink-muted">Verificando seu acesso…</p></>}
    </div>
  </AuthShell>

  if (!sessao?.autenticado) return <LoginPage onLogin={login} notice={notice} />
  return <Dashboard onLogout={() => { void logout() }} loggingOut={loggingOut} logoutError={logoutError} />
}
