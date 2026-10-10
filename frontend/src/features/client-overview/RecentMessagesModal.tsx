import { useEffect } from 'react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/lib/format'
import type { Client } from '@/types/client'
import {
  MessageSquare,
  X,
  Mail,
  Phone,
  MessageCircle,
  Users,
  Mic,
} from 'lucide-react'

interface RecentMessagesModalProps {
  client: Client
  isOpen: boolean
  onClose: () => void
}

interface MensagemItem {
  id: string
  canal: string
  origem: string
  texto: string
  data: string
  proximosPassos?: string | null
  isAudioTranscrito: boolean
}

function getChannelIcon(canal: string, isAudioTranscrito: boolean) {
  if (isAudioTranscrito) {
    return <Mic className="size-3.5 text-brand" />
  }
  switch (canal.toLowerCase()) {
    case 'whatsapp':
      return <MessageCircle className="size-3.5 text-positive" />
    case 'email':
      return <Mail className="size-3.5 text-sky-400" />
    case 'telefone':
      return <Phone className="size-3.5 text-brand" />
    case 'presencial':
      return <Users className="size-3.5 text-ink-muted" />
    default:
      return <MessageSquare className="size-3.5 text-ink-muted" />
  }
}

export function RecentMessagesModal({ client, isOpen, onClose }: RecentMessagesModalProps) {
  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const deInteracoes: MensagemItem[] = (client.interactions ?? []).map((i) => {
    const isAudio = i.canal.toLowerCase() === 'telefone' || i.texto.includes('[Transcrição')
    return {
      id: `interacao-${i.id}`,
      canal: i.canal,
      origem: isAudio ? 'Transcrição de chamada (XP Voice)' : 'Registro do assessor',
      texto: i.texto,
      data: i.ocorrida_em,
      proximosPassos: i.proximos_passos,
      isAudioTranscrito: isAudio,
    }
  })

  const deFontes: MensagemItem[] = (client.sourceDocuments ?? [])
    .filter((f) => f.tipo === 'interacao')
    .map((f) => {
      const conteudoTexto =
        typeof f.conteudo === 'string' ? f.conteudo : JSON.stringify(f.conteudo, null, 2)
      const isAudio =
        (f.canal || '').toLowerCase() === 'telefone' || conteudoTexto.includes('[Transcrição')
      return {
        id: `fonte-${f.id}`,
        canal: f.canal || 'whatsapp',
        origem: isAudio ? 'XP Voice · Transcrição STT' : f.origem || 'Documento ingerido',
        texto: conteudoTexto,
        data: f.ocorrida_em,
        isAudioTranscrito: isAudio,
      }
    })

  const todasMensagens = [...deInteracoes, ...deFontes].sort(
    (a, b) => new Date(b.data).getTime() - new Date(a.data).getTime(),
  )

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="messages-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="flex max-h-[85vh] w-full max-w-xl flex-col rounded-2xl border border-line bg-surface-raised shadow-2xl">
        {/* Cabeçalho */}
        <header className="flex items-center justify-between border-b border-line px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <MessageSquare className="size-4.5" />
            </div>
            <div>
              <h2 id="messages-modal-title" className="text-base font-semibold text-ink">
                Mensagens recentes
              </h2>
              <p className="text-[11px] text-ink-muted">
                {client.name} · {todasMensagens.length}{' '}
                {todasMensagens.length === 1 ? 'registro no banco' : 'registros no banco'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar modal"
            className="rounded-lg p-1.5 text-ink-muted transition-colors hover:bg-surface hover:text-ink"
          >
            <X className="size-5" />
          </button>
        </header>

        {/* Lista de mensagens */}
        <div className="flex-1 space-y-3.5 overflow-y-auto p-6">
          {todasMensagens.length === 0 ? (
            <div className="py-12 text-center">
              <MessageSquare className="mx-auto size-10 text-ink-muted opacity-40" />
              <p className="mt-3 text-sm text-ink-muted">
                Nenhuma mensagem ou interação registrada no banco para este cliente.
              </p>
              <p className="mt-1 text-xs text-ink-subtle">
                Interações de WhatsApp, e-mail e atas cadastradas aparecerão aqui.
              </p>
            </div>
          ) : (
            todasMensagens.map((msg) => (
              <article
                key={msg.id}
                className={`rounded-xl border p-4 transition-colors ${
                  msg.isAudioTranscrito
                    ? 'border-brand/25 bg-surface/95 shadow-sm'
                    : 'border-line bg-surface/80 hover:border-line-strong'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {getChannelIcon(msg.canal, msg.isAudioTranscrito)}
                    <Badge className="text-[10px] capitalize">
                      {msg.canal}
                    </Badge>
                    {msg.isAudioTranscrito && (
                      <span className="inline-flex items-center gap-1 rounded bg-brand/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand">
                        XP Voice (STT)
                      </span>
                    )}
                    <span className="text-[10px] text-ink-muted">· {msg.origem}</span>
                  </div>
                  <time className="text-[11px] text-ink-muted" dateTime={msg.data}>
                    {formatDate(msg.data)}
                  </time>
                </div>

                <div
                  className={`mt-3 whitespace-pre-wrap rounded-lg p-3 text-xs leading-relaxed ${
                    msg.isAudioTranscrito
                      ? 'border border-line/60 bg-surface text-ink'
                      : 'text-ink'
                  }`}
                >
                  {msg.texto}
                </div>

                {msg.proximosPassos && (
                  <div className="mt-3 rounded-lg border border-brand/20 bg-brand/5 p-2.5">
                    <p className="text-[10px] font-medium tracking-wide text-brand uppercase">
                      Próximos passos
                    </p>
                    <p className="mt-0.5 text-xs text-ink-muted">
                      {msg.proximosPassos}
                    </p>
                  </div>
                )}
              </article>
            ))
          )}
        </div>

        {/* Rodapé */}
        <footer className="flex items-center justify-end border-t border-line px-6 py-3.5">
          <Button onClick={onClose} variant="secondary">
            Fechar
          </Button>
        </footer>
      </div>
    </div>
  )
}
