import { Panel } from '@/components/ui/Panel'
import { controlClass, MutationForm } from '@/components/ui/MutationForm'
import { api } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/format'
import type { Client } from '@/types/client'

export function ClientWorkspace({ client, onUpdated }: { client: Client; onUpdated: () => Promise<void> }) {
  const pref = client.preferences
  return <div id={`registros-${client.id}`} className="min-w-0 space-y-4">
    <Panel className="p-5">
      <details><summary className="cursor-pointer text-sm font-medium leading-6">Posições e fontes</summary>
        {client.positions?.length ? client.positions.map((p) => <p key={p.id} className="mt-2 text-[11px]">{p.ativo} · {formatCurrency(p.valor)} · vence {p.vencimento}<br /><span className="text-ink-muted">Fonte: posição #{p.id} · {p.fonte}</span></p>) : <p className="mt-2 text-xs text-ink-muted">Nenhuma posição cadastrada.</p>}
      </details>
    </Panel>
    <Panel className="p-5"><details><summary className="cursor-pointer text-sm font-medium">Formulário e conversas originais ({client.sourceDocuments?.length ?? 0})</summary>
      {client.sourceDocuments?.map((f) => <details key={f.id} className="mt-3 rounded-lg border border-line p-3">
        <summary className="cursor-pointer text-xs">{f.tipo === 'formulario' ? 'Formulário' : f.tipo === 'nota_assessor' ? 'Informação registrada pelo chat' : f.canal} · {f.registro_id} v{f.versao} · {f.atual ? 'atual' : 'anterior'}</summary>
        <p className="mt-2 text-[10px] text-ink-muted">{f.origem} · {formatDate(f.ocorrida_em)}</p>
        {typeof f.conteudo === 'string' ? <p className="mt-2 whitespace-pre-wrap text-xs">{f.conteudo}</p> : <dl className="mt-2 text-xs">{Object.entries(f.conteudo).map(([k, v]) => <div key={k} className="mt-2"><dt className="text-ink-muted">{k}</dt><dd className="whitespace-pre-wrap">{v}</dd></div>)}</dl>}
      </details>)}
      {!client.sourceDocuments?.length && <p className="mt-3 text-xs text-ink-muted">Nenhuma fonte importada.</p>}
    </details></Panel>
    <Panel className="p-5"><details><summary className="cursor-pointer text-sm font-medium">Contatos, relacionamento e preferências</summary>
      <details className="mt-4"><summary className="cursor-pointer text-xs">Registrar interação</summary>
        <MutationForm label="Registrar contato" reset onSave={async (fd) => {
          const body: Record<string, unknown> = { canal: fd.get('canal'), texto: fd.get('texto'), proximos_passos: fd.get('proximos_passos') }
          if (fd.get('ocorrida_em')) body.ocorrida_em = fd.get('ocorrida_em')
          await api(`/api/clientes/${client.id}/interacoes`, { method: 'POST', body }); await onUpdated()
        }}>
          <label className="block text-xs">Canal<select name="canal" defaultValue={pref?.canal_preferido || 'telefone'} className={`${controlClass} mt-1`}><option value="telefone">Telefone</option><option value="whatsapp">WhatsApp</option><option value="email">E-mail</option><option value="presencial">Presencial</option></select></label>
          <label className="block text-xs">O que aconteceu<textarea name="texto" required rows={3} className={`${controlClass} mt-1`} /></label>
          <label className="block text-xs">Ocorrência (opcional)<input name="ocorrida_em" type="datetime-local" className={`${controlClass} mt-1`} /></label>
          <label className="block text-xs">Próximos passos<input name="proximos_passos" className={`${controlClass} mt-1`} /></label>
        </MutationForm>
      </details>
      <details className="mt-4"><summary className="cursor-pointer text-xs">Histórico de interações ({client.interactions?.length ?? 0})</summary>
        {client.interactions?.map((i) => <div key={i.id} className="mt-3 border-t border-line pt-2 text-xs"><p className="text-ink-muted">{i.canal} · {formatDate(i.ocorrida_em)} · interação #{i.id}</p><p className="mt-1 whitespace-pre-wrap">{i.texto}</p>{i.proximos_passos && <p className="mt-1 text-ink-muted">Próximos passos: {i.proximos_passos}</p>}</div>)}
      </details>
      <details className="mt-4"><summary className="cursor-pointer text-xs">Avaliar relacionamento</summary>
        <MutationForm label="Salvar avaliação" onSave={async (fd) => { await api(`/api/clientes/${client.id}/relacionamento`, { method: 'POST', body: { estado: fd.get('estado'), justificativa: fd.get('justificativa') } }); await onUpdated() }}>
          <label className="block text-xs">Relacionamento<select name="estado" className={`${controlClass} mt-1`}><option value="atencao">Atenção</option><option value="positivo">Positivo</option><option value="negativo">Negativo</option></select></label>
          <label className="block text-xs">Justificativa<textarea name="justificativa" required rows={2} className={`${controlClass} mt-1`} /></label>
        </MutationForm>
      </details>
      {pref && <details className="mt-4"><summary className="cursor-pointer text-xs">Preferências de contato</summary>
        <MutationForm label="Salvar preferências" onSave={async (fd) => {
          await api(`/api/clientes/${client.id}/preferencias`, { method: 'PATCH', body: { canal_preferido: fd.get('canal') || null, intervalo_minimo_dias: Number(fd.get('intervalo')), permite_assuntos_pessoais: fd.get('pessoal') === 'on' } }); await onUpdated()
        }}>
          <label className="block text-xs">Canal preferido<select name="canal" defaultValue={pref.canal_preferido || ''} className={`${controlClass} mt-1`}><option value="">Sem preferência</option><option value="telefone">Telefone</option><option value="whatsapp">WhatsApp</option><option value="email">E-mail</option><option value="presencial">Presencial</option></select></label>
          <label className="block text-xs">Intervalo mínimo<select name="intervalo" defaultValue={pref.intervalo_minimo_dias} className={`${controlClass} mt-1`}>{[7, 14, 30].map((d) => <option key={d} value={d}>{d} dias</option>)}</select></label>
          <label className="flex items-center gap-2 text-xs"><input type="checkbox" name="pessoal" defaultChecked={pref.permite_assuntos_pessoais} />Permite assuntos pessoais</label>
        </MutationForm>
      </details>}
    </details></Panel>
  </div>
}
