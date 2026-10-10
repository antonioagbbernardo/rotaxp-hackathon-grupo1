export interface Pauta {
  id: number
  gerada_em: string
  avisos: string[]
  secoes: { titulo: string; itens: { texto: string; fontes: string[]; url?: string }[] }[]
}
export interface Reuniao {
  id: number
  cliente_id: number
  cliente_nome: string
  objetivo: string
  inicio_em: string
  estado: 'agendada' | 'cancelada' | 'concluida'
  notas: string
  google_agenda: { estado: 'nao_configurado' | 'nao_conectado' | 'sincronizado' | 'falhou'; erro: string | null; evento_url: string | null }
  proxima: boolean
  pauta: Pauta | null
  pauta_desatualizada: boolean
  revisada: boolean
  interacao_id: number | null
  resultado: { texto: string; proximos_passos: string; ocorrida_em: string } | null
}
export interface LembrancasView {
  candidatos: { id: number; revisao: number; valor: string; sujeito: string; fontes: string[] }[]
  lembrancas: { id: number; descricao: string; tipo: string; sujeito: string; ocorrencia: string;
    estado: string; adiado_ate: string | null; proxima: boolean; pode_contatar: boolean; fontes: string[] }[]
}
