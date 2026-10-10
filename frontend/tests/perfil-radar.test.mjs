import assert from 'node:assert/strict'
import { test } from 'node:test'
import { calcularPerfilRadar } from '../src/lib/perfil-radar.ts'

const HOJE = '2026-10-10'
const pos = (id, ativo, valor, vencimento) => ({ id, ativo, valor, vencimento })
const eixo = (r, chave) => r.eixos.find((e) => e.chave === chave)

test('CA72: carteira só de baixo risco sugere Conservador', () => {
  const r = calcularPerfilRadar(
    [pos(1, 'CDB Banco Exemplo', '50000.00', '2026-10-15'), pos(2, 'LCI Banco Exemplo', '30000.00', '2026-11-10')],
    HOJE,
    'Moderado; objetivo: aposentadoria',
  )
  assert.equal(r.sugerido, 'Conservador')
  assert.ok(eixo(r, 'risco').valor < 35)
  assert.equal(eixo(r, 'credito').valor, 0)
})

test('CA72: crédito privado dominante sobe risco e crédito privado', () => {
  const r = calcularPerfilRadar(
    [pos(5, 'CRA Exemplo', '80000.00', '2026-10-17'), pos(6, 'LCA Exemplo', '15000.00', '2026-10-18')],
    HOJE,
  )
  assert.ok(eixo(r, 'credito').valor > 80)
  assert.ok(eixo(r, 'risco').valor > 50)
  assert.deepEqual(eixo(r, 'risco').fontes, ['posição #5', 'posição #6'])
})

test('CA73: sem posições não há eixos nem sugestão', () => {
  const r = calcularPerfilRadar([], HOJE, 'Moderado')
  assert.deepEqual(r.eixos, [])
  assert.equal(r.sugerido, null)
  assert.equal(r.diverge, false)
})

test('CA73: ativo desconhecido fica fora do risco e gera aviso', () => {
  const r = calcularPerfilRadar([pos(1, 'Cripto XPTO', '1000.00', '2026-12-01'), pos(2, 'CDB X', '1000.00', '2026-12-01')], HOJE)
  assert.equal(r.avisos.length, 1)
  assert.match(r.avisos[0], /Cripto XPTO/)
  assert.deepEqual(eixo(r, 'risco').fontes, ['posição #2'])
})

test('CA73: só ativos desconhecidos deixam o risco ausente, sem inventar valor', () => {
  const r = calcularPerfilRadar([pos(1, 'Cripto XPTO', '1000.00', '2026-12-01')], HOJE)
  assert.equal(eixo(r, 'risco').valor, null)
  assert.equal(r.sugerido, null)
})

test('CA74: posição vencida conta como prazo zero e liquidez imediata', () => {
  const r = calcularPerfilRadar([pos(3, 'Debênture Exemplo', '20000.00', '2026-10-08')], HOJE)
  assert.equal(eixo(r, 'liquidez').valor, 100)
  assert.equal(eixo(r, 'horizonte').valor, 0)
})

test('CA75: divergência entre declarado e sugerido é exibida', () => {
  const r = calcularPerfilRadar([pos(1, 'Tesouro Exemplo', '10000.00', '2026-10-10')], HOJE, 'Arrojado')
  assert.equal(r.declarado, 'Arrojado')
  assert.equal(r.sugerido, 'Conservador')
  assert.equal(r.diverge, true)
})

test('diversificação: um ativo só é 0 e dois iguais é 50', () => {
  assert.equal(eixo(calcularPerfilRadar([pos(1, 'CDB A', '100.00', '2027-01-01')], HOJE), 'diversificacao').valor, 0)
  assert.equal(
    eixo(calcularPerfilRadar([pos(1, 'CDB A', '100.00', '2027-01-01'), pos(2, 'CDB B', '100.00', '2027-01-01')], HOJE), 'diversificacao').valor,
    50,
  )
})

test('data de referência usa o dia de São Paulo, não o dia UTC', async () => {
  const { diaLocal } = await import('../src/lib/format.ts')
  assert.equal(diaLocal('2026-10-11T01:30:00+00:00'), '2026-10-10')
  assert.equal(diaLocal('2026-10-10T17:51:09.379673+00:00'), '2026-10-10')
  assert.throws(() => diaLocal(''), /Instante inválido/)
})

test('formas femininas do perfil declarado são reconhecidas', () => {
  const r = calcularPerfilRadar([pos(1, 'Tesouro X', '100.00', '2026-10-10')], HOJE, 'Moderada')
  assert.equal(r.declarado, 'Moderado')
})
