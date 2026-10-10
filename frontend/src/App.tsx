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

export function App() {
  const [data, setData] = useState<PulseView | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedClientId, setSelectedClientId] = useState(location.hash.match(/^#\/clientes\/(\d+)$/)?.[1] ?? '')
  const requestId = useRef(0)
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
      const id = location.hash.match(/^#\/clientes\/(\d+)$/)?.[1]
      if (id && data?.clients.some((c) => c.id === id)) setSelectedClientId(id)
    }
    window.addEventListener('hashchange', changed)
    return () => window.removeEventListener('hashchange', changed)
  }, [data])
  const selectedClient = data?.clients.find((client) => client.id === selectedClientId)
  const retry = () => { setLoading(true); void refresh().catch(() => {}) }
  // Gravação já concluída: falha de releitura aparece no banner, cujo retry
  // consulta a base sem repetir a gravação do formulário.
  const updated = () => { setLoading(true); return refresh().catch(() => {}) }

  return (
    <div className="flex min-h-dvh flex-col xl:h-dvh">
      <AppHeader advisor={data?.advisor ?? { name: 'Carregando assessor', role: 'Assessor de investimentos' }} />
      <div className="px-4 pt-3 text-xs text-ink-muted" aria-live="polite">
        {loading && <p>Carregando dados do backend…</p>}
        {error && <div role="alert" className="flex flex-wrap items-center gap-3 text-negative">{error}<Button onClick={retry}>Tentar novamente</Button></div>}
        {!loading && !error && data && <p>Dados fictícios persistidos · Contexto para poupar sua busca; a decisão continua com o assessor.</p>}
      </div>

      {data && <main className="grid min-w-0 flex-1 gap-4 p-4 sm:gap-6 sm:p-6 lg:grid-cols-[280px_minmax(0,1fr)] xl:min-h-0 xl:grid-cols-[280px_minmax(0,1fr)_400px]">
        <div className="min-w-0 space-y-4 xl:overflow-y-auto">
        <ClientSidebar
          clients={data.clients}
          selectedClientId={selectedClient?.id ?? ''}
          onSelectClient={(id) => { setSelectedClientId(id); location.hash = `/clientes/${id}` }}
        />
        <SourceImporter onUpdated={updated} />
        </div>

        {selectedClient ? <>
        <div className="min-w-0 space-y-4 xl:overflow-y-auto">
          <ClientSummary client={selectedClient} />
          <div className="grid gap-4 md:grid-cols-2">
            <PerceptionHistory entries={selectedClient.perception} />
            <InvestmentProfile portfolio={selectedClient.portfolio} />
          </div>
          <RadarPerfil client={selectedClient} hoje={data?.generatedAt ?? ''} />
          <ClientWorkspace key={selectedClient.id} client={selectedClient} onUpdated={updated} />
          <NewsSection client={selectedClient} />
        </div>

        <div className="flex min-h-0 flex-col lg:col-span-2 xl:col-span-1">
          <AssistantPanel key={selectedClient.id} client={selectedClient} onUpdated={updated} />
        </div>
        </> : <div className="p-5 text-sm text-ink-muted">Nenhum cliente cadastrado. Inicialize a base fictícia com o comando seed do backend.</div>}
      </main>}
    </div>
  )
}
