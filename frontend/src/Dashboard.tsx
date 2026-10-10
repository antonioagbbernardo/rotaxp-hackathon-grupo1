import { useCallback, useEffect, useRef, useState } from 'react'
import { AppHeader } from '@/components/layout/AppHeader'
import { AssistantPanel } from '@/features/assistant/AssistantPanel'
import { ClientSummary } from '@/features/client-overview/ClientSummary'
import { InvestmentProfile } from '@/features/client-overview/InvestmentProfile'
import { PerceptionHistory } from '@/features/client-overview/PerceptionHistory'
import { RadarPerfil } from '@/features/client-overview/RadarPerfil'
import { ClientSidebar } from '@/features/clients/ClientSidebar'
import { NewsSection } from '@/features/news/NewsSection'
import { ClientWorkspace } from '@/features/client-overview/ClientWorkspace'
import { SourceImporter } from '@/features/clients/SourceImporter'
import { Button } from '@/components/ui/Button'
import { api } from '@/lib/api'
import type { PulseView } from '@/types/client'
import { MeetingsSection, UpcomingMeetings } from '@/features/meetings/MeetingsSection'
import { RemindersSection } from '@/features/reminders/RemindersSection'
import { AdvisorProfile } from '@/features/advisor/AdvisorProfile'

export function Dashboard({ onLogout, loggingOut, logoutError }: { onLogout: () => void; loggingOut: boolean; logoutError: string }) {
  const [data, setData] = useState<PulseView | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [profileOpen, setProfileOpen] = useState(location.hash === '#/perfil')
  const [selectedClientId, setSelectedClientId] = useState(location.hash.match(/^#\/clientes\/(\d+)$/)?.[1] ?? '')
  const requestId = useRef(0)
  const humorTentado = useRef(new Set<string>())
  const noticiasTentadas = useRef(new Set<string>())
  const refresh = useCallback(async (signal?: AbortSignal) => {
    const request = ++requestId.current
    try {
      const result = await api<PulseView>('/api/pulse', { signal })
      if (signal?.aborted || request !== requestId.current) return
      setData(result)
      setError('')
      setSelectedClientId((current) => result.clients.some((c) => c.id === current) ? current : result.clients[0]?.id ?? '')
    } catch (e) {
      if (signal?.aborted || request !== requestId.current) return
      setError(e instanceof Error ? e.message : 'Não foi possível carregar os clientes.')
      throw e
    } finally {
      if (!signal?.aborted && request === requestId.current) setLoading(false)
    }
  }, [])
  useEffect(() => {
    const controller = new AbortController()
    const request = ++requestId.current
    api<PulseView>('/api/pulse', { signal: controller.signal }).then((result) => {
      if (controller.signal.aborted || request !== requestId.current) return
      setData(result); setError('')
      setSelectedClientId((current) => result.clients.some((c) => c.id === current) ? current : result.clients[0]?.id ?? '')
    }).catch((e: unknown) => {
      if (!controller.signal.aborted && request === requestId.current) setError(e instanceof Error ? e.message : 'Não foi possível carregar os clientes.')
    }).finally(() => {
      if (!controller.signal.aborted && request === requestId.current) setLoading(false)
    })
    return () => controller.abort()
  }, [])
  useEffect(() => {
    const changed = () => {
      setProfileOpen(location.hash === '#/perfil')
      const id = location.hash.match(/^#\/clientes\/(\d+)$/)?.[1]
      if (id && data?.clients.some((c) => c.id === id)) setSelectedClientId(id)
    }
    window.addEventListener('hashchange', changed)
    return () => window.removeEventListener('hashchange', changed)
  }, [data])
  useEffect(() => {
    const controller = new AbortController()
    const interval = window.setInterval(() => { void refresh(controller.signal).catch(() => {}) }, 60_000)
    return () => { window.clearInterval(interval); controller.abort() }
  }, [refresh])
  const selectedClient = data?.clients.find((client) => client.id === selectedClientId)
  useEffect(() => {
    const pendentes = data?.clients.filter((c) => c.newsState?.configurado && c.newsState.assuntos.some((a) => a.estado === 'nunca' || a.estado === 'desatualizado') && !noticiasTentadas.current.has(`${c.id}:${c.newsState.assuntos.map((a) => `${a.id}:${a.ultima_coleta}`).join('|')}`)) ?? []
    if (!pendentes.length) return
    for (const c of pendentes) noticiasTentadas.current.add(`${c.id}:${c.newsState!.assuntos.map((a) => `${a.id}:${a.ultima_coleta}`).join('|')}`)
    void (async () => {
      for (const c of pendentes) {
        try { await api(`/api/clientes/${c.id}/noticias/atualizar`, { method: 'POST' }) }
        catch { /* Erros de coleta aparecem na seção de notícias. */ }
      }
      await refresh().catch(() => {})
    })()
  }, [data, refresh])
  useEffect(() => {
    const pendentes = data?.clients.filter((c) => c.mood?.configurado && c.mood.estado === 'pendente' && !humorTentado.current.has(`${c.id}:${c.mood.assinatura}`)) ?? []
    if (!pendentes.length) return
    for (const c of pendentes) humorTentado.current.add(`${c.id}:${c.mood!.assinatura}`)
    // Inferências em sequência e cache no servidor: uma chamada por conjunto de conversas.
    void (async () => {
      for (const c of pendentes) {
        try { await api(`/api/pulse/clientes/${c.id}/humor`, { method: 'POST' }) }
        catch { /* O estado/erro persistido aparece no cliente após a releitura. */ }
      }
      await refresh().catch(() => {})
    })()
  }, [data, refresh])
  const retry = () => { setLoading(true); void refresh().catch(() => {}) }
  // Gravação já concluída: falha de releitura aparece no banner, cujo retry
  // consulta a base sem repetir a gravação do formulário.
  const updated = () => { setLoading(true); return refresh().catch(() => {}) }

  return (
    <div className="flex min-h-dvh flex-col xl:h-dvh">
      <AppHeader advisor={data?.advisor ?? { name: 'Carregando assessor', role: 'Assessor de investimentos' }} onLogout={onLogout} loggingOut={loggingOut}
        onOpenProfile={() => { location.hash = '/perfil' }} profileOpen={profileOpen} profileAvailable={!!data} />
      <div className="px-4 pt-3 text-xs text-ink-muted" aria-live="polite">
        {logoutError && <p role="alert" className="mb-2 text-negative">{logoutError}</p>}
        {loading && <p>Carregando dados do backend…</p>}
        {error && <div role="alert" className="flex flex-wrap items-center gap-3 text-negative">{error}<Button onClick={retry}>Tentar novamente</Button></div>}
        {!loading && !error && data && <p>Dados fictícios persistidos · Contexto para poupar sua busca; a decisão continua com o assessor.</p>}
      </div>

      {profileOpen ? <AdvisorProfile onBack={() => { location.hash = selectedClientId ? `/clientes/${selectedClientId}` : '' }}
        onSaved={(perfil) => { setData((current) => current ? { ...current, advisor: { name: perfil.name, role: perfil.role } } : current) }} />
        : data && <main className="grid min-w-0 flex-1 gap-4 p-4 sm:gap-6 sm:p-6 lg:grid-cols-[280px_minmax(0,1fr)] xl:min-h-0 xl:grid-cols-[280px_minmax(0,1fr)_400px]">
        <div className="min-w-0 space-y-4 xl:overflow-y-auto">
        <ClientSidebar
          clients={data.clients}
          selectedClientId={selectedClient?.id ?? ''}
          onSelectClient={(id) => { setSelectedClientId(id); location.hash = `/clientes/${id}` }}
        />
        <SourceImporter onUpdated={updated} />
        <UpcomingMeetings revision={data.generatedAt} onSelect={(id) => { setSelectedClientId(id); location.hash = `/clientes/${id}` }} />
        </div>

        {selectedClient ? <>
        <div className="min-w-0 space-y-4 xl:overflow-y-auto">
          <ClientSummary key={`humor-${selectedClient.id}`} client={selectedClient} onUpdated={updated} />
          <div className="grid gap-4 md:grid-cols-2">
            <PerceptionHistory entries={selectedClient.perception} />
            <InvestmentProfile portfolio={selectedClient.portfolio} />
          </div>
          {data && <RadarPerfil client={selectedClient} hoje={data.generatedAt} />}
          <ClientWorkspace key={selectedClient.id} client={selectedClient} onUpdated={updated} />
          <MeetingsSection key={`agenda-${selectedClient.id}`} clientId={selectedClient.id} revision={data.generatedAt} onUpdated={updated} />
          <RemindersSection key={`lembrancas-${selectedClient.id}`} clientId={selectedClient.id} revision={data.generatedAt} onUpdated={updated} />
          <NewsSection key={selectedClient.id} client={selectedClient} onUpdated={updated} />
        </div>

        <div className="flex min-h-0 flex-col lg:col-span-2 xl:col-span-1">
          <AssistantPanel key={selectedClient.id} client={selectedClient} onUpdated={updated} />
        </div>
        </> : <div className="p-5 text-sm text-ink-muted">Nenhum cliente cadastrado. Inicialize a base fictícia com o comando seed do backend.</div>}
      </main>}
    </div>
  )
}
