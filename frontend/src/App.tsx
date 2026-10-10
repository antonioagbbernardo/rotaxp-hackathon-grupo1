import { useState } from 'react'
import { AppHeader } from '@/components/layout/AppHeader'
import { clients } from '@/data/clients'
import { AssistantPanel } from '@/features/assistant/AssistantPanel'
import { ClientSummary } from '@/features/client-overview/ClientSummary'
import { InvestmentProfile } from '@/features/client-overview/InvestmentProfile'
import { PerceptionHistory } from '@/features/client-overview/PerceptionHistory'
import { ClientSidebar } from '@/features/clients/ClientSidebar'
import { NewsSection } from '@/features/news/NewsSection'

const advisor = { name: 'Lucas Martins', role: 'Assessor de investimentos' }

export function App() {
  const [selectedClientId, setSelectedClientId] = useState(clients[0].id)
  const selectedClient = clients.find((client) => client.id === selectedClientId) ?? clients[0]

  return (
    <div className="flex min-h-dvh flex-col xl:h-dvh">
      <AppHeader advisor={advisor} isDemo />

      <main className="grid flex-1 gap-6 p-6 lg:grid-cols-[300px_1fr] xl:min-h-0 xl:grid-cols-[300px_minmax(0,1fr)_450px]">
        <ClientSidebar
          clients={clients}
          selectedClientId={selectedClient.id}
          onSelectClient={setSelectedClientId}
        />

        <div className="min-w-0 space-y-4 xl:overflow-y-auto">
          <ClientSummary client={selectedClient} />
          <div className="grid gap-4 md:grid-cols-2">
            <PerceptionHistory entries={selectedClient.perception} />
            <InvestmentProfile portfolio={selectedClient.portfolio} />
          </div>
          <NewsSection client={selectedClient} />
        </div>

        <div className="flex min-h-0 flex-col lg:col-span-2 xl:col-span-1">
          <AssistantPanel key={selectedClient.id} client={selectedClient} />
        </div>
      </main>
    </div>
  )
}
