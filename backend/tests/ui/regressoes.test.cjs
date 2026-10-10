// Executa o JS entregue ao navegador, com DOM e rede controlados, sem dependências.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

class Elemento {
  constructor(tag = '#texto', texto = '') {
    this.tagName = tag;
    this.children = [];
    this.listeners = {};
    this.attributes = {};
    this.texto = texto;
    for (const prop of ['className', 'type', 'value', 'href', 'name', 'placeholder']) this[prop] = '';
    for (const prop of ['selected', 'checked', 'disabled', 'required']) this[prop] = false;
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; this.texto = ''; }
  setAttribute(k, v) { this.attributes[k] = v; }
  addEventListener(k, fn) { (this.listeners[k] ??= []).push(fn); }
  disparar(k) { return Promise.all((this.listeners[k] ?? []).map(fn => fn({
    target: this, currentTarget: this, preventDefault() {},
  }))); }
  get textContent() { return this.texto + this.children.map(n => n.textContent).join(' '); }
  set textContent(v) { this.texto = v; this.children = []; }
  querySelectorAll(seletor) {
    const tags = seletor.split(',').map(s => s.trim());
    return this.children.flatMap(n => [...(tags.includes(n.tagName) ? [n] : []), ...n.querySelectorAll(seletor)]);
  }
}

const proximoTurno = () => new Promise(resolve => setImmediate(resolve));
const lista = nome => ({ clientes: [{ id: 1, nome, prioridade: 'baixa',
  alertas_pendentes: 0, proxima_pendencia: null, relacionamento: null }] });
const detalhe = (id, nome = `Cliente ${id}`) => ({
  cliente: { id, nome, preferencias: { canal_preferido: 'email', intervalo_minimo_dias: 7,
    permite_assuntos_pessoais: true } },
  prioridade: 'baixa', relacionamento: null, historico_avaliacoes: [],
  resumo: { fatos: [], ausencias: [] }, alertas: [], posicoes: [], interacoes: [], datas_importantes: [],
});

async function iniciar() {
  const app = new Elemento('main');
  const requisicoes = [];
  const eventos = {};
  const location = { hash: '#/' };
  const contexto = {
    Node: Elemento, URLSearchParams, location,
    document: { getElementById: () => app, createElement: tag => new Elemento(tag),
      createTextNode: texto => new Elemento('#texto', texto) },
    window: { addEventListener: (nome, fn) => { eventos[nome] = fn; } },
    FormData: class {
      constructor(form) { this.campos = form.querySelectorAll('input, select, textarea'); }
      get(nome) {
        const campo = this.campos.find(c => c.name === nome);
        if (!campo) return null;
        if (campo.type === 'checkbox') return campo.checked ? 'on' : null;
        if (campo.tagName === 'select') {
          const op = campo.children.find(o => o.selected) ?? campo.children[0];
          return campo.value || op?.value;
        }
        return campo.value;
      }
    },
    fetch: (url, init) => new Promise((resolve, reject) => {
      requisicoes.push({ url, init, reject, responder: (dados, status = 200) =>
        resolve({ ok: status < 400, status, json: async () => dados }) });
    }),
  };
  runInNewContext(readFileSync(join(__dirname, '../../app/static/js/app.js'), 'utf8'), contexto);
  requisicoes[0].responder({ clientes: [] });
  await proximoTurno();
  return { app, requisicoes, navegar(id) {
    location.hash = id === null ? '#/' : `#/clientes/${id}`;
    eventos.hashchange();
  } };
}

test('busca mantém resultado atual quando a resposta antiga chega depois', async () => {
  const tela = await iniciar();
  const busca = tela.app.querySelectorAll('input')[0];
  busca.value = 'Ana'; await busca.disparar('input');
  busca.value = 'Carla'; await busca.disparar('input');
  tela.requisicoes[2].responder(lista('Carla')); await proximoTurno();
  tela.requisicoes[1].responder(lista('Ana')); await proximoTurno();
  assert.match(tela.app.textContent, /Carla/);
  assert.doesNotMatch(tela.app.textContent, /Ana/);
});

test('resposta de detalhe antigo não substitui o cliente atual', async () => {
  const tela = await iniciar();
  tela.navegar(1); tela.navegar(2);
  tela.requisicoes[2].responder(detalhe(2)); await proximoTurno();
  tela.requisicoes[1].responder(detalhe(1)); await proximoTurno();
  assert.match(tela.app.textContent, /Cliente 2/);
  assert.doesNotMatch(tela.app.textContent, /Cliente 1/);
});

