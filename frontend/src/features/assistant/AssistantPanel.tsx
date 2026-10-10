import { useState } from 'react'
import { Panel } from '@/components/ui/Panel'
import wave from '@/assets/onda-pulse.png'
import type { Client } from '@/types/client'
import { AskAssistantForm } from './AskAssistantForm'
import { OpeningSuggestion } from './OpeningSuggestion'
import { UserMessage } from './UserMessage'
import { api } from '@/lib/api'
import { atualizarNoticias } from '@/lib/noticias'
import { Button } from '@/components/ui/Button'
import { ClientBriefing } from './ClientBriefing'
import { useApiResource } from '@/hooks/useApiResource'

interface ChatTurn {
  id: number; request_id: string; pergunta: string; resposta: string; fontes: string[];
  nota_sugerida: string | null; nota_id: number | null; error?: string
  contexto_sugerido?: { categoria: string; assunto: string; sujeito: string; valor: string; trecho: string }[]
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
  const [newsNotice, setNewsNotice] = useState('')
  const { data: chat, error: chatError, loading, refresh } = useApiResource<ChatView>(
    `/api/pulse/clientes/${client.id}/chat`, (client.sourceDocuments ?? []).map((d) => `${d.id}:${d.versao}`).join('|'))
  const turns = [...(chat?.mensagens.filter((m) => !followUps.some((f) => f.request_id === m.request_id)) ?? []), ...followUps]
  const { assistant } = client
  const firstName = client.name.split(' ')[0]

  async function handleAsk(question: string, retryIndex?: number) {
    if (busy) return
    setBusy(true); setNewsNotice('')
    const index = retryIndex ?? followUps.length
    const requestId = retryIndex === undefined ? crypto.randomUUID() : followUps[index].request_id
    const pending: ChatTurn = { id: 0, request_id: requestId, pergunta: question, resposta: '', fontes: [], nota_sugerida: null, nota_id: null }
    setFollowUps((current) => retryIndex === undefined ? [...current, pending] : current.map((entry, n) => n === index ? pending : entry))
    try {
      const result = await api<ChatTurn>(`/api/pulse/clientes/${client.id}/chat`, { method: 'POST', signal: AbortSignal.timeout(60_000), body: { pergunta: question, request_id: requestId } })
      setFollowUps((current) => current.map((entry, n) => n === index ? result : entry))
      if (result.nota_id) {
        await refresh().catch(() => {}); await onUpdated()
        if (result.contexto_sugerido?.some((item) => item.categoria === 'interesse')) {
          setNewsNotice('Interesses salvos. Atualizando notícias…')
          const collectionError = await atualizarNoticias(client.id)
          await onUpdated()
          setNewsNotice(collectionError || 'Interesses e notícias atualizados automaticamente.')
        }
      }
    } catch (e) {
      setFollowUps((current) => current.map((entry, n) => n === index ? { ...pending, error: e instanceof Error ? e.message : 'Consulta não concluída.' } : entry))
    } finally { setBusy(false) }
  }

  return (
    <Panel className="flex min-h-0 flex-1 flex-col px-5 pt-5 pb-3" aria-labelledby="assistant-title">
      <header className="flex items-start gap-4 border-b border-line px-2 pb-3.5">
        <img src={wave} alt="" aria-hidden className="mt-0.5 h-5 w-auto shrink-0" />
        <div>
          <h2 id="assistant-title" className="text-base font-semibold">
            Pulse IA
          </h2>
          <p className="mt-1 text-[11px] text-ink-muted">Seu assistente de relacionamento · Prepare o atendimento de {firstName}.</p>
        </div>
      </header>

      <div className="-mx-1 mt-4 min-h-0 flex-1 space-y-3.5 overflow-y-auto px-1 pb-1">
        <UserMessage>{assistant.question}</UserMessage>

        <ClientBriefing client={client} onUpdated={onUpdated} />

        <OpeningSuggestion openings={assistant.openings} />

        {chatError && <p role="alert" className="text-xs text-negative">{chatError}<Button onClick={() => void refresh()}>Tentar novamente</Button></p>}
        {loading && <p role="status" className="text-xs text-ink-muted">Carregando conversa…</p>}
        {chat && !chat.configurado && <p role="alert" className="text-xs text-brand">Configure OPENAI_API_KEY no backend deste computador para conversar.</p>}
        {!!chat?.notas.length && <details className="rounded-lg border border-line p-3"><summary className="cursor-pointer text-xs font-medium">Informações registradas pelo assessor ({chat.notas.length})</summary>
          {chat.notas.map((n) => <p key={n.id} className="mt-2 whitespace-pre-wrap text-xs leading-5">{n.texto}</p>)}
        </details>}
        {turns.map((entry) => (
          <div key={entry.request_id} className="space-y-2">
            <UserMessage>{entry.pergunta}</UserMessage>
            {entry.resposta && <><p className="whitespace-pre-wrap text-xs leading-6">{entry.resposta}</p><ul className="text-[10px] text-ink-muted">{entry.fontes.map((s) => <li key={s}>{s}</li>)}</ul></>}
            {entry.nota_sugerida && <div className="rounded-lg border border-line p-3">
              <p className="text-[11px] font-medium">{entry.nota_id ? 'Contexto salvo automaticamente' : 'Nota anterior não registrada'}</p>
              <p className="mt-2 whitespace-pre-wrap text-xs leading-5">{entry.nota_sugerida}</p>
              {!!entry.contexto_sugerido?.length && <ul className="mt-2 space-y-2 text-[11px] text-ink-muted">{entry.contexto_sugerido.map((c, i) => <li key={`${c.assunto}-${i}`}><strong>{c.categoria.replace('_', ' ')} · {c.sujeito}:</strong> {c.valor}<span className="mt-1 block text-[10px]">Sua mensagem: “{c.trecho}”</span></li>)}</ul>}

            </div>}
            {entry.error && <div role="alert" className="text-xs text-negative">{entry.error}<Button onClick={() => void handleAsk(entry.pergunta, followUps.findIndex((f) => f.request_id === entry.request_id))} disabled={busy}>Tentar novamente</Button></div>}
            {!entry.resposta && !entry.error && <p role="status" className="text-[11px] text-ink-muted">Preparando resposta com OpenAI…</p>}
          </div>
        ))}
      </div>

      <div className="mt-3">
        {newsNotice && <p role="status" className="mb-2 text-xs text-ink-muted">{newsNotice}</p>}
        <AskAssistantForm placeholder="Converse, peça ajuda ou informe algo novo…" onAsk={(q) => void handleAsk(q)} disabled={busy || loading || !chat?.configurado} />
        <p className="mt-2 text-[9px] text-ink-muted">
          Informe interesses, preferências e contexto aqui · Salvos automaticamente
        </p>
      </div>
    </Panel>
  )
}
