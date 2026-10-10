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
import { useApiResource } from '@/hooks/useApiResource'

interface ChatTurn {
  id: number; request_id: string; pergunta: string; resposta: string; fontes: string[];
  nota_sugerida: string | null; nota_id: number | null; error?: string
}
interface ChatView {
  configurado: boolean; modelo: string; mensagens: ChatTurn[];
  notas: { id: number; texto: string; evidencia: string; registrada_em: string }[]
}

interface AssistantPanelProps {
  client: Client
  onUpdated: () => Promise<void>
}

export function AssistantPanel({ client, onUpdated }: AssistantPanelProps) {
  const [followUps, setFollowUps] = useState<ChatTurn[]>([])
  const [busy, setBusy] = useState(false)
  const [noteError, setNoteError] = useState('')
  const { data: chat, error: chatError, loading, refresh } = useApiResource<ChatView>(
    `/api/pulse/clientes/${client.id}/chat`, '')
  const turns = [...(chat?.mensagens.filter((m) => !followUps.some((f) => f.request_id === m.request_id)) ?? []), ...followUps]
  const { assistant } = client
  const firstName = client.name.split(' ')[0]

  async function handleAsk(question: string, retryIndex?: number) {
    if (busy) return
    setBusy(true)
    const index = retryIndex ?? followUps.length
    const requestId = retryIndex === undefined ? crypto.randomUUID() : followUps[index].request_id
    const pending: ChatTurn = { id: 0, request_id: requestId, pergunta: question, resposta: '', fontes: [], nota_sugerida: null, nota_id: null }
    setFollowUps((current) => retryIndex === undefined ? [...current, pending] : current.map((entry, n) => n === index ? pending : entry))
    try {
      const result = await api<ChatTurn>(`/api/pulse/clientes/${client.id}/chat`, { method: 'POST', body: { pergunta: question, request_id: requestId } })
      setFollowUps((current) => current.map((entry, n) => n === index ? result : entry))
    } catch (e) {
      setFollowUps((current) => current.map((entry, n) => n === index ? { ...pending, error: e instanceof Error ? e.message : 'Consulta não concluída.' } : entry))
    } finally { setBusy(false) }
  }

  async function confirmNote(turn: ChatTurn) {
    if (busy) return
    setBusy(true); setNoteError('')
    try {
      const updated = await api<ChatTurn>(`/api/pulse/clientes/${client.id}/chat/${turn.id}/nota`, { method: 'POST' })
      setFollowUps((rows) => rows.map((r) => r.id === turn.id ? updated : r))
      await refresh()
      await onUpdated()
    } catch (e) { setNoteError(e instanceof Error ? e.message : 'Não foi possível registrar a nota.') }
    finally { setBusy(false) }
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

        {chatError && <p role="alert" className="text-xs text-negative">{chatError}<Button onClick={() => void refresh()}>Tentar novamente</Button></p>}
        {loading && <p role="status" className="text-xs text-ink-muted">Carregando conversa…</p>}
        {chat && !chat.configurado && <p role="alert" className="text-xs text-brand">Configure OPENAI_API_KEY no backend deste computador para conversar.</p>}
        {!!chat?.notas.length && <details className="rounded-lg border border-line p-3"><summary className="cursor-pointer text-xs font-medium">Notas confirmadas do assessor ({chat.notas.length})</summary>
          {chat.notas.map((n) => <p key={n.id} className="mt-2 whitespace-pre-wrap text-xs leading-5">{n.texto}</p>)}
        </details>}
        {turns.map((entry) => (
          <div key={entry.request_id} className="space-y-2">
            <UserMessage>{entry.pergunta}</UserMessage>
            {entry.resposta && <><p className="whitespace-pre-wrap text-xs leading-6">{entry.resposta}</p><ul className="text-[10px] text-ink-muted">{entry.fontes.map((s) => <li key={s}>{s}</li>)}</ul></>}
            {entry.nota_sugerida && <div className="rounded-lg border border-line p-3">
              <p className="text-[11px] font-medium">{entry.nota_id ? 'Nota registrada no contexto' : 'Informação para registrar no contexto'}</p>
              <p className="mt-2 whitespace-pre-wrap text-xs leading-5">{entry.nota_sugerida}</p>
              {!entry.nota_id && <Button disabled={busy} className="mt-3" onClick={() => void confirmNote(entry)}>Confirmar e salvar nota</Button>}
            </div>}
            {entry.error && <div role="alert" className="text-xs text-negative">{entry.error}<Button onClick={() => void handleAsk(entry.pergunta, followUps.findIndex((f) => f.request_id === entry.request_id))} disabled={busy}>Tentar novamente</Button></div>}
            {!entry.resposta && !entry.error && <p role="status" className="text-[11px] text-ink-muted">Preparando resposta com OpenAI…</p>}
          </div>
        ))}
        {noteError && <p role="alert" className="text-xs text-negative">{noteError}</p>}
      </div>

      <div className="mt-3">
        <AskAssistantForm placeholder="Converse, peça ajuda ou informe algo novo…" onAsk={(q) => void handleAsk(q)} disabled={busy || loading || !chat?.configurado} />
        <p className="mt-2 text-[9px] text-ink-muted">
          OpenAI · Conversa salva por cliente · Notas após sua confirmação
        </p>
      </div>
    </Panel>
  )
}
