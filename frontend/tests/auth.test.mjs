import assert from 'node:assert/strict'
import { test } from 'node:test'
import * as communication from '../src/lib/api.ts'

test('escrita envia CSRF da sessão por header e leitura mantém headers vazios', async (t) => {
  communication.setCsrfToken('token-ficticio')
  t.after(() => communication.setCsrfToken(''))
  t.mock.method(globalThis, 'fetch', async (_, options) => {
    assert.equal(options.credentials, 'same-origin')
    if (options.method === 'PATCH') {
      assert.equal(options.headers['X-CSRF-Token'], 'token-ficticio')
      assert.equal(options.headers['Content-Type'], 'application/json')
    } else assert.deepEqual(options.headers, {})
    return new Response('{}')
  })
  await communication.api('/api/clientes/1/preferencias', { method: 'PATCH', body: {} })
  await communication.api('/api/pulse')
})

test('401 de sessão anuncia encerramento e não repete gravação', async (t) => {
  const eventos = []
  const anterior = globalThis.dispatchEvent
  globalThis.dispatchEvent = (event) => { eventos.push(event.type); return true }
  t.after(() => { if (anterior) globalThis.dispatchEvent = anterior; else delete globalThis.dispatchEvent })
  let chamadas = 0
  t.mock.method(globalThis, 'fetch', async () => {
    chamadas++
    return new Response(JSON.stringify({ erro: { codigo: 'sessao_necessaria', mensagem: 'Entre novamente.' } }), { status: 401 })
  })
  await assert.rejects(communication.api('/api/clientes/1/interacoes', { method: 'POST', body: {} }), /Entre novamente/)
  assert.deepEqual(eventos, ['xp-pulse:sessao-necessaria'])
  assert.equal(chamadas, 1)
})

test('erro de credenciais permanece no formulário sem evento de expiração', async (t) => {
  const anterior = globalThis.dispatchEvent
  globalThis.dispatchEvent = () => { assert.fail('Credenciais erradas não são expiração de sessão.') }
  t.after(() => { if (anterior) globalThis.dispatchEvent = anterior; else delete globalThis.dispatchEvent })
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ erro: { codigo: 'credenciais_invalidas', mensagem: 'Usuário ou senha incorretos.' } }), { status: 401 }))
  await assert.rejects(communication.api('/api/auth/login', { method: 'POST', body: {} }), /Usuário ou senha incorretos/)
})

test('login consulta sessão, usa token atual e encaminha apenas os campos esperados', async (t) => {
  const auth = await import('../src/lib/auth.ts')
  const caminhos = []
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    caminhos.push(path)
    if (path.endsWith('/sessao')) return new Response(JSON.stringify({ autenticado: false, usuario: null, csrf_token: 'antes' }))
    assert.equal(options.headers['X-CSRF-Token'], 'antes')
    assert.deepEqual(JSON.parse(options.body), { usuario: 'admin', senha: 'admin' })
    return new Response(JSON.stringify({ autenticado: true, usuario: 'admin', csrf_token: 'depois' }))
  })
  assert.equal((await auth.entrar('admin', 'admin')).autenticado, true)
  assert.deepEqual(caminhos, ['/api/auth/sessao', '/api/auth/login'])
  t.after(() => communication.setCsrfToken(''))
})

test('logout renova token antes de revogar e aceita sessão já encerrada', async (t) => {
  const auth = await import('../src/lib/auth.ts')
  let autenticado = true
  let posts = 0
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    if (path.endsWith('/logout')) {
      posts++
      assert.equal(options.headers['X-CSRF-Token'], 'atual')
      autenticado = false
    }
    return new Response(JSON.stringify({ autenticado, usuario: autenticado ? 'admin' : null, csrf_token: 'atual' }))
  })
  assert.equal((await auth.sair()).autenticado, false)
  assert.equal((await auth.sair()).autenticado, false)
  assert.equal(posts, 1)
  t.after(() => communication.setCsrfToken(''))
})

test('falha de rede ao consultar sessão é erro, sem conceder acesso', async (t) => {
  const auth = await import('../src/lib/auth.ts')
  t.mock.method(globalThis, 'fetch', async () => { throw new Error('Rede indisponível') })
  await assert.rejects(auth.consultarSessao(), /Rede indisponível/)
})
