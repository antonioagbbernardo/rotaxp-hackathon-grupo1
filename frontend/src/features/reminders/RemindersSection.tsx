import { BellRing } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { controlClass, MutationForm } from '@/components/ui/MutationForm'
import { useApiResource } from '@/hooks/useApiResource'
import { api } from '@/lib/api'
import type { LembrancasView } from '@/types/agenda'

export function RemindersSection({ clientId, revision, onUpdated }: { clientId: string; revision: string; onUpdated: () => Promise<void> }) {
  const { data, error, loading, refresh } = useApiResource<LembrancasView>(`/api/clientes/${clientId}/lembrancas`, revision)
  const candidatos = data?.candidatos ?? []
  async function save(path: string, body: unknown) {
    await api(path, { method: 'POST', body })
    await refresh(); await onUpdated()
  }
  return <Panel className="p-5">
    <h2 className="flex items-center gap-2 text-sm font-medium"><BellRing size={16} className="text-brand" />Lembranças com contexto</h2>
    <p className="mt-1 text-[11px] leading-5 text-ink-muted">Confirme a data e a pessoa nas fontes. A lembrança ajuda a preparar o contato; você decide se é pertinente.</p>
    {loading && <p role="status" className="mt-3 text-xs text-ink-muted">Consultando lembranças…</p>}
    {error && <div role="alert" className="mt-3 text-xs text-negative">{error}<Button className="ml-2" onClick={() => { void refresh() }}>Tentar novamente</Button></div>}
    {!!candidatos.length && <details className="mt-4"><summary className="cursor-pointer text-xs font-medium text-brand">Confirmar uma lembrança das fontes</summary>
      <MutationForm label="Confirmar data e salvar lembrança" onSave={(fd) => {
        const i = candidatos.find((candidate) => candidate.id === Number(fd.get('item_id')))
        if (!i) throw new Error('Escolha uma informação revisada.')
        return save(`/api/clientes/${clientId}/lembrancas`, { item_id: i.id, revisao: i.revisao, descricao: fd.get('descricao'), tipo: fd.get('tipo'), data: fd.get('data') })
      }}>
        <label className="block text-xs">Informação revisada<select name="item_id" className={`${controlClass} mt-1`} required>{candidatos.map((i) => <option key={i.id} value={i.id}>{i.sujeito === 'familiar' ? 'Familiar' : 'Cliente'} · {i.valor}</option>)}</select></label>
        <label className="block text-xs">Tipo<select name="tipo" className={`${controlClass} mt-1`}><option value="aniversario">Aniversário (recorrente)</option><option value="compromisso">Compromisso (data específica)</option></select></label>
        <label className="block text-xs">Descrição<input name="descricao" className={`${controlClass} mt-1`} required maxLength={500} placeholder="Ex.: aniversário de um familiar" /></label>
        <label className="block text-xs">Data confirmada<input name="data" className={`${controlClass} mt-1`} type="date" required /></label>
      </MutationForm>
      <details className="mt-3"><summary className="cursor-pointer text-[11px]">Conferir fontes dos candidatos</summary>{candidatos.map((i) => <div key={i.id} className="mt-3 text-xs"><p>{i.valor}</p>{i.fontes.map((f) => <p key={f} className="mt-1 text-[10px] text-ink-muted">{f}</p>)}</div>)}</details>
    </details>}
    {data?.lembrancas.map((r) => <div key={r.id} className="mt-4 rounded-lg border border-line p-3">
      <p className="text-xs font-medium">{r.descricao}</p><p className="mt-1 text-[11px] text-ink-muted">{r.ocorrencia.split('-').reverse().join('/')} · {r.sujeito === 'familiar' ? 'Familiar' : 'Cliente'} · {r.estado}</p>
      {r.proxima && <p className="mt-2 text-[11px] text-brand">{r.pode_contatar ? 'Próxima ou pendente · avaliar relevância antes de abordar' : 'Próxima ou pendente · aguardar intervalo de contato pessoal'}</p>}
      {r.adiado_ate && <p className="mt-2 text-[11px] text-ink-muted">Adiada até {r.adiado_ate.split('-').reverse().join('/')}</p>}
      {r.fontes.map((f) => <p key={f} className="mt-2 text-[10px] text-ink-muted">Fonte: {f}</p>)}
      <details className="mt-3"><summary className="cursor-pointer text-xs">Registrar feedback</summary>
        <MutationForm label="Salvar decisão" onSave={(fd) => {
          const body: Record<string, unknown> = { acao: fd.get('acao'), motivo: fd.get('motivo') }
          if (body.acao === 'adiar') body.adiado_ate = fd.get('adiado_ate')
          return save(`/api/clientes/${clientId}/lembrancas/${r.id}/feedback`, body)
        }}>
          <label className="block text-xs">Decisão<select name="acao" className={`${controlClass} mt-1`}><option value="concluir">Concluir acompanhamento</option><option value="descartar">Não é pertinente nesta ocorrência</option><option value="adiar">Adiar</option></select></label>
          <label className="block text-xs">Motivo<textarea name="motivo" className={`${controlClass} mt-1`} required rows={2} maxLength={1000} /></label>
          <label className="block text-xs">Nova data (somente ao adiar)<input type="date" name="adiado_ate" className={`${controlClass} mt-1`} /></label>
        </MutationForm>
      </details>
    </div>)}
    {!loading && !error && !data?.lembrancas.length && <p className="mt-4 text-xs text-ink-muted">Nenhuma lembrança confirmada elegível. Revise uma data ou compromisso nas fontes e confira as preferências pessoais.</p>}
  </Panel>
}