test('erro atrasado de detalhe não apaga a lista após voltar', async () => {
  const tela = await iniciar();
  tela.navegar(1); tela.navegar(null);
  tela.requisicoes[2].responder(lista('Carla')); await proximoTurno();
  tela.requisicoes[1].responder({ erro: { mensagem: 'Erro antigo' } }, 404); await proximoTurno();
  assert.match(tela.app.textContent, /Carla/);
  assert.doesNotMatch(tela.app.textContent, /Erro antigo/);
});

test('duas submissões durante o envio geram somente um POST', async () => {
  const tela = await iniciar();
  tela.navegar(5); tela.requisicoes[1].responder(detalhe(5)); await proximoTurno();
  const form = tela.app.querySelectorAll('form')[0];
  form.querySelectorAll('textarea')[0].value = 'Contato realizado';
  const envio = form.disparar('submit');
  const repetido = form.disparar('submit');
  assert.equal(tela.requisicoes.filter(r => r.init.method === 'POST').length, 1);
  assert.equal(form.querySelectorAll('button')[0].disabled, true);
  tela.requisicoes[2].responder({ interacao: {} }, 201);
  await proximoTurno();
  tela.requisicoes[3]?.responder(detalhe(5));
  await Promise.all([envio, repetido]);
});

test('falha mantém o conteúdo e permite tentar o envio novamente', async () => {
  const tela = await iniciar();
  tela.navegar(5); tela.requisicoes[1].responder(detalhe(5)); await proximoTurno();
  const form = tela.app.querySelectorAll('form')[0];
  const texto = form.querySelectorAll('textarea')[0]; texto.value = 'Conteúdo preservado';
  const envio = form.disparar('submit');
  tela.requisicoes[2].responder({ erro: { mensagem: 'Serviço indisponível' } }, 503);
  await envio;
  assert.equal(texto.value, 'Conteúdo preservado');
  assert.equal(form.querySelectorAll('button')[0].disabled, false);
  assert.match(form.textContent, /Serviço indisponível/);
  const tentativa = form.disparar('submit');
  assert.equal(tela.requisicoes.filter(r => r.init.method === 'POST').length, 2);
  tela.requisicoes[3].responder({ erro: { mensagem: 'Serviço indisponível' } }, 503);
  await tentativa;
});

test('envio concluído após navegar não volta ao cliente anterior', async () => {
  const tela = await iniciar();
  tela.navegar(5); tela.requisicoes[1].responder(detalhe(5)); await proximoTurno();
  const form = tela.app.querySelectorAll('form')[0];
  const envio = form.disparar('submit');
  tela.navegar(1); tela.requisicoes[3].responder(detalhe(1)); await proximoTurno();
  tela.requisicoes[2].responder({ interacao: {} }, 201); await proximoTurno();
  assert.equal(tela.requisicoes.length, 4, 'Não deve recarregar o cliente anterior');
  assert.match(tela.app.textContent, /Cliente 1/);
  await envio;
});

test('detalhe exibe datas importantes e histórico de avaliações com origem', async () => {
  const tela = await iniciar();
  const d = detalhe(1);
  d.datas_importantes = [{ id: 8, tipo: 'aniversario', vinculo: 'familiar',
    descricao: 'Filha', dia: 12, mes: 10, fonte: 'Registro fictício do assessor' }];
  d.historico_avaliacoes = [{ id: 9, estado: 'atencao', justificativa: 'Aguardando retorno combinado',
    assessor_id: 1, avaliada_em: '2026-10-10T18:00:00+00:00' }];
  tela.navegar(1); tela.requisicoes[1].responder(d); await proximoTurno();
  assert.match(tela.app.textContent, /Datas importantes/);
  assert.match(tela.app.textContent, /Filha/);
  assert.match(tela.app.textContent, /12\/10/);
  assert.match(tela.app.textContent, /Registro fictício do assessor/);
  assert.match(tela.app.textContent, /Histórico de avaliações/);
  assert.match(tela.app.textContent, /Aguardando retorno combinado/);
  assert.match(tela.app.textContent, /Assessor #1/);
});
