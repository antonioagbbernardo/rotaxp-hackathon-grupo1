import { Avatar } from '@/components/ui/Avatar'
import { Badge, type BadgeTone } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { SentimentFace } from '@/components/ui/SentimentFace'
import { priorityLabel, priorityTone, sentimentLabel } from '@/lib/sentiment'
import { formatMonth } from '@/lib/format'
import type { Client, ClientStatus } from '@/types/client'
import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { MessageSquare } from 'lucide-react'
import { RecentMessagesModal } from './RecentMessagesModal'

const statusBadge: Record<ClientStatus, { label: string; tone: BadgeTone }> = {
  opportunity: { label: "Oportunidade", tone: "positive" },
  attention: { label: "Atenção", tone: "negative" },
  stable: { label: "Estável", tone: "neutral" },
};

interface ClientSummaryProps {
  client: Client;
  onUpdated?: () => Promise<void>;
}

export function ClientSummary({ client, onUpdated }: ClientSummaryProps) {
  const status = statusBadge[client.status];
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [showMessagesModal, setShowMessagesModal] = useState(false)
  const totalMensagens = (client.interactions?.length ?? 0) + (client.sourceDocuments?.filter((f) => f.tipo === 'interacao').length ?? 0)
  async function atualizarHumor(revisar = false) {
    setBusy(true); setError('')
    try {
      await api(`/api/pulse/clientes/${client.id}/humor${revisar ? '/revisar' : ''}`, { method: 'POST', ...(revisar ? { body: { assinatura: client.mood?.assinatura } } : {}) })
      await onUpdated?.()
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível analisar as interações.') }
    finally { setBusy(false) }
  }

  return (
    <Panel className="px-6 pt-6 pb-4">
      <div className="flex items-start gap-4">
        <Avatar name={client.name} src={client.photoUrl} size="lg" />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold">{client.name}</h1>
            <Badge tone={client.priority ? priorityTone[client.priority] : status.tone} withDot>
              Prioridade de atendimento: {client.priority ? priorityLabel[client.priority] : 'não calculada'}
            </Badge>
          </div>
          <p className="mt-1 text-[11px] text-ink-muted">
            {client.clientSince ? `Cliente desde ${formatMonth(client.clientSince)}` : 'Data de cadastro não informada'} · Último contato{' '}
            {client.lastContactDays === null ? 'sem registro' : client.lastContactDays === 0 ? 'hoje' : `há ${client.lastContactDays} ${client.lastContactDays === 1 ? 'dia' : 'dias'}`}
          </p>
          <p className="mt-2 flex items-center gap-2 text-xs">
            <SentimentFace sentiment={client.sentiment} className="size-5" label={`Humor: ${sentimentLabel[client.sentiment]}`} />
            <span>Humor inferido: <strong className="font-medium">{sentimentLabel[client.sentiment]}</strong></span>
          </p>
          {client.mood && <div className="mt-2 space-y-2 text-[11px] text-ink-muted">
            <p>{client.mood.motivo}</p>
            {client.mood.evidencias.map((e, i) => <blockquote key={`${e.fonte}-${i}`} className="border-l-2 border-brand pl-2">“{e.trecho}” <span className="block text-[10px]">Fonte: {e.fonte.replace('interacao-', 'interação #')}</span></blockquote>)}
            <p>{client.mood.estado === 'atualizado' ? (client.mood.revisado_em ? 'Inferência revisada pelo assessor.' : 'Hipótese baseada nas conversas · confira as evidências.') : client.mood.estado === 'pendente' && client.mood.configurado ? 'Analisando as interações…' : client.mood.estado === 'processando' ? 'Análise em andamento…' : ''}</p>
            {!client.mood.configurado && <p>Configure a chave OpenAI no backend para inferir o humor.</p>}
            {client.mood.estado === 'atualizado' && !client.mood.revisado_em && <Button disabled={busy} onClick={() => { void atualizarHumor(true) }}>Marcar como revisado</Button>}
            {client.mood.estado === 'falhou' && <Button disabled={busy} onClick={() => { void atualizarHumor() }}>{busy ? 'Analisando…' : 'Tentar inferir novamente'}</Button>}
            {error && <p role="alert" className="text-negative">{error}</p>}
          </div>}
          <p className="mt-2 text-[11px] text-ink-muted">Avaliação do assessor: {client.relationshipLabel ?? 'Não avaliado'}</p>
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

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3.5 text-[11px]">
        <dl className="flex flex-wrap items-center gap-x-6 gap-y-1 text-ink-muted">
          <div>
            <dt className="inline font-medium">WhatsApp: </dt>
            <dd className="inline">{client.whatsapp || 'não informado'}</dd>
          </div>
          <div>
            <dt className="inline font-medium">E-mail: </dt>
            <dd className="inline">{client.email || 'E-mail não informado'}</dd>
          </div>
        </dl>
        <Button
          onClick={() => setShowMessagesModal(true)}
          variant="secondary"
          className="flex h-8 items-center gap-1.5 px-3 text-xs text-ink hover:border-brand/50 hover:text-brand"
        >
          <MessageSquare className="size-3.5 text-brand" />
          <span>Mensagens recentes</span>
          {totalMensagens > 0 && (
            <span className="rounded-full bg-surface px-1.5 py-0.5 text-[10px] font-medium text-ink-muted">
              {totalMensagens}
            </span>
          )}
        </Button>
      </div>

      <RecentMessagesModal
        client={client}
        isOpen={showMessagesModal}
        onClose={() => setShowMessagesModal(false)}
      />
    </Panel>
  );
}
