import type { Client } from '@/types/client'
import { NewsCard } from './NewsCard'

interface NewsSectionProps {
  client: Client
}

export function NewsSection({ client }: NewsSectionProps) {
  const firstName = client.name.split(' ')[0]

  return (
    <section aria-labelledby="news-title">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="news-title" className="text-lg font-semibold">
            Notícias que importam para {firstName}
          </h2>
          <p className="mt-1 text-[11px] text-ink-muted">
            Impacto personalizado com base nos interesses e na carteira.
          </p>
        </div>
      </div>

      <ul className="mt-4 space-y-4">
        {client.news.length === 0 && <li className="rounded-xl border border-line p-4 text-xs text-ink-muted">Nenhuma notícia coletada para este cliente. A integração de notícias será a próxima etapa.</li>}
        {client.news.map((news) => (
          <li key={news.id}>
            <NewsCard news={news} pronoun={client.pronoun} />
          </li>
        ))}
      </ul>
    </section>
  )
}
