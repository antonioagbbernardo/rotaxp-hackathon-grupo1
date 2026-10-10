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

const statusLabel = { nunca: 'Ainda sem coleta', atualizado: 'Coleta do dia', desatualizado: 'Cache de outro dia', falhou: 'Atualização falhou', processando: 'Coleta em andamento' }

export function NewsSection({ client, onUpdated }: NewsSectionProps) {
  const firstName = client.name.split(' ')[0]
  const state = client.newsState
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
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
