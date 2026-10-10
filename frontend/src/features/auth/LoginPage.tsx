import { useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { ArrowRight, Eye, EyeOff, LoaderCircle, LockKeyhole, UserRound } from 'lucide-react'
import logo from '@/assets/logo-xp-pulse.png'
import { Button } from '@/components/ui/Button'

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <main className="relative isolate flex min-h-dvh flex-col items-center justify-center overflow-hidden px-5 py-10">
      <div aria-hidden="true" className="pointer-events-none absolute -top-32 left-1/2 -z-10 h-80 w-80 -translate-x-1/2 rounded-full bg-brand/5 blur-[100px]" />
      <div className="w-full max-w-100">
        <img src={logo} alt="XP Pulse" className="mx-auto mb-10 h-auto w-56 max-w-full" />
        <section className="rounded-2xl border border-line bg-surface p-6 shadow-2xl shadow-black/20 sm:p-8">
          {children}
        </section>
        <p className="mt-6 text-center text-[11px] text-ink-subtle">Mais contexto. Mais tempo para se relacionar.</p>
      </div>
    </main>
  )
}

interface LoginPageProps {
  onLogin: (usuario: string, senha: string) => Promise<void>
  notice?: string
}

const inputClass = 'h-12 w-full rounded-lg border border-line bg-surface-raised pl-10 pr-3 text-sm text-ink outline-none transition-colors placeholder:text-ink-subtle focus:border-brand focus:ring-2 focus:ring-brand/10 disabled:opacity-60'

export function LoginPage({ onLogin, notice }: LoginPageProps) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const enviando = useRef(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (enviando.current) return
    enviando.current = true
    setLoading(true)
    setError('')
    try {
      await onLogin(usuario, senha)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível entrar. Tente novamente.')
    } finally {
      enviando.current = false
      setLoading(false)
    }
  }

  return (
    <AuthShell>
      <div className="mb-7 text-center">
        <p className="mb-2 text-[10px] font-semibold tracking-[0.18em] text-brand uppercase">Área do assessor</p>
        <h1 className="text-2xl font-semibold tracking-tight">Bem-vindo ao XP Pulse</h1>
        <p className="mt-2 text-xs leading-5 text-ink-muted">Entre para acompanhar seus clientes.</p>
      </div>
      <form onSubmit={(event) => { void submit(event) }} className="space-y-5" aria-busy={loading}>
        <div>
          <label htmlFor="login-usuario" className="mb-2 block text-xs font-medium">Usuário</label>
          <div className="relative">
            <UserRound aria-hidden="true" size={16} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-ink-subtle" />
            <input id="login-usuario" name="usuario" autoComplete="username" placeholder="Digite seu usuário"
              className={inputClass} value={usuario} onChange={(e) => setUsuario(e.target.value)}
              required maxLength={80} disabled={loading} autoCapitalize="none" spellCheck={false} />
          </div>
        </div>
        <div>
          <label htmlFor="login-senha" className="mb-2 block text-xs font-medium">Senha</label>
          <div className="relative">
            <LockKeyhole aria-hidden="true" size={16} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-ink-subtle" />
            <input id="login-senha" name="senha" type={showPassword ? 'text' : 'password'} autoComplete="current-password"
              placeholder="Digite sua senha" className={`${inputClass} pr-12`} value={senha}
              onChange={(e) => setSenha(e.target.value)} required maxLength={256} disabled={loading} />
            <button type="button" className="absolute top-1/2 right-2.5 -translate-y-1/2 rounded p-1.5 text-ink-subtle transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-brand"
              onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Ocultar senha' : 'Exibir senha'}
              aria-pressed={showPassword} disabled={loading}>
              {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
            </button>
          </div>
        </div>
        {error ? <p role="alert" className="rounded-lg border border-negative/30 bg-negative-soft p-3 text-xs leading-5 text-negative">{error}</p>
          : notice && <p role="status" className="text-xs leading-5 text-ink-muted">{notice}</p>}
        <Button type="submit" variant="primary" disabled={loading} className="flex h-12 w-full items-center justify-center gap-2 text-center text-sm font-semibold disabled:opacity-60">
          {loading ? <><LoaderCircle size={16} aria-hidden="true" className="animate-spin" /> Entrando…</>
            : <>Entrar <ArrowRight size={16} aria-hidden="true" /></>}
        </Button>
      </form>
    </AuthShell>
  )
}
