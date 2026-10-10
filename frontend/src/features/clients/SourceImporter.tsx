import { useState } from 'react'
import { Panel } from '@/components/ui/Panel'
import { controlClass, MutationForm } from '@/components/ui/MutationForm'
import { api } from '@/lib/api'

export function SourceImporter({ onUpdated }: { onUpdated: () => Promise<void> }) {
  const [result, setResult] = useState('')
  return <Panel className="p-4">
    <details>
      <summary className="cursor-pointer text-xs font-medium">Importar fontes fictícias</summary>
      <p className="mt-2 text-[11px] text-ink-muted">Formulário e conversas já existentes, por arquivo JSON. Identidade ausente fica pendente.</p>
      <MutationForm label="Importar JSON" onSave={async (fd) => {
        const file = fd.get('arquivo')
        if (!(file instanceof File) || !file.size) throw new Error('Selecione um JSON fictício.')
        let body: unknown
        try { body = JSON.parse(await file.text()) } catch { throw new Error('O arquivo não contém JSON válido.') }
        const r = await api<{ importados: number; reutilizados: number; pendentes: number }>('/api/fontes/importar', { method: 'POST', body })
        setResult(`${r.importados} importados · ${r.reutilizados} reutilizados · ${r.pendentes} identidades pendentes no lote`)
        await onUpdated()
      }}>
        <label className="block text-xs">Arquivo JSON fictício<input className={`${controlClass} mt-1`} name="arquivo" type="file" accept=".json,application/json" required /></label>
      </MutationForm>
      <p className="mt-2 text-xs text-ink-muted" role="status">{result}</p>
    </details>
  </Panel>
}
