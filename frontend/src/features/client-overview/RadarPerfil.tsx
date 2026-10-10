import { Panel } from '@/components/ui/Panel'
import { calcularPerfilRadar, type EixoRadar } from '@/lib/perfil-radar'
import type { Client } from '@/types/client'

const TAMANHO = 240
const CENTRO = TAMANHO / 2
const RAIO = 78
const ANEIS = [25, 50, 75, 100]

function ponto(indice: number, total: number, valor: number, raio = RAIO) {
  const angulo = -Math.PI / 2 + (2 * Math.PI * indice) / total
  const r = (raio * valor) / 100
  return { x: CENTRO + r * Math.cos(angulo), y: CENTRO + r * Math.sin(angulo) }
}

function poligono(eixos: EixoRadar[], escala: (e: EixoRadar) => number) {
  return eixos
    .map((e, i) => {
      const p = ponto(i, eixos.length, escala(e))
      return `${p.x.toFixed(1)},${p.y.toFixed(1)}`
    })
    .join(' ')
}

interface RadarPerfilProps {
  client: Client
  /** data de referência: `generatedAt` do backend (relógio único) */
  hoje: string
}

export function RadarPerfil({ client, hoje }: RadarPerfilProps) {
  const posicoes = (client.positions ?? []).map((p) => ({
    id: p.id,
    ativo: p.ativo,
    valor: p.valor,
    vencimento: p.vencimento,
  }))
  const perfil = calcularPerfilRadar(posicoes, hoje.slice(0, 10), client.tags[0]?.label)
  const resumo = perfil.eixos.map((e) => `${e.rotulo} ${e.valor ?? 'sem dado'}`).join(', ')

  return (
    <Panel className="px-5 py-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-sm font-medium">Radar de perfil</h2>
        <p className="text-[10px] text-ink-muted">Estimativa heurística · dados fictícios · não é recomendação</p>
      </div>

      {perfil.eixos.length === 0 ? (
        <p className="mt-4 text-xs text-ink-muted">
          Sem posições cadastradas: não há dados para estimar o perfil.
        </p>
      ) : (
        <div className="mt-3 grid items-center gap-4 sm:grid-cols-[minmax(0,300px)_1fr]">
          <svg
            viewBox={`-40 0 ${TAMANHO + 80} ${TAMANHO}`}
            className="mx-auto w-full max-w-80"
            role="img"
            aria-label={`Radar de perfil: ${resumo}`}
          >
            {ANEIS.map((anel) => (
              <polygon
                key={anel}
                points={poligono(perfil.eixos, () => anel)}
                className="fill-none stroke-line"
                strokeWidth={1}
              />
            ))}
            {perfil.eixos.map((e, i) => {
              const fim = ponto(i, perfil.eixos.length, 100)
              return (
                <line key={e.chave} x1={CENTRO} y1={CENTRO} x2={fim.x} y2={fim.y} className="stroke-line" strokeWidth={1} />
              )
            })}
            <polygon
              points={poligono(perfil.eixos, (e) => e.valor ?? 0)}
              className="fill-brand/20 stroke-brand"
              strokeWidth={2}
              strokeLinejoin="round"
            />
            {perfil.eixos.map((e, i) => {
              const p = ponto(i, perfil.eixos.length, e.valor ?? 0)
              const r = ponto(i, perfil.eixos.length, 100, RAIO + 16)
              return (
                <g key={e.chave}>
                  {e.valor !== null && (
                    <circle cx={p.x} cy={p.y} r={4} className="fill-brand stroke-surface" strokeWidth={2}>
                      <title>{`${e.rotulo}: ${e.valor}`}</title>
                    </circle>
                  )}
                  <text
                    x={r.x}
                    y={r.y}
                    textAnchor={r.x < CENTRO - 4 ? 'end' : r.x > CENTRO + 4 ? 'start' : 'middle'}
                    dominantBaseline="middle"
                    className="fill-ink-muted text-[9px]"
                  >
                    {e.rotulo}
                  </text>
                </g>
              )
            })}
          </svg>

          <div className="min-w-0">
            <p className="text-xs">
              Sugerido pela carteira:{' '}
              <strong className="font-semibold">{perfil.sugerido ?? 'sem dado suficiente'}</strong>
            </p>
            <p className="mt-1 text-xs text-ink-muted">
              Declarado: {perfil.declarado ?? client.tags[0]?.label ?? 'não informado'}
              {perfil.diverge && <span className="text-brand"> · divergente da carteira</span>}
            </p>

            <ul className="mt-3 space-y-1.5">
              {perfil.eixos.map((e) => (
                <li key={e.chave} className="text-[11px]" title={e.explicacao}>
                  <div className="flex justify-between gap-3">
                    <span>{e.rotulo}</span>
                    <span className="font-medium tabular-nums">{e.valor ?? 'sem dado'}</span>
                  </div>
                  <p className="text-[10px] text-ink-muted">Fonte: {e.fontes.join(', ') || 'nenhuma'}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {perfil.avisos.map((aviso) => (
        <p key={aviso} className="mt-2 text-[10px] text-ink-muted">{aviso}</p>
      ))}
      <p className="mt-3 text-[10px] text-ink-subtle">
        Calculado só das posições (tipo, valor e prazo); humor e percepção não entram.
      </p>
    </Panel>
  )
}
