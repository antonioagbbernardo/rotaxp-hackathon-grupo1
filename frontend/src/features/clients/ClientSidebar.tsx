import { Badge } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { useClientFilters } from '@/hooks/useClientFilters'
import type { ClientListItem } from '@/types/client'
import { Button } from '@/components/ui/Button'
import { ClientCard } from './ClientCard'
import { ClientFilterTabs } from './ClientFilterTabs'
import { ClientSearch } from './ClientSearch'

interface ClientSidebarProps {
  clients: ClientListItem[]
  selectedClientId: string
  onSelectClient: (clientId: string) => void
  pagination?: { page: number; total: number; pages: number }
  onPage?: (page: number) => void
}

export function ClientSidebar({ clients, selectedClientId, onSelectClient, pagination, onPage }: ClientSidebarProps) {
  const { query, setQuery, filter, setFilter, visibleClients, counts } = useClientFilters(clients)

  return (
    <Panel className="flex min-h-0 flex-col p-5" aria-labelledby="clients-title">
      <div className="flex items-center gap-4">
        <h2 id="clients-title" className="text-lg font-semibold">
          Meus clientes
        </h2>
        <Badge>{pagination?.total ?? counts.all} clientes</Badge>
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

      {pagination && pagination.pages > 1 && <div className="mt-3 space-y-2 text-xs">
        <p>Busca e filtros nesta página · {pagination.page}/{pagination.pages}</p>
        <div className="flex gap-2"><Button disabled={pagination.page<=1} onClick={() => onPage?.(pagination.page-1)}>Anterior</Button>
          <Button disabled={pagination.page>=pagination.pages} onClick={() => onPage?.(pagination.page+1)}>Próxima</Button></div>
      </div>}

      <p className="mt-4 border-t border-line pt-4 text-[10px] leading-relaxed text-ink-muted">
        Relacionamento informado pelo assessor.
        <br />
        Prioridade calculada pelos alertas pendentes.
      </p>
    </Panel>
  )
}
