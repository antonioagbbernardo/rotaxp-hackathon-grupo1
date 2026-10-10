/**
 * Radar de perfil do investidor — heurística de demonstração (incremento 09).
 * Estimativa sobre posições fictícias; não é suitability nem recomendação.
 * Os pesos abaixo são o ponto de troca por um modelo de ML.
 */

export type PerfilSugerido = 'Conservador' | 'Moderado' | 'Arrojado'
export type ChaveEixo = 'risco' | 'credito' | 'liquidez' | 'horizonte' | 'diversificacao'

export interface PosicaoRadar {
  id: number
  ativo: string
  valor: string
  vencimento: string
}

export interface EixoRadar {
  chave: ChaveEixo
  rotulo: string
  /** 0–100; null quando nenhuma posição reconhecida alimenta o eixo */
  valor: number | null
  fontes: string[]
  explicacao: string
}

export interface PerfilRadar {
  eixos: EixoRadar[]
  sugerido: PerfilSugerido | null
  declarado: string | null
  diverge: boolean
  avisos: string[]
}

/** Risco 0–100 por tipo de ativo (palavra-chave do nome, sem acento). */
const RISCO_POR_TIPO: Record<string, number> = {
  tesouro: 5,
  cdb: 15,
  lci: 15,
  lca: 15,
  debenture: 70,
  cra: 70,
  cri: 70,
  fundo: 60,
  fii: 60,
  acao: 90,
  acoes: 90,
  etf: 90,
}
const CREDITO_PRIVADO = new Set(['debenture', 'cra', 'cri'])
const LIMITE_LIQUIDEZ_DIAS = 90
const TETO_HORIZONTE_DIAS = 5 * 365
const LIMITE_CONSERVADOR = 35
const LIMITE_MODERADO = 60

const DIA_MS = 86_400_000

function semAcento(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

function tipoDoAtivo(ativo: string) {
  return semAcento(ativo)
    .split(/[^a-z]+/)
    .find((palavra) => palavra in RISCO_POR_TIPO)
}

function centavos(valor: string): bigint | null {
  const m = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(valor.trim())
  if (!m || m[1]) return null
  const cents = BigInt(m[2]) * 100n + BigInt((m[3] ?? '').padEnd(2, '0') || '0')
  return cents > 0n ? cents : null
}

function diaUtc(iso: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!m) return null
  const [ano, mes, dia] = [Number(m[1]), Number(m[2]), Number(m[3])]
  const data = new Date(Date.UTC(ano, mes - 1, dia))
  // rejeita datas que o calendário "rola" (ex.: 2026-13-45 ou 2026-02-30)
  if (data.getUTCFullYear() !== ano || data.getUTCMonth() !== mes - 1 || data.getUTCDate() !== dia) return null
  return data.getTime()
}

function razaoInteira(numerador: bigint, denominador: bigint) {
  return Number((numerador * 2n + denominador) / (2n * denominador))
}

function perfilDeclarado(tag: string | null | undefined): PerfilSugerido | null {
  if (!tag) return null
  const t = semAcento(tag)
  if (t.startsWith('conservador')) return 'Conservador'
  if (t.startsWith('moderad')) return 'Moderado'
  if (t.startsWith('arrojad') || t.startsWith('agressiv')) return 'Arrojado'
  return null
}

