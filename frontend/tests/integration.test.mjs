import assert from 'node:assert/strict'
import { test } from 'node:test'
import { api } from '../src/lib/api.ts'
import { formatCurrency, formatElapsed, formatMonth } from '../src/lib/format.ts'

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


test('data de cadastro completa não interrompe a renderização do perfil', () => {
  assert.equal(formatMonth('2021-03-15'), formatMonth('2021-03'))
  assert.equal(formatMonth('2021-03-15T00:00:00Z'), formatMonth('2021-03'))
  assert.equal(formatMonth(''), 'Data não informada')
  assert.equal(formatMonth('2021-13-15'), 'Data não informada')
})

test('perfil editável e cabeçalho preservam o nome e contatos salvos sem substituições', async (t) => {
  const perfil = { name: 'Assessor Fictício', role: 'Assessor de investimentos', email: 'ficticio@example.com', phone: '', office: 'Escritório fictício' }
  t.mock.method(globalThis, 'fetch', async (path) => new Response(JSON.stringify(
    path === '/api/pulse/assessor' ? perfil : { advisor: { name: perfil.name, role: perfil.role }, clients: [] })))
  assert.deepEqual(await api('/api/pulse/assessor'), perfil)
  assert.deepEqual((await api('/api/pulse')).advisor, { name: perfil.name, role: perfil.role })
})
