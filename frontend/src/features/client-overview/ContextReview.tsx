import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { controlClass, MutationForm } from '@/components/ui/MutationForm'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/format'
import type { Client, ContextItem } from '@/types/client'

const states = { pendente: 'Aguardando revisão', confirmado: 'Aprovado', corrigido: 'Corrigido', descartado: 'Descartado', adiado: 'Adiado' }

function ReviewItem({ item, clientId, onUpdated }: { item: ContextItem; clientId: string; onUpdated: () => Promise<void> }) {
  const [action, setAction] = useState('aprovar')
  return <article className="min-w-0 rounded-lg border border-line p-3">
    <p className="text-[10px] text-ink-muted">#{item.id} · {states[item.estado]} · {item.tipo === 'hipotese' ? 'Hipótese' : 'Fato extraído'} · sujeito: {item.sujeito}</p>
    <p className="mt-2 whitespace-pre-wrap text-xs">{item.valor_revisado || item.valor_original}</p>
    {item.valor_revisado && <p className="mt-2 text-[10px] text-ink-muted">Original da IA: {item.valor_original}</p>}
    {item.estado === 'adiado' && <p className="mt-2 text-[10px] text-ink-muted">Retomar em {item.adiado_ate?.split('-').reverse().join('/')}</p>}
    {!item.evidencia_atual && <p className="mt-2 text-xs text-brand">Fonte de versão anterior.</p>}
    {item.conflitos.length > 0 && <p className="mt-2 text-xs text-brand">Possível divergência com #{item.conflitos.join(', #')}. Confira antes de usar.</p>}
    <details className="mt-3">
      <summary className="cursor-pointer text-[11px] text-brand">Evidências e revisões</summary>
      {item.evidencias.map((e, n) => <div key={n} className="mt-2 text-[11px]">
        <p className="text-ink-muted">{e.origem} · {e.registro_id} v{e.versao}{e.campo && ` · campo ${e.campo}`}</p>
        <blockquote className="mt-1 whitespace-pre-wrap border-l border-brand pl-2">{e.trecho}</blockquote>
      </div>)}
      {item.historico_revisoes.map((r) => <p key={r.id} className="mt-2 text-[10px] text-ink-muted">{formatDate(r.revisada_em)} · {r.acao}: {r.motivo}</p>)}
    </details>
    <details className="mt-3">
      <summary className="cursor-pointer text-[11px]">Registrar decisão</summary>
      <MutationForm label="Salvar decisão" onSave={async (fd) => {
        const body: Record<string, unknown> = { acao: action, revisao: item.revisao, motivo: fd.get('motivo') }
        if (action === 'corrigir') body.valor = fd.get('valor')
        if (action === 'adiar') body.adiado_ate = fd.get('adiado_ate')
        await api(`/api/clientes/${clientId}/contexto/${item.id}/revisar`, { method: 'POST', body })
        await onUpdated()
      }}>
        <label className="block text-xs">Ação<select className={`${controlClass} mt-1`} value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="aprovar">Aprovar</option><option value="corrigir">Corrigir</option><option value="descartar">Descartar</option><option value="adiar">Adiar</option>
        </select></label>
        {action === 'corrigir' && <label className="block text-xs">Valor corrigido<textarea name="valor" rows={2} required maxLength={500} className={`${controlClass} mt-1`} defaultValue={item.valor_revisado || item.valor_original} /></label>}
        {action === 'adiar' && <label className="block text-xs">Retomar revisão em<input name="adiado_ate" type="date" required className={`${controlClass} mt-1`} /></label>}
        <label className="block text-xs">Motivo da decisão<input name="motivo" required maxLength={1000} className={`${controlClass} mt-1`} /></label>
      </MutationForm>
    </details>
    <details className="mt-3">
      <summary className="cursor-pointer text-[11px]">Assunto: {item.bloqueado ? 'bloqueado para contato' : 'sem bloqueio'}</summary>
      <p className="mt-2 text-[10px] text-ink-muted">Permissão individual. O contexto e suas evidências permanecem.</p>
      <MutationForm label={item.bloqueado ? 'Permitir assunto' : 'Bloquear assunto'} onSave={async (fd) => {
        await api(`/api/clientes/${clientId}/assuntos/${encodeURIComponent(item.assunto)}`, { method: 'POST', body: { bloqueado: !item.bloqueado, motivo: fd.get('motivo') } })
        await onUpdated()
      }}><label className="block text-xs">Motivo para alterar o assunto<input name="motivo" required maxLength={1000} className={`${controlClass} mt-1`} /></label></MutationForm>
    </details>
  </article>
}

export function ContextReview({ client, onUpdated }: { client: Client; onUpdated: () => Promise<void> }) {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const context = client.context
  if (!context) return null
  const pending = context.itens.filter((i) => i.estado === 'pendente')
  const reviewed = context.itens.filter((i) => i.estado !== 'pendente')
  async function process() {
    if (busy) return
    setBusy(true); setError(''); setMessage('Analisando fontes novas…')
    try {
      const r = await api<{ novos: number; reutilizado: boolean }>(`/api/clientes/${client.id}/contexto/processar`, { method: 'POST' })
      setMessage(r.reutilizado ? 'Sem fontes novas. Contexto reutilizado.' : `${r.novos} proposta(s) gerada(s) para revisão.`)
      await onUpdated()
    } catch (e) { setMessage(''); setError(e instanceof Error ? e.message : 'Análise não concluída.') }
    finally { setBusy(false) }
  }
  return <Panel className="min-w-0 p-5">
    <h2 className="text-sm font-medium">Contexto e revisão do assessor</h2>
    <p className="mt-2 text-[11px] text-ink-muted">A IA prepara propostas. Confira as evidências e decida o que usar no atendimento.</p>
    <p className="mt-2 text-[10px] text-ink-muted">{context.fontes_novas} fonte(s) nova(s) · {context.modelo}{!context.configurado && ' · chave não configurada'}</p>
    <Button className="mt-3" onClick={() => void process()} disabled={busy}>{busy ? 'Analisando…' : 'Processar fontes com IA'}</Button>
    {message && <p role="status" className="mt-2 text-xs text-positive">{message}</p>}
    {error && <p role="alert" className="mt-2 text-xs text-negative">{error} Contexto anterior preservado.</p>}
    <details open className="mt-4">
      <summary className="cursor-pointer text-xs font-medium">Fila de revisão ({pending.length})</summary>
      <div className="mt-3 space-y-3">{pending.length ? pending.map((i) => <ReviewItem key={`${i.id}-${i.revisao}`} item={i} clientId={client.id} onUpdated={onUpdated} />) : <p className="text-xs text-ink-muted">Nenhuma proposta pendente.</p>}</div>
    </details>
    <details className="mt-4"><summary className="cursor-pointer text-xs font-medium">Decisões registradas ({reviewed.length})</summary>
      <div className="mt-3 space-y-3">{reviewed.map((i) => <ReviewItem key={`${i.id}-${i.revisao}`} item={i} clientId={client.id} onUpdated={onUpdated} />)}</div>
    </details>
  </Panel>
}
