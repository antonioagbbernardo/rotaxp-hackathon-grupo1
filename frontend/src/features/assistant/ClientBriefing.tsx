import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/format'
import type { Client, ResumoIA, TrechoResumoIA } from '@/types/client'

function Sources({ sources }: { sources: string[] }) {
  return <details className="mt-2 text-[10px] leading-relaxed text-ink-muted">
    <summary className="cursor-pointer">Ver fontes</summary>
    <ul className="mt-1 space-y-1 break-words">{sources.map((s) => <li key={s}>{s}</li>)}</ul>
  </details>
}

function BriefingSection({ title, items }: { title: string; items: TrechoResumoIA[] }) {
  if (!items.length) return null
  return <section className="border-t border-line pt-3">
    <h4 className="text-xs font-semibold">{title}</h4>
    <ul className="mt-2 space-y-3">
      {items.map((item, i) => <li key={i} className="flex gap-2 text-[13px] leading-relaxed">
        <span aria-hidden className="mt-0.5 text-brand">•</span>
        <div className="min-w-0"><p className="break-words">{item.texto}</p><Sources sources={item.fontes} /></div>
      </li>)}
    </ul>
  </section>
}

export function ClientBriefing({ client, onUpdated }: { client: Client; onUpdated: () => Promise<void> }) {
  const [generated, setGenerated] = useState<ResumoIA | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const { assistant } = client
  const state = assistant.aiSummary
  // Uma atualização dos fatos esconde a resposta local de uma versão anterior.
  const summary = generated?.assinatura === state?.assinatura ? generated : state?.resumo
  const facts = assistant.summaryItems ?? [assistant.summary]

  async function generate() {
    if (busy) return
    setBusy(true); setError('')
    try {
      const result = await api<{ resumo: ResumoIA }>(`/api/pulse/clientes/${client.id}/resumo-ia`, { method: 'POST' })
      setGenerated(result.resumo)
      await onUpdated()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Não foi possível preparar a síntese.')
    } finally { setBusy(false) }
  }

  return <div className="min-w-0 rounded-xl border border-line bg-surface-raised p-4">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="flex items-center gap-1.5 text-sm font-semibold"><span aria-hidden className="text-brand">✦</span> XP Pulse</h3>
      {client.priority && <Badge tone={client.priority === 'alta' ? 'negative' : 'neutral'}>Prioridade de atendimento: {client.priority === 'alta' ? 'Alta' : client.priority === 'media' ? 'Média' : 'Baixa'}</Badge>}
    </div>
    <p className="mt-2 text-[11px] leading-relaxed text-ink-muted">Relacionamento: {client.relationshipLabel ?? 'Não avaliado'} · Avaliação do assessor</p>

    {summary ? <div className="mt-4 space-y-3.5">
      <section>
        <h4 className="text-xs font-semibold">Visão geral</h4>
        <p className="mt-2 break-words text-[13px] leading-relaxed">{summary.visao_geral.texto}</p>
        <Sources sources={summary.visao_geral.fontes} />
      </section>
      <BriefingSection title="Pontos de atenção" items={summary.pontos_atencao} />
      <BriefingSection title="Antes do contato" items={summary.antes_contato} />
      <p className="border-t border-line pt-3 text-[10px] leading-relaxed text-ink-muted">
        Síntese por IA · Revise antes do atendimento.<br />
        {formatDate(summary.gerado_em)} · {summary.modelo}
      </p>
      <details className="text-xs">
        <summary className="cursor-pointer text-ink-muted">Conferir registros da base</summary>
        <ul className="mt-3 space-y-2 text-[12px] leading-relaxed">{facts.map((f, i) => <li key={i} className="break-words">{f}</li>)}</ul>
        <Sources sources={assistant.summarySources ?? []} />
      </details>
    </div> : <div className="mt-4">
      <h4 className="text-xs font-semibold">Resumo dos registros</h4>
      <ul className="mt-3 space-y-2 text-[13px] leading-relaxed">{facts.map((f, i) => <li key={i} className="flex gap-2"><span aria-hidden className="text-ink-muted">•</span><span className="min-w-0 break-words">{f}</span></li>)}</ul>
      <Sources sources={assistant.summarySources ?? []} />
    </div>}

    {!summary && <div className="mt-4 border-t border-line pt-3">
      <Button variant="primary" onClick={() => void generate()} disabled={busy || !state?.configurado} className="h-auto min-h-9 w-full py-2 text-center">
        {busy ? 'Preparando síntese…' : error ? 'Tentar síntese novamente' : 'Preparar resumo com IA'}
      </Button>
      <p className="mt-2 text-[10px] leading-relaxed text-ink-muted">
        {state?.configurado ? 'Organiza os fatos para o assessor revisar antes do contato.' : 'A síntese por IA precisa de configuração no backend.'}
      </p>
    </div>}
    {busy && <p role="status" className="mt-2 text-[11px] text-ink-muted">Consultando a IA. Isso pode levar alguns segundos.</p>}
    {error && <p role="alert" className="mt-2 break-words text-xs text-negative">{error}</p>}
  </div>
}
