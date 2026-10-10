export type Sentiment = 'positive' | 'negative' | 'neutral' | 'unknown'

export type Pronoun = 'ela' | 'ele' | 'este cliente'

export type ClientStatus = 'opportunity' | 'attention' | 'stable'

export type AssetClass = 'fixedIncome' | 'funds' | 'stocks'

export interface ProfileTag {
  label: string
  highlighted?: boolean
}

export interface PerceptionEntry {
  id?: number
  label?: string
  reason?: string
  date?: string
  /** ISO month, e.g. "2025-05" */
  month: string
  sentiment: Sentiment
}

export interface AllocationSlice {
  asset: AssetClass
  percent: number
}

export interface Portfolio {
  total: string | number | null
  goal: string
  allocation: AllocationSlice[]
}

export interface NewsItem {
  id: string
  sentiment: Sentiment
  title: string
  whyItMatters: string
  relevance: string
  scenario: string
  updatedMinutesAgo: number
  url?: string
  source?: string
  publishedAt?: string
  collectedAt?: string
  topic?: string
  description?: string
}

export interface NewsState {
  configurado: boolean
  catalogo: { id: string; nome: string }[]
  interesses: { id: number; revisao: number; valor: string; fontes: string[] }[]
  vinculos: { id: number | string; item_id: number | null; revisao: number; assunto: string; interesse: string; fontes: string[]; automatico?: boolean; geral?: boolean }[]
  assuntos: { id: string; nome: string; estado: 'nunca' | 'atualizado' | 'desatualizado' | 'falhou' | 'processando'; ultima_coleta: string | null; ultima_tentativa: string | null; erro: { codigo: string; mensagem: string } | null }[]
  limite_diario: number | null
  chamadas_hoje: number
}

export interface Insight {
  kind: 'opportunity' | 'concern'
  title: string
  body: string
}

export interface OpeningMessage {
  tone: string
  text: string
}

export interface AssistantBrief {
  question: string
  summary: string
  insights: Insight[]
  openings: OpeningMessage[]
  sources?: string[]
  summarySources?: string[]
  summaryItems?: string[]
  aiSummary?: { configurado: boolean; modelo: string; assinatura: string; resumo: ResumoIA | null }
}

export interface TrechoResumoIA {
  texto: string
  fontes: string[]
}

export interface ResumoIA {
  visao_geral: TrechoResumoIA
  pontos_atencao: TrechoResumoIA[]
  antes_contato: TrechoResumoIA[]
  modelo: string
  gerado_em: string
  assinatura: string
  uso: { input_tokens?: number; output_tokens?: number; total_tokens?: number }
}

export interface Client {
  mood?: { sentiment: Sentiment; motivo: string; estado: string; assinatura: string; configurado: boolean; revisado_em: string | null; gerado_em?: string; evidencias: { fonte: string; trecho: string }[] }
  id: string
  name: string
  pronoun: Pronoun
  status: ClientStatus
  interests: string[]
  tags: ProfileTag[]
  sentiment: Sentiment
  headline: string
  updatedMinutesAgo: number | null
  clientSince: string | null
  lastContactDays: number | null
  whatsapp: string
  email: string
  perception: PerceptionEntry[]
  portfolio: Portfolio
  news: NewsItem[]
  newsState?: NewsState
  assistant: AssistantBrief
  priority?: 'alta' | 'media' | 'baixa'
  relationshipLabel?: string
  context?: ContextView
  sourceDocuments?: SourceDocument[]
  alerts?: Alert[]
  interactions?: Interaction[]
  preferences?: Preferences
  positions?: Position[]
}

export interface Evidence {
  documento_id: number
  campo: string | null
  trecho: string
  origem: string
  registro_id: string
  versao: number
}
export interface ContextItem {
  id: number
  categoria: string
  assunto: string
  sujeito: string
  tipo: string
  valor_original: string
  valor_revisado: string | null
  estado: 'pendente' | 'confirmado' | 'corrigido' | 'descartado' | 'adiado'
  revisao: number
  adiado_ate: string | null
  evidencia_atual: boolean
  conflitos: number[]
  bloqueado: boolean
  evidencias: Evidence[]
  historico_revisoes: { id: number; acao: string; motivo: string; revisada_em: string }[]
}
export interface ContextView {
  itens: ContextItem[]
  modelo: string
  configurado: boolean
  fontes_novas: number
}
export interface SourceDocument {
  id: number
  origem: string
  registro_id: string
  versao: number
  atual: boolean
  tipo: string
  canal: string | null
  ocorrida_em: string
  conteudo: string | Record<string, string>
}
export interface Alert {
  chave_ocorrencia: string
  rotulo: string
  motivo: string
  prioridade: 'alta' | 'media' | 'baixa'
  estado: string
  fonte: { tipo_fonte: string; id_fonte: number | number[]; data_referencia?: string }
}
export interface Interaction {
  id: number
  canal: string
  texto: string
  ocorrida_em: string
  proximos_passos: string | null
}
export interface Preferences {
  canal_preferido: string | null
  intervalo_minimo_dias: number
  permite_assuntos_pessoais: boolean
}
export interface Position {
  id: number
  ativo: string
  valor: string
  vencimento: string
  fonte: string
}
export interface PulseView {
  advisor: { name: string; role: string }
  generatedAt: string
  clients: Client[]
}