export function calcularPerfilRadar(
  posicoes: PosicaoRadar[],
  hoje: string,
  declaradoBruto?: string | null,
): PerfilRadar {
  const hojeMs = diaUtc(hoje)
  if (hojeMs === null) throw new Error(`perfil-radar: data de referência inválida "${hoje}"`)

  const avisos: string[] = []
  const validas: { id: number; ativo: string; cents: bigint; dias: number; tipo: string | undefined }[] = []
  for (const p of posicoes) {
    const cents = centavos(p.valor)
    const venc = diaUtc(p.vencimento)
    if (cents === null || venc === null) {
      avisos.push(`Posição #${p.id} (${p.ativo}) ignorada: valor ou vencimento inválido.`)
      continue
    }
    const dias = Math.max(0, Math.round((venc - hojeMs) / DIA_MS))
    validas.push({ id: p.id, ativo: p.ativo, cents, dias, tipo: tipoDoAtivo(p.ativo) })
  }

  const declarado = perfilDeclarado(declaradoBruto)
  if (validas.length === 0) {
    return { eixos: [], sugerido: null, declarado, diverge: false, avisos }
  }

  const reconhecidas = validas.filter((p) => p.tipo !== undefined)
  for (const p of validas.filter((v) => v.tipo === undefined)) {
    avisos.push(`Tipo de ativo não reconhecido: ${p.ativo} (posição #${p.id}); fora do cálculo de risco.`)
  }
  const fonte = (lista: { id: number }[]) => lista.map((p) => `posição #${p.id}`)

  const totalTodas = validas.reduce((s, p) => s + p.cents, 0n)
  const totalReconh = reconhecidas.reduce((s, p) => s + p.cents, 0n)

  let risco: number | null = null
  let credito: number | null = null
  if (totalReconh > 0n) {
    const soma = reconhecidas.reduce((s, p) => s + p.cents * BigInt(RISCO_POR_TIPO[p.tipo as string]), 0n)
    risco = razaoInteira(soma, totalReconh)
    const emCredito = reconhecidas
      .filter((p) => CREDITO_PRIVADO.has(p.tipo as string))
      .reduce((s, p) => s + p.cents, 0n)
    credito = razaoInteira(emCredito * 100n, totalReconh)
  }

  const curtas = validas.filter((p) => p.dias <= LIMITE_LIQUIDEZ_DIAS).reduce((s, p) => s + p.cents, 0n)
  const liquidez = razaoInteira(curtas * 100n, totalTodas)

  const somaPrazo = validas.reduce((s, p) => s + p.cents * BigInt(Math.min(p.dias, TETO_HORIZONTE_DIAS)), 0n)
  const horizonte = razaoInteira(somaPrazo * 100n, totalTodas * BigInt(TETO_HORIZONTE_DIAS))

  // 1 − HHI (concentração por posição), com participações em pontos-base inteiros
  const hhi = validas.reduce((s, p) => {
    const bp = (p.cents * 10_000n) / totalTodas
    return s + bp * bp
  }, 0n)
  const diversificacao = Math.round(100 - Number(hhi) / 1_000_000)

  const eixos: EixoRadar[] = [
    {
      chave: 'risco',
      rotulo: 'Risco da carteira',
      valor: risco,
      fontes: fonte(reconhecidas),
      explicacao: 'Média ponderada pelo valor: Tesouro 5, CDB/LCI/LCA 15, crédito privado 70, fundos 60, ações 90.',
    },
    {
      chave: 'credito',
      rotulo: 'Crédito privado',
      valor: credito,
      fontes: fonte(reconhecidas),
      explicacao: 'Parcela do valor em debêntures, CRA e CRI.',
    },
    {
      chave: 'liquidez',
      rotulo: 'Liquidez',
      valor: liquidez,
      fontes: fonte(validas),
      explicacao: `Parcela do valor que vence em até ${LIMITE_LIQUIDEZ_DIAS} dias (vencida conta como imediata).`,
    },
    {
      chave: 'horizonte',
      rotulo: 'Horizonte',
      valor: horizonte,
      fontes: fonte(validas),
      explicacao: 'Prazo médio ponderado até o vencimento; 100 equivale a 5 anos ou mais.',
    },
    {
      chave: 'diversificacao',
      rotulo: 'Diversificação',
      valor: diversificacao,
      fontes: fonte(validas),
      explicacao: 'Quanto menos concentrada em poucas posições, mais alto (1 − índice de concentração).',
    },
  ]

  const sugerido: PerfilSugerido | null =
    risco === null ? null : risco < LIMITE_CONSERVADOR ? 'Conservador' : risco < LIMITE_MODERADO ? 'Moderado' : 'Arrojado'

  return {
    eixos,
    sugerido,
    declarado,
    diverge: declarado !== null && sugerido !== null && declarado !== sugerido,
    avisos,
  }
}
