import { useState } from 'react'
import { Badge } from '@/components/ui/Badge'
import { Panel } from '@/components/ui/Panel'
import { SparkleIcon } from '@/components/ui/icons'
import { getInitials } from '@/lib/format'
import type { Client } from '@/types/client'
import { AskAssistantForm } from './AskAssistantForm'
import { InsightCard } from './InsightCard'
import { OpeningSuggestion } from './OpeningSuggestion'
import { UserMessage } from './UserMessage'

interface AssistantPanelProps {
  client: Client
}

export function AssistantPanel({ client }: AssistantPanelProps) {
  const [followUps, setFollowUps] = useState<string[]>([])
  const { assistant } = client
  const firstName = client.name.split(' ')[0]

  const handleAsk = (question: string) => setFollowUps((current) => [...current, question])

  return (
    <Panel className="flex min-h-0 flex-1 flex-col px-5 pt-5 pb-3" aria-labelledby="assistant-title">
      <header className="flex items-start gap-4 border-b border-line px-2 pb-3.5">
        <SparkleIcon className="mt-1 size-5 text-brand" />
        <div>
          <h2 id="assistant-title" className="text-base font-semibold">
            Assistente do assessor
          </h2>
          <p className="mt-1 text-[11px] text-ink-muted">IA com o contexto de {firstName}</p>
        </div>
      </header>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge className="w-38 text-[11px]">
          {getInitials(client.name)} {client.name}
        </Badge>
        <Badge tone="positive" withDot className="w-38 text-[11px]">
          Contexto atualizado
        </Badge>
      </div>

      <div className="-mx-1 mt-3.5 min-h-0 flex-1 space-y-3.5 overflow-y-auto px-1 pb-1">
        <UserMessage>{assistant.question}</UserMessage>

        <div>
          <p className="flex items-center gap-1 text-xs font-semibold">
            <span aria-hidden>✦</span> XP Pulse
          </p>
          <p className="mt-2 text-[13px] leading-relaxed">{assistant.summary}</p>
        </div>

        <ol className="space-y-3">
          {assistant.insights.map((insight, index) => (
            <li key={insight.title}>
              <InsightCard insight={insight} position={index + 1} />
            </li>
          ))}
        </ol>

        <OpeningSuggestion openings={assistant.openings} sources={client.news} />

        {followUps.map((question, index) => (
          <div key={index} className="space-y-2">
            <UserMessage>{question}</UserMessage>
            <p className="text-[11px] text-ink-subtle">
              Respostas novas não estão disponíveis nos dados de demonstração.
            </p>
          </div>
        ))}
      </div>

      <div className="mt-3">
        <AskAssistantForm placeholder={`Pergunte sobre ${firstName}...`} onAsk={handleAsk} />
        <p className="mt-2 text-[9px] text-ink-muted">
          Sugestões para revisão do assessor · Dados fictícios
        </p>
      </div>
    </Panel>
  )
}
