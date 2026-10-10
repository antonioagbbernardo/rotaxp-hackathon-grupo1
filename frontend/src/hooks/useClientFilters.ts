import { useMemo, useState } from 'react'
import type { Client } from '@/types/client'

export type ClientFilter = 'all' | 'positive' | 'neutral' | 'negative'

function normalize(text: string) {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
}

function matchesQuery(client: Client, query: string) {
  if (!query) return true
  const haystack = normalize([client.name, ...client.interests].join(' '))
  return haystack.includes(query)
}

export function useClientFilters(clients: Client[]) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<ClientFilter>('all')

  const counts = useMemo(() => {
    return {
      all: clients.length,
      positive: clients.filter((client) => client.sentiment === 'positive').length,
      neutral: clients.filter((client) => client.sentiment === 'neutral').length,
      negative: clients.filter((client) => client.sentiment === 'negative').length,
    }
  }, [clients])

  const visibleClients = useMemo(() => {
    const normalizedQuery = normalize(query.trim())
    return clients.filter(
      (client) =>
        (filter === 'all' || client.sentiment === filter) &&
        matchesQuery(client, normalizedQuery),
    )
  }, [clients, filter, query])

  return {
    query,
    setQuery,
    filter,
    setFilter,
    visibleClients,
    counts,
  }
}
