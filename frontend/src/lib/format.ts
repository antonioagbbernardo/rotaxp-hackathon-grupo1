const currency = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

const monthYear = new Intl.DateTimeFormat('pt-BR', {
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

export function formatCurrency(value: string | number | null) {
  if (value === null) return 'Não informado'
  if (typeof value === 'number') return currency.format(value)
  const [whole, fraction = '00'] = value.split('.')
  const integer = BigInt(whole)
  const formatted = new Intl.NumberFormat('pt-BR').format(integer < 0n ? -integer : integer)
  return `${value.startsWith('-') ? '-' : ''}R$ ${formatted},${fraction.padEnd(2, '0').slice(0, 2)}`
}

export function formatDate(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })
}

/** Aceita mês ISO ou data ISO completa e apresenta mês/ano. */
export function formatMonth(isoMonth: string) {
  const month = /^(\d{4})-(0[1-9]|1[0-2])(?:$|-[0-3]\d(?:$|T))/.exec(isoMonth)
  if (!month) return 'Data não informada'
  return monthYear.format(new Date(`${month[1]}-${month[2]}-01T00:00:00Z`)).replace(' de ', ' ')
}

export function capitalize(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function formatElapsed(minutes: number | null) {
  if (minutes === null) return 'sem registro'
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `há ${hours} h`
  const days = Math.floor(hours / 24)
  return `há ${days} ${days === 1 ? 'dia' : 'dias'}`
}

export function getInitials(name: string) {
  const parts = name.replace(/\([^)]*\)/g, '').trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase()
}

const diaSaoPaulo = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'America/Sao_Paulo',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

/** Instante ISO (UTC) -> dia civil "YYYY-MM-DD" em America/Sao_Paulo, como o Clock do backend. */
export function diaLocal(iso: string) {
  const data = new Date(iso)
  if (Number.isNaN(data.getTime())) throw new Error(`Instante inválido: "${iso}"`)
  return diaSaoPaulo.format(data)
}
