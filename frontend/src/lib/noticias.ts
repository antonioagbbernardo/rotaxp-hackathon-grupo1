import { api } from './api'

export async function atualizarNoticias(clientId: string): Promise<string> {
  try {
    const result = await api<{ resultados: { estado: string; erro?: { mensagem: string } }[] }>(
      `/api/clientes/${clientId}/noticias/atualizar`, { method: 'POST', signal: AbortSignal.timeout(60_000) })
    const failures = result.resultados.filter((r) => r.estado === 'erro')
    return failures.length ? `Contexto salvo. ${failures.map((r) => r.erro?.mensagem ?? 'Coleta não concluída.').join(' ')}` : ''
  } catch (e) {
    return `Contexto salvo. Não foi possível atualizar as notícias: ${e instanceof Error ? e.message : 'tente buscar novamente.'}`
  }
}
