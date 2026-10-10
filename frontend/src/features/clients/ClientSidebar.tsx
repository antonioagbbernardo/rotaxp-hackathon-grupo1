import { Badge } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { useClientFilters } from '@/hooks/useClientFilters'
import type { Client } from '@/types/client'
import { ClientCard } from './ClientCard'
import { ClientFilterTabs } from './ClientFilterTabs'
import { ClientSearch } from './ClientSearch'

interface ClientSidebarProps {
  clients: Client[]
  selectedClientId: string
  onSelectClient: (clientId: string) => void
}

export function ClientSidebar({ clients, selectedClientId, onSelectClient }: ClientSidebarProps) {
  const { query, setQuery, filter, setFilter, visibleClients, counts } = useClientFilters(clients)

  return (
    <Panel className="flex min-h-0 flex-col p-5" aria-labelledby="clients-title">
      <div className="flex items-center gap-4">
        <h2 id="clients-title" className="text-lg font-semibold">
          Meus clientes
        </h2>
        <Badge>{counts.all} clientes</Badge>
      </div>

      <div className="mt-4 flex items-center gap-2">
        <ClientSearch value={query} onChange={setQuery} />
      </div>

      <div className="mt-4">
        <ClientFilterTabs value={filter} counts={counts} onChange={setFilter} />
      </div>

      <h3 className="mt-7 mb-3 text-[10px] font-medium tracking-wide text-ink-muted uppercase">
        Prioridade de contato
      </h3>

      <ul className="-mx-2 min-h-0 flex-1 space-y-2 overflow-y-auto px-2">
        {visibleClients.map((client) => (
          <li key={client.id}>
            <ClientCard
              client={client}
              isSelected={client.id === selectedClientId}
              onSelect={onSelectClient}
            />
          </li>
        ))}
        {visibleClients.length === 0 && (
          <li className="py-8 text-center text-xs text-ink-muted">Nenhum cliente encontrado.</li>
        )}
      </ul>

      <p className="mt-4 border-t border-line pt-4 text-[10px] leading-relaxed text-ink-muted">
        Relacionamento informado pelo assessor.
        <br />
        Prioridade calculada pelos alertas pendentes.
      </p>
    </Panel>
  )
}
