import { useState } from 'react'
import { Panel } from '@/components/ui/Panel'
import wave from '@/assets/onda-pulse.png'
import type { Client } from '@/types/client'
import { AskAssistantForm } from './AskAssistantForm'
import { InsightCard } from './InsightCard'
import { OpeningSuggestion } from './OpeningSuggestion'
import { UserMessage } from './UserMessage'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { ClientBriefing } from './ClientBriefing'

interface AssistantPanelProps {
  client: Client
  onUpdated: () => Promise<void>
}

export function AssistantPanel({ client, onUpdated }: AssistantPanelProps) {
  const [followUps, setFollowUps] = useState<{ question: string; answer?: string; sources?: string[]; error?: string }[]>([])
  const [busy, setBusy] = useState(false)
  const { assistant } = client
  const firstName = client.name.split(' ')[0]

  async function handleAsk(question: string, retryIndex?: number) {
    if (busy) return
    setBusy(true)
    const index = retryIndex ?? followUps.length
    setFollowUps((current) => retryIndex === undefined ? [...current, { question }] : current.map((entry, n) => n === index ? { question } : entry))
    try {
      const result = await api<{ resposta: string; fontes: string[] }>(`/api/pulse/clientes/${client.id}/perguntar`, { method: 'POST', body: { pergunta: question } })
      setFollowUps((current) => current.map((entry, n) => n === index ? { question, answer: result.resposta, sources: result.fontes } : entry))
    } catch (e) {
      setFollowUps((current) => current.map((entry, n) => n === index ? { question, error: e instanceof Error ? e.message : 'Consulta não concluída.' } : entry))
    } finally { setBusy(false) }
  }

  return (
    <Panel className="flex min-h-0 flex-1 flex-col px-5 pt-5 pb-3" aria-labelledby="assistant-title">
      <header className="flex items-start gap-4 border-b border-line px-2 pb-3.5">
        <img src={wave} alt="" aria-hidden className="mt-0.5 h-5 w-auto shrink-0" />
        <div>
          <h2 id="assistant-title" className="text-base font-semibold">
            Assistente do assessor
          </h2>
          <p className="mt-1 text-[11px] text-ink-muted">Prepare o atendimento de {firstName} com contexto e fontes.</p>
        </div>
      </header>

      <div className="-mx-1 mt-4 min-h-0 flex-1 space-y-3.5 overflow-y-auto px-1 pb-1">
        <UserMessage>{assistant.question}</UserMessage>

        <ClientBriefing client={client} onUpdated={onUpdated} />

        <ol className="space-y-3">
          {assistant.insights.map((insight, index) => (
            <li key={insight.title}>
              <InsightCard insight={insight} position={index + 1} />
            </li>
          ))}
        </ol>

        <OpeningSuggestion openings={assistant.openings} />

        {followUps.map((entry, index) => (
          <div key={index} className="space-y-2">
            <UserMessage>{entry.question}</UserMessage>
            {entry.answer && <><p className="whitespace-pre-wrap text-xs">{entry.answer}</p><ul className="text-[10px] text-ink-muted">{entry.sources?.map((s) => <li key={s}>{s}</li>)}</ul></>}
            {entry.error && <div role="alert" className="text-xs text-negative">{entry.error}<Button onClick={() => void handleAsk(entry.question, index)} disabled={busy}>Tentar novamente</Button></div>}
            {!entry.answer && !entry.error && <p role="status" className="text-[11px] text-ink-muted">Consultando registros…</p>}
          </div>
        ))}
      </div>

      <div className="mt-3">
        <AskAssistantForm placeholder={`Perfil, vencimentos, último contato...`} onAsk={(q) => void handleAsk(q)} disabled={busy} />
        <p className="mt-2 text-[9px] text-ink-muted">
          Consulta por templates com fontes · Sem envio · Dados fictícios
        </p>
      </div>
    </Panel>
  )
}
