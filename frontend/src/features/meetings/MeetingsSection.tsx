import { CalendarDays } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { controlClass, MutationForm } from '@/components/ui/MutationForm'
import { useApiResource } from '@/hooks/useApiResource'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/format'
import type { Reuniao } from '@/types/agenda'
import { useState } from 'react'

function localInput(iso: string) {
  const parts = new Intl.DateTimeFormat('en', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(iso))
  const p = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`
}

export function UpcomingMeetings({ revision, onSelect }: { revision: string; onSelect: (id: string) => void }) {
  const { data, error, loading, refresh } = useApiResource<{ reunioes: Reuniao[] }>('/api/reunioes', revision)
  const proximas = data?.reunioes.filter((r) => r.proxima) ?? []
  return <Panel className="p-4">
    <h2 className="flex items-center gap-2 text-sm font-medium"><CalendarDays size={15} className="text-brand" />Próximas reuniões</h2>
    <p className="mt-1 text-[11px] text-ink-muted">Preparação nas próximas 24 horas</p>
    {error && <div role="alert" className="mt-3 text-xs text-negative">{error}<Button onClick={() => { void refresh() }} className="mt-2">Tentar novamente</Button></div>}
    {proximas.map((r) => <button type="button" key={r.id} onClick={() => onSelect(String(r.cliente_id))} className="mt-3 block w-full rounded-lg border border-line p-3 text-left transition-colors hover:bg-surface-raised focus-visible:outline-2 focus-visible:outline-brand">
      <p className="text-xs font-medium">{r.cliente_nome}</p><p className="mt-1 text-[11px] text-ink-muted">{formatDate(r.inicio_em)}</p>
      <p className="mt-1 text-[10px] text-brand">{r.revisada ? 'Pauta revisada' : r.pauta ? 'Pauta para revisar' : 'Preparar pauta'}</p>
    </button>)}
    {loading && <p role="status" className="mt-3 text-xs text-ink-muted">Consultando agenda…</p>}
    {!loading && !error && !proximas.length && <p className="mt-3 text-xs text-ink-muted">Nenhuma reunião nas próximas 24 horas.</p>}
  </Panel>
}

export function MeetingsSection({ clientId, revision, onUpdated }: { clientId: string; revision: string; onUpdated: () => Promise<void> }) {
  const { data, error, loading, refresh } = useApiResource<{ reunioes: Reuniao[] }>(`/api/clientes/${clientId}/reunioes`, revision)
  const google = useApiResource<{ configurado: boolean; conectado: boolean; email: string | null }>('/api/integracoes/google-agenda', revision)
  const [googleError, setGoogleError] = useState('')
  const [googleBusy, setGoogleBusy] = useState(false)
  const retorno = new URLSearchParams(window.location.search).get('google_agenda')

  async function conectarGoogle() {
    setGoogleError('')
    setGoogleBusy(true)
    try {
      const resposta = await api<{ url: string }>('/api/integracoes/google-agenda/conectar', { method: 'POST' })
      window.location.assign(resposta.url)
    } catch (erro) {
      setGoogleError(erro instanceof Error ? erro.message : 'Não foi possível iniciar a conexão com o Google.')
      setGoogleBusy(false)
    }
  }

  async function desconectarGoogle() {
    setGoogleError('')
    setGoogleBusy(true)
    try {
      const resposta = await api<{ aviso: string | null }>('/api/integracoes/google-agenda/desconectar', { method: 'POST' })
      setGoogleError(resposta.aviso ?? '')
      await google.refresh()
      await refresh()
    } catch (erro) {
      setGoogleError(erro instanceof Error ? erro.message : 'Não foi possível desconectar o Google Agenda.')
    } finally {
      setGoogleBusy(false)
    }
  }

  async function save(path: string, method = 'POST', body?: unknown) {
    await api(path, { method, body })
    await refresh()
    await google.refresh()
    await onUpdated()
  }
  return <Panel className="p-5">
    <h2 className="flex items-center gap-2 text-sm font-medium"><CalendarDays size={16} className="text-brand" />Reuniões e preparação</h2>
    <p className="mt-1 text-[11px] leading-5 text-ink-muted">Keynotes com fontes para você revisar antes do encontro. Suas notas ficam preservadas.</p>
    <div className="mt-4 rounded-lg border border-line p-3">
      <p className="text-xs font-medium">Google Agenda</p>
      {google.loading && <p role="status" className="mt-2 text-[11px] text-ink-muted">Consultando conexão…</p>}
      {google.error && <p role="alert" className="mt-2 text-[11px] text-negative">{google.error}</p>}
      {google.data && <p className="mt-2 text-[11px] text-ink-muted">
        {!google.data.configurado ? 'Integração não configurada neste ambiente.' : google.data.conectado
          ? `Conectado a ${google.data.email}. Eventos vão para o calendário principal.`
          : 'Conta Google não conectada. Os agendamentos permanecem no painel.'}
      </p>}
      {retorno === 'conectado' && <p role="status" className="mt-2 text-[11px] text-brand">Conta Google conectada.</p>}
      {retorno === 'cancelado' && <p role="status" className="mt-2 text-[11px] text-ink-muted">A conexão com o Google foi cancelada.</p>}
      {retorno === 'erro' && <p role="alert" className="mt-2 text-[11px] text-negative">Não foi possível concluir a conexão. Confira a configuração OAuth e tente novamente.</p>}
      {googleError && <p role="alert" className="mt-2 text-[11px] text-negative">{googleError}</p>}
      {google.data?.configurado && <>
        <Button disabled={googleBusy} onClick={() => { void conectarGoogle() }} className="mt-3">
          {googleBusy ? 'Abrindo Google…' : google.data.conectado ? 'Reconectar conta' : 'Conectar Google Agenda'}
        </Button>
        {google.data.conectado && <Button disabled={googleBusy} onClick={() => { void desconectarGoogle() }} className="ml-2 mt-3">Desconectar</Button>}
      </>}
    </div>
    {loading && <p role="status" className="mt-3 text-xs text-ink-muted">Consultando agenda…</p>}
    {error && <div role="alert" className="mt-3 text-xs text-negative">{error}<Button className="ml-2" onClick={() => { void refresh() }}>Tentar novamente</Button></div>}
    <details className="mt-4"><summary className="cursor-pointer text-xs font-medium text-brand">Agendar reunião</summary>
      <MutationForm label="Agendar reunião" reset onSave={(fd) => save(`/api/clientes/${clientId}/reunioes`, 'POST', { objetivo: fd.get('objetivo'), inicio_em: fd.get('inicio_em') })}>
        <label className="block text-xs">Objetivo<input className={`${controlClass} mt-1`} name="objetivo" required maxLength={500} placeholder="Ex.: revisar objetivos e vencimentos" /></label>
        <label className="block text-xs">Data e hora (Brasília)<input className={`${controlClass} mt-1`} name="inicio_em" type="datetime-local" required /></label>
      </MutationForm>
    </details>
    {data?.reunioes.map((r) => <div key={r.id} className="mt-4 rounded-lg border border-line p-4">
      <div className="flex flex-wrap justify-between gap-2"><h3 className="text-xs font-medium">{r.objetivo}</h3><span className="text-[10px] text-brand">{r.estado === 'concluida' ? 'Concluída' : r.estado === 'cancelada' ? 'Cancelada' : r.proxima ? 'Próxima · preparar' : 'Agendada'}</span></div>
      <p className="mt-1 text-[11px] text-ink-muted">{formatDate(r.inicio_em)} · reunião #{r.id}</p>
      <p className={`mt-2 text-[11px] ${r.google_agenda.estado === 'falhou' ? 'text-negative' : 'text-ink-muted'}`}>
        {r.google_agenda.estado === 'sincronizado' ? 'Sincronizada com Google Agenda.'
          : r.google_agenda.estado === 'falhou' ? `Falha na sincronização: ${r.google_agenda.erro}`
            : r.google_agenda.estado === 'nao_configurado' ? 'Google Agenda não configurado.'
              : 'Ainda não sincronizada com Google Agenda.'}
      </p>
      {r.google_agenda.evento_url && <a href={r.google_agenda.evento_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-[11px] text-brand underline">Abrir evento no Google Agenda</a>}
      {google.data?.conectado && r.estado !== 'concluida' && r.google_agenda.estado !== 'sincronizado' &&
        <MutationForm label="Sincronizar agora com Google Agenda" onSave={() => save(`/api/reunioes/${r.id}/sincronizar-google-agenda`)}>{null}</MutationForm>}
      {r.pauta_desatualizada && r.estado === 'agendada' && <p role="status" className="mt-3 text-xs text-brand">Novos dados: atualize e revise a pauta novamente.</p>}
      {r.estado === 'agendada' && <MutationForm label={r.pauta ? 'Atualizar pauta' : 'Preparar pauta'} onSave={() => save(`/api/reunioes/${r.id}/preparar`)}>{null}</MutationForm>}
      {r.pauta && <details className="mt-4" open={r.proxima}><summary className="cursor-pointer text-xs font-medium">Keynotes · {r.revisada ? 'Revisadas pelo assessor' : 'Aguardando revisão'}</summary>
        <p className="mt-2 text-[10px] text-ink-muted">Versão #{r.pauta.id} · preparada em {formatDate(r.pauta.gerada_em)}</p>
        {r.pauta.avisos.map((aviso) => <p key={aviso} className="mt-2 text-[11px] leading-5 text-ink-muted">{aviso}</p>)}
        {r.pauta.secoes.map((s) => <section key={s.titulo} className="mt-4"><h4 className="text-xs font-medium">{s.titulo}</h4>
          {!s.itens.length && <p className="mt-1 text-[11px] text-ink-muted">Nenhum registro disponível.</p>}
          <ul className="mt-2 space-y-2">{s.itens.map((i, index) => <li key={index} className="text-xs leading-5">
            {i.url ? <a href={i.url} target="_blank" rel="noopener noreferrer" className="text-brand underline underline-offset-2">{i.texto}</a> : i.texto}
            {i.fontes.map((f) => <p key={f} className="text-[10px] text-ink-muted">Fonte: {f}</p>)}
          </li>)}</ul></section>)}
        {r.estado === 'agendada' && !r.revisada && <MutationForm label="Confirmar revisão da pauta" onSave={() => save(`/api/reunioes/${r.id}/revisar`, 'POST', { pauta_id: r.pauta?.id })}>{null}</MutationForm>}
      </details>}
      <details className="mt-4"><summary className="cursor-pointer text-xs">Notas do assessor{r.notas ? ' · salvas' : ''}</summary>
        <MutationForm label="Salvar notas" onSave={(fd) => save(`/api/reunioes/${r.id}`, 'PATCH', { notas: fd.get('notas') })}>
          <label className="block text-xs">Observações<textarea name="notas" className={`${controlClass} mt-1`} defaultValue={r.notas} maxLength={4000} rows={3} /></label>
        </MutationForm>
      </details>
      {r.estado === 'agendada' && <>
        <details className="mt-4"><summary className="cursor-pointer text-xs">Reagendar ou alterar objetivo</summary>
          <MutationForm label="Salvar alterações" onSave={(fd) => save(`/api/reunioes/${r.id}`, 'PATCH', { objetivo: fd.get('objetivo'), inicio_em: fd.get('inicio_em') })}>
            <label className="block text-xs">Objetivo<input name="objetivo" className={`${controlClass} mt-1`} required maxLength={500} defaultValue={r.objetivo} /></label>
            <label className="block text-xs">Data e hora (Brasília)<input name="inicio_em" className={`${controlClass} mt-1`} type="datetime-local" required defaultValue={localInput(r.inicio_em)} /></label>
          </MutationForm>
        </details>
        <details className="mt-4"><summary className="cursor-pointer text-xs">Concluir encontro realizado</summary>
          <MutationForm label="Concluir e registrar no histórico" onSave={(fd) => save(`/api/reunioes/${r.id}/concluir`, 'POST', { resumo: fd.get('resumo'), proximos_passos: fd.get('proximos_passos') })}>
            <label className="block text-xs">O que aconteceu<textarea name="resumo" className={`${controlClass} mt-1`} rows={3} required maxLength={4000} /></label>
            <label className="block text-xs">Próximos passos<textarea name="proximos_passos" className={`${controlClass} mt-1`} rows={2} maxLength={1000} /></label>
          </MutationForm>
        </details>
        <details className="mt-4"><summary className="cursor-pointer text-xs text-negative">Cancelar reunião</summary>
          <MutationForm label="Confirmar cancelamento" onSave={() => save(`/api/reunioes/${r.id}/cancelar`)}>{null}</MutationForm>
        </details>
      </>}
      {r.resultado && <div className="mt-4 text-xs leading-5"><p className="font-medium">Resultado registrado · interação #{r.interacao_id}</p><p>{r.resultado.texto}</p>{r.resultado.proximos_passos && <p className="mt-1 text-ink-muted">Próximos passos: {r.resultado.proximos_passos}</p>}</div>}
    </div>)}
    {!loading && !error && !data?.reunioes.length && <p className="mt-4 text-xs text-ink-muted">Nenhuma reunião cadastrada para este cliente.</p>}
  </Panel>
}
