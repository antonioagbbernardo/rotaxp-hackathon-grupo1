import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/format'
import type { Client } from '@/types/client'
import { NewsCard } from './NewsCard'

interface NewsSectionProps {
  client: Client
  onUpdated: () => Promise<void>
}

interface InterestProposal {
  id: number; resposta: string; nota_sugerida: string | null; nota_id: number | null;
  contexto_sugerido?: { categoria: string; sujeito: string; valor: string; trecho: string }[]
}

const statusLabel = { nunca: 'Ainda sem coleta', atualizado: 'Coleta do dia', desatualizado: 'Cache de outro dia', falhou: 'Atualização falhou', processando: 'Coleta em andamento' }

export function NewsSection({ client, onUpdated }: NewsSectionProps) {
  const firstName = client.name.split(' ')[0]
  const state = client.newsState
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [interest, setInterest] = useState('')
  const [proposal, setProposal] = useState<InterestProposal | null>(null)
  async function addInterest() {
    if (busy || !interest.trim()) return
    setBusy(true); setError(''); setNotice(''); setProposal(null)
    try {
      const result = await api<InterestProposal>(`/api/pulse/clientes/${client.id}/chat`, { method: 'POST', body: { pergunta: `Informação fornecida pelo assessor sobre os interesses e contexto deste cliente: ${interest.trim()}`, request_id: crypto.randomUUID() } })
      setProposal(result)
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível preparar o interesse.') }
    finally { setBusy(false) }
  }
  async function confirmInterest() {
    if (busy || !proposal) return
    setBusy(true); setError('')
    try {
      await api(`/api/pulse/clientes/${client.id}/chat/${proposal.id}/nota`, { method: 'POST' })
      setProposal(null); setInterest(''); setNotice('Contexto salvo. Os interesses identificados serão usados na seleção de notícias.')
      await onUpdated()
    } catch (e) { setError(e instanceof Error ? e.message : 'Não foi possível salvar o interesse.') }
    finally { setBusy(false) }
  }
  async function collect() {
    if (busy) return
    setBusy(true); setError(''); setNotice('')
    try {
      const result = await api<{ resultados: { assunto: string; estado: string; erro?: { mensagem: string } }[] }>(`/api/clientes/${client.id}/noticias/atualizar`, { method: 'POST' })
      await onUpdated()
      const failures = result.resultados.filter((r) => r.estado === 'erro')
      const updated = result.resultados.filter((r) => r.estado === 'atualizado').length
      const reused = result.resultados.filter((r) => r.estado === 'reutilizado').length
      if (failures.length) setError(failures.map((r) => `${state?.catalogo.find((t) => t.id === r.assunto)?.nome ?? r.assunto}: ${r.erro?.mensagem ?? 'Coleta não concluída.'}`).join(' '))
      if (updated || reused) setNotice(updated ? 'Busca concluída. As notícias disponíveis foram atualizadas.' : 'As notícias já foram consultadas nos últimos dois minutos. Exibindo o resultado mais recente; o provedor pode não ter novos artigos.')
    } catch (e) { setError(e instanceof Error ? e.message : 'Coleta não concluída.') }
    finally { setBusy(false) }
  }

  async function discard(id: string, motivo: string) {
    await api(`/api/clientes/${client.id}/noticias/descartar`, { method: 'POST', body: { artigo_id: id, motivo } })
    await onUpdated()
  }

  return (
    <section aria-labelledby="news-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="news-title" className="text-lg font-semibold">
            Notícias que importam para {firstName}
          </h2>
          <p className="mt-1 text-[11px] text-ink-muted">
            Selecionadas automaticamente pelos interesses identificados. Remova as que não forem pertinentes.
          </p>
        </div>
        <Button onClick={() => void collect()} disabled={busy || !state?.configurado}>
          {busy ? 'Aguarde…' : 'Buscar notícias'}
        </Button>
      </div>

      <details className="mt-3 rounded-lg border border-line p-3 text-xs">
        <summary className="cursor-pointer font-medium">Adicionar interesse ou contexto pelo chat</summary>
        <form className="mt-3 space-y-2" onSubmit={(e) => { e.preventDefault(); void addInterest() }}>
          <label className="block">O que o assessor sabe sobre este cliente
            <input required maxLength={3500} value={interest} onChange={(e) => setInterest(e.target.value)} placeholder="Ex.: acompanha Fórmula 1 e torce pelo Palmeiras" disabled={busy}
              className="mt-2 block w-full rounded-lg border border-line bg-surface p-2" />
          </label>
          <Button type="submit" disabled={busy || !interest.trim()}>Enviar ao assistente</Button>
        </form>
        {proposal && <div className="mt-3 space-y-2">
          <p className="whitespace-pre-wrap leading-5">{proposal.resposta}</p>
          {proposal.nota_sugerida && !proposal.nota_id && <>
            <p className="leading-5">{proposal.nota_sugerida}</p>
            {proposal.contexto_sugerido?.map((c, i) => <p key={i} className="text-[11px] text-ink-muted">{c.categoria} · {c.sujeito}: {c.valor}<span className="block">Sua mensagem: “{c.trecho}”</span></p>)}
            <p className="text-[10px] text-ink-muted">A confirmação atualiza o contexto, substitui informações anteriores do mesmo assunto e alimenta as notícias, preservando o histórico.</p>
            <Button disabled={busy} onClick={() => { void confirmInterest() }}>Confirmar e salvar contexto</Button>
          </>}
        </div>}
      </details>

      <p className="mt-3 text-[10px] leading-relaxed text-ink-muted">NewsAPI pode disponibilizar artigos com atraso conforme o plano. Coleta recente não garante notícia em tempo real. O humor é inferido das interações; as notícias não são recomendações de investimento.</p>
      {state && <div className="mt-3 space-y-3">
        {!state.configurado && <p className="text-xs text-ink-muted">A busca de notícias precisa de configuração no backend.</p>}
        {state.assuntos.some((a) => a.id === 'mercado') && <p className="text-xs text-ink-muted">Sem assunto pessoal identificado no catálogo, mostramos notícias gerais do mercado financeiro.</p>}
        <ul className="space-y-2 text-[11px] leading-relaxed text-ink-muted">
          {state.assuntos.map((t) => <li key={t.id}>
            <span className="font-medium">{t.nome}</span> · {statusLabel[t.estado]}{t.ultima_coleta && ` · Última coleta ${formatDate(t.ultima_coleta)}`}
            {t.erro && <p className="text-negative">{t.erro.mensagem}</p>}
          </li>)}
        </ul>
        <p className="text-[10px] text-ink-muted">Consultas nesta instalação hoje: {state.chamadas_hoje}/{state.limite_diario ?? 'limite não configurado'}. Clientes com o mesmo assunto reutilizam a coleta.</p>
      </div>}
      {busy && <p role="status" className="mt-3 text-xs text-ink-muted">Processando. A busca pode levar alguns segundos.</p>}
      {notice && <p role="status" className="mt-3 text-xs text-ink-muted">{notice}</p>}
      {error && <p role="alert" className="mt-3 text-xs leading-relaxed text-negative">{error}</p>}

      <ul className="mt-4 space-y-4">
        {client.news.length === 0 && <li className="rounded-xl border border-line p-4 text-xs text-ink-muted">Nenhuma notícia disponível para revisão neste cliente. Confira os assuntos e o estado da coleta acima.</li>}
        {client.news.map((news) => (
          <li key={news.id}>
            <NewsCard news={news} pronoun={client.pronoun} onDiscard={discard} />
          </li>
        ))}
      </ul>
    </section>
  )
}
