import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowLeft, BriefcaseBusiness, Check, Mail, Save, UserRound } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { api } from '@/lib/api'

export interface AdvisorProfileData {
  name: string
  role: string
  email: string
  phone: string
  office: string
}

const campos = [
  { chave: 'name', rotulo: 'Nome completo', limite: 120, tipo: 'text', completo: 'name', obrigatorio: true },
  { chave: 'role', rotulo: 'Cargo', limite: 80, tipo: 'text', completo: 'organization-title', obrigatorio: true },
  { chave: 'email', rotulo: 'E-mail profissional', limite: 254, tipo: 'email', completo: 'email', obrigatorio: false },
  { chave: 'phone', rotulo: 'Telefone', limite: 30, tipo: 'tel', completo: 'tel', obrigatorio: false },
  { chave: 'office', rotulo: 'Escritório', limite: 120, tipo: 'text', completo: 'organization', obrigatorio: false },
] as const

export function AdvisorProfile({ onBack, onSaved }: {
  onBack: () => void
  onSaved: (perfil: AdvisorProfileData) => void
}) {
  const [salvo, setSalvo] = useState<AdvisorProfileData | null>(null)
  const [edicao, setEdicao] = useState<AdvisorProfileData | null>(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [sucesso, setSucesso] = useState(false)
  const [tentativa, setTentativa] = useState(0)
  const enviando = useRef(false)
  const titulo = useRef<HTMLHeadingElement>(null)
  useEffect(() => { titulo.current?.focus() }, [])
  useEffect(() => {
    const controller = new AbortController()
    api<AdvisorProfileData>('/api/pulse/assessor', { signal: controller.signal }).then((perfil) => {
      if (!controller.signal.aborted) { setSalvo(perfil); setEdicao(perfil); setErro('') }
    }).catch((e: unknown) => {
      if (!controller.signal.aborted) setErro(e instanceof Error ? e.message : 'Não foi possível carregar o perfil.')
    }).finally(() => { if (!controller.signal.aborted) setCarregando(false) })
    return () => controller.abort()
  }, [tentativa])
  const alterado = !!edicao && !!salvo && campos.some(({ chave }) => edicao[chave] !== salvo[chave])

  async function salvar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!edicao || !alterado || enviando.current) return
    enviando.current = true; setSalvando(true); setErro(''); setSucesso(false)
    try {
      const perfil = await api<AdvisorProfileData>('/api/pulse/assessor', { method: 'PUT', body: edicao })
      setSalvo(perfil); setEdicao(perfil); onSaved(perfil); setSucesso(true)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Não foi possível salvar. Tente novamente.')
    } finally { enviando.current = false; setSalvando(false) }
  }

  return <main className="min-w-0 flex-1 overflow-y-auto p-4 sm:p-6 lg:p-10">
    <div className="mx-auto max-w-5xl">
      <Button onClick={onBack} disabled={salvando} className="mb-6 flex items-center gap-2">
        <ArrowLeft size={14} aria-hidden /> Voltar ao painel
      </Button>
      <p className="text-[10px] font-semibold tracking-[0.18em] text-brand uppercase">Sua conta</p>
      <h1 ref={titulo} tabIndex={-1} className="mt-2 text-2xl font-semibold outline-none">Meu perfil</h1>
      <p className="mt-2 text-xs leading-6 text-ink-muted">Mantenha seus dados profissionais atualizados.</p>
      <div className="mt-7 grid items-start gap-5 md:grid-cols-[260px_minmax(0,1fr)]">
        <Panel className="min-w-0 overflow-hidden">
          <div className="h-2 bg-brand" />
          <div className="p-6">
            <Avatar name={salvo?.name ?? 'Assessor'} size="lg" className="bg-brand/10 text-brand ring-1 ring-brand/20" />
            <h2 className="mt-4 text-base font-semibold break-words">{salvo?.name ?? 'Seu perfil'}</h2>
            <p className="mt-1 text-xs leading-5 break-words text-ink-muted">{salvo?.role ?? 'Carregando…'}</p>
            <div className="mt-5 space-y-3 border-t border-line pt-5 text-xs text-ink-muted">
              <p className="flex items-start gap-2"><BriefcaseBusiness size={14} className="shrink-0" aria-hidden /><span className="break-words">{salvo?.office || 'Escritório não informado'}</span></p>
              <p className="flex items-start gap-2"><Mail size={14} className="shrink-0" aria-hidden /><span className="min-w-0 break-words">{salvo?.email || 'E-mail não informado'}</span></p>
            </div>
            <p className="mt-6 text-[10px] text-ink-muted">Perfil de demonstração · Dados fictícios</p>
          </div>
        </Panel>
        <Panel className="min-w-0 p-5 sm:p-7" aria-labelledby="dados-profissionais">
          <div className="flex items-center gap-3 border-b border-line pb-5">
            <span className="rounded-lg bg-surface-raised p-2.5 text-brand"><UserRound size={18} aria-hidden /></span>
            <div><h2 id="dados-profissionais" className="text-sm font-semibold">Dados profissionais</h2>
              <p className="mt-1 text-[11px] text-ink-muted">Estas informações identificam você no painel.</p></div>
          </div>
          {carregando && <p role="status" className="mt-5 text-xs text-ink-muted">Carregando perfil…</p>}
          {erro && <p role="alert" className="mt-5 text-xs leading-5 text-negative">{erro}</p>}
          {!carregando && !edicao && <Button className="mt-4" onClick={() => { setCarregando(true); setTentativa((n) => n + 1) }}>Tentar novamente</Button>}
          {edicao && <form onSubmit={(e) => void salvar(e)} className="mt-6">
            <fieldset disabled={salvando} className="grid min-w-0 gap-5 sm:grid-cols-2">
              <legend className="sr-only">Editar dados profissionais</legend>
              {campos.map(({ chave, rotulo, limite, tipo, completo, obrigatorio }) => <div key={chave} className={chave === 'office' ? 'sm:col-span-2' : ''}>
                <label htmlFor={`perfil-${chave}`} className="mb-2 block text-xs font-medium">{rotulo}{!obrigatorio && <span className="ml-1 font-normal text-ink-muted">(opcional)</span>}</label>
                <input id={`perfil-${chave}`} name={chave} type={tipo} autoComplete={completo} required={obrigatorio}
                  maxLength={limite}
                  value={edicao[chave]} onChange={(e) => { setEdicao({ ...edicao, [chave]: e.target.value }); setSucesso(false) }}
                  className="h-11 w-full min-w-0 rounded-lg border border-line bg-canvas px-3 text-sm outline-none transition-colors focus:border-brand focus:ring-1 focus:ring-brand disabled:opacity-60" />
              </div>)}
            </fieldset>
            {sucesso && <p role="status" className="mt-5 flex items-center gap-2 text-xs text-positive"><Check size={15} aria-hidden /> Perfil salvo com sucesso.</p>}
            <div className="mt-7 flex flex-wrap items-center justify-end gap-3 border-t border-line pt-5">
              <Button disabled={salvando || !alterado} onClick={() => { setEdicao(salvo); setErro(''); setSucesso(false) }}>Cancelar</Button>
              <Button type="submit" variant="primary" disabled={salvando || !alterado} className="flex items-center gap-2"><Save size={14} aria-hidden />{salvando ? 'Salvando…' : 'Salvar alterações'}</Button>
            </div>
          </form>}
        </Panel>
      </div>
    </div>
  </main>
}
