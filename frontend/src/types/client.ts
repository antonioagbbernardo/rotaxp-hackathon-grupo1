export type Sentiment = 'positive' | 'negative' | 'neutral'

export type Pronoun = 'ela' | 'ele'

export type ClientStatus = 'opportunity' | 'attention' | 'stable'

export type AssetClass = 'fixedIncome' | 'funds' | 'stocks'

export interface ProfileTag {
  label: string
  highlighted?: boolean
}

export interface PerceptionEntry {
  /** ISO month, e.g. "2025-05" */
  month: string
  sentiment: Sentiment
}

export interface AllocationSlice {
  asset: AssetClass
  percent: number
}

export interface Portfolio {
  total: number
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
}

export interface Client {
  id: string
  name: string
  pronoun: Pronoun
  status: ClientStatus
  interests: string[]
  tags: ProfileTag[]
  sentiment: Sentiment
  headline: string
  updatedMinutesAgo: number
  clientSince: string
  lastContactDays: number
  whatsapp: string
  email: string
  perception: PerceptionEntry[]
  portfolio: Portfolio
  news: NewsItem[]
  assistant: AssistantBrief
}
