import { Avatar } from '@/components/ui/Avatar'
import { Badge, type BadgeTone } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { formatMonth } from '@/lib/format'
import type { Client, ClientStatus } from '@/types/client'

const statusBadge: Record<ClientStatus, { label: string; tone: BadgeTone }> = {
  opportunity: { label: "Oportunidade", tone: "positive" },
  attention: { label: "Atenção", tone: "negative" },
  stable: { label: "Estável", tone: "neutral" },
};

interface ClientSummaryProps {
  client: Client;
}

export function ClientSummary({ client }: ClientSummaryProps) {
  const status = statusBadge[client.status];

  return (
    <Panel className="px-6 pt-6 pb-4">
      <div className="flex items-start gap-4">
        <Avatar name={client.name} size="lg" />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold">{client.name}</h1>
            <Badge tone={status.tone} withDot className="w-30">
              Prioridade: {client.priority === 'alta' ? 'Alta' : client.priority === 'media' ? 'Média' : 'Baixa'}
            </Badge>
          </div>
          <p className="mt-1 text-[11px] text-ink-muted">
            {client.clientSince ? `Cliente desde ${formatMonth(client.clientSince)}` : 'Data de cadastro não informada'} · Último contato{' '}
            {client.lastContactDays === null ? 'sem registro' : client.lastContactDays === 0 ? 'hoje' : `há ${client.lastContactDays} ${client.lastContactDays === 1 ? 'dia' : 'dias'}`}
            {' · '}Relacionamento: {client.relationshipLabel ?? 'Não avaliado'}
          </p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {client.tags.map((tag) => (
              <li key={tag.label}>
                <Badge tone={tag.highlighted ? "positive" : "neutral"}>
                  {tag.label}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-1 gap-2 border-t border-line pt-3.5 text-[11px] sm:grid-cols-2 sm:items-center">
        <div className="text-ink-muted">
          <dt className="inline">WhatsApp </dt>
          <dd className="inline">{client.whatsapp || 'não informado'}</dd>
        </div>
        <div className="text-ink-muted">
          <dt className="sr-only">E-mail</dt>
          <dd>{client.email || 'E-mail não informado'}</dd>
        </div>
      </dl>
    </Panel>
  );
}
