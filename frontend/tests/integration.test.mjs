import assert from 'node:assert/strict'
import { test } from 'node:test'
import { api } from '../src/lib/api.ts'
import { formatCurrency, formatElapsed } from '../src/lib/format.ts'

test('total financeiro acima do limite seguro mantém reais e centavos exatos', () => {
  assert.equal(formatCurrency('9007199254770993.01'), 'R$ 9.007.199.254.770.993,01')
  assert.equal(formatCurrency('80000.00'), 'R$ 80.000,00')
  assert.equal(formatCurrency('-0.01'), '-R$ 0,01')
})

test('ausência de carteira ou data não aparece como zero ou hoje', () => {
  assert.equal(formatCurrency(null), 'Não informado')
  assert.equal(formatElapsed(null), 'sem registro')
})

test('erro da API mantém campo e mensagem para corrigir revisão e tentar novamente', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ erro: { campo: 'revisao', mensagem: 'Item já revisado; recarregue.' } }), { status: 409 }))
  await assert.rejects(api('/api/clientes/1/contexto/2/revisar', { method: 'POST', body: {} }), /revisao: Item já revisado/)
})

test('proxy indisponível não vira dados fictícios ou sucesso vazio', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<html>erro proxy</html>', { status: 502 }))
  await assert.rejects(api('/api/pulse'), /Resposta inválida do servidor/)
})

test('leitura mantém IDs da API e encaminha cancelamento sem corpo ou segredo', async (t) => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(path, '/api/pulse')
    assert.equal(options.signal, controller.signal)
    assert.equal(options.method, 'GET')
    assert.equal(options.body, undefined)
    assert.deepEqual(options.headers, {})
    return new Response(JSON.stringify({ clients: [{ id: '2' }, { id: '1' }] }))
  })
  assert.deepEqual((await api('/api/pulse', { signal: controller.signal })).clients.map((c) => c.id), ['2', '1'])
})
