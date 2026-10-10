// Interface do MVP: lista priorizada, detalhe com resumo/alertas e formulários.
// Todo texto vindo da API entra via nodes de texto (sem innerHTML).
const app = document.getElementById("app");
let telaAtual = 0;
let pedidoDetalhe = 0;

const ROTULO_PRIORIDADE = { alta: "Alta", media: "Média", baixa: "Baixa" };
const COR_PRIORIDADE = {
  alta: "bg-red-100 text-red-800",
  media: "bg-amber-100 text-amber-800",
  baixa: "bg-slate-100 text-slate-700",
};
const CANAIS = { whatsapp: "WhatsApp", email: "E-mail", telefone: "Telefone", presencial: "Presencial" };
const ESTADOS = { positivo: "Positivo", atencao: "Atenção", negativo: "Negativo" };

function h(tag, props = {}, ...filhos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "className") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k in el) el[k] = v;
    else el.setAttribute(k, v);
  }
  for (const f of filhos.flat()) {
    if (f === null || f === undefined || f === false) continue;
    el.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return el;
}

async function api(caminho, opcoes = {}) {
  const init = { method: opcoes.method || "GET", headers: {} };
  if (opcoes.corpo !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(opcoes.corpo);
  }
  const resp = await fetch(caminho, init);
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro?.mensagem || `Erro ${resp.status}`);
  return dados;
}

const fmtData = (iso) => new Date(iso).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
const fmtDia = (iso) => iso.split("-").reverse().join("/");
const fmtFonte = (f) =>
  f ? `fonte: ${f.tipo_fonte} #${[].concat(f.id_fonte ?? []).join(",")}${f.data_referencia ? " · " + fmtDia(f.data_referencia) : ""}` : "";

const tagPrioridade = (p) =>
  h("span", { className: `text-xs px-2 py-1 rounded ${COR_PRIORIDADE[p]}` }, `Prioridade de atendimento: ${ROTULO_PRIORIDADE[p]}`);
const rotuloRelacionamento = (r) => `Relacionamento: ${r ? r.rotulo : "Não avaliado"}`;

const campo = (rotulo, controle) => h("label", { className: "block text-sm mb-2" }, h("span", { className: "block mb-1" }, rotulo), controle);
const estiloControle = "w-full border border-slate-300 rounded p-2 bg-white";
const botao = (texto, extra = {}) =>
  h("button", { type: "submit", className: "bg-slate-900 text-white rounded px-3 py-2 text-sm", ...extra }, texto);
const secao = (titulo, ...filhos) =>
  h("section", { className: "bg-white rounded shadow-sm p-3 mb-3" }, h("h2", { className: "font-semibold mb-2" }, titulo), ...filhos);
const aviso = (texto) => h("p", { className: "text-sm text-slate-500" }, texto);

// Troca o conteúdo ignorando filhos nulos (seções condicionais).
const montar = (...nos) => app.replaceChildren(...nos.filter(Boolean));

function formulario(onEnviar, ...filhos) {
  const erro = h("p", { className: "text-sm text-red-700 mt-2", role: "alert" });
  const form = h("form", {}, ...filhos, erro);
  let enviando = false;
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (enviando) return;
    const dados = new FormData(form);
    const controles = [...form.querySelectorAll("button, input, select, textarea")];
    const desabilitados = controles.map((controle) => controle.disabled);
    enviando = true;
    controles.forEach((controle) => { controle.disabled = true; });
    erro.textContent = "";
    try {
      await onEnviar(dados);
    } catch (e) {
      erro.textContent = e.message;
    } finally {
      controles.forEach((controle, i) => { controle.disabled = desabilitados[i]; });
      enviando = false;
    }
  });
  return form;
}

// ---------- Lista ----------
async function viewLista(tela) {
  const estado = { q: "", prioridade: "" };
  const lista = h("div");
  let pedidoLista = 0;
  async function carregar() {
    const pedido = ++pedidoLista;
    const params = new URLSearchParams();
    if (estado.q) params.set("q", estado.q);
    if (estado.prioridade) params.set("prioridade", estado.prioridade);
    try {
      const { clientes } = await api(`/api/clientes?${params}`);
      if (tela !== telaAtual || pedido !== pedidoLista) return;
      lista.replaceChildren(
        ...(clientes.length
          ? clientes.map((c) =>
              h("a", { href: `#/clientes/${c.id}`, className: "block bg-white rounded p-3 mb-2 shadow-sm" },
                h("div", { className: "font-medium" }, c.nome),
                h("div", { className: "flex flex-wrap gap-2 items-center mt-1" },
                  tagPrioridade(c.prioridade),
                  h("span", { className: "text-xs text-slate-600" }, rotuloRelacionamento(c.relacionamento)),
                  h("span", { className: "text-xs text-slate-600" },
                    `${c.alertas_pendentes} pendência(s)` + (c.proxima_pendencia ? ` · próxima ${fmtDia(c.proxima_pendencia)}` : ""))))
            )
          : [aviso("Nenhum cliente encontrado.")])
      );
    } catch (e) {
      if (tela !== telaAtual || pedido !== pedidoLista) return;
      lista.replaceChildren(h("p", { className: "text-red-700", role: "alert" }, e.message));
    }
  }
  const busca = h("input", { type: "search", placeholder: "Buscar por nome", className: estiloControle, "aria-label": "Buscar por nome" });
  busca.addEventListener("input", () => { estado.q = busca.value; carregar(); });
  const filtro = h("select", { className: estiloControle, "aria-label": "Filtrar por prioridade" },
    h("option", { value: "" }, "Todas as prioridades"),
    ...Object.entries(ROTULO_PRIORIDADE).map(([v, t]) => h("option", { value: v }, t)));
  filtro.addEventListener("change", () => { estado.prioridade = filtro.value; carregar(); });
  app.replaceChildren(h("div", { className: "grid gap-2 mb-3 sm:grid-cols-2" }, busca, filtro), lista);
  await carregar();
}

// ---------- Detalhe ----------
async function viewDetalhe(id, tela) {
  const pedido = ++pedidoDetalhe;
  const atual = () => tela === telaAtual && pedido === pedidoDetalhe;
  let d;
  try {
    d = await api(`/api/clientes/${id}`);
  } catch (e) {
    if (!atual()) return;
    app.replaceChildren(h("a", { href: "#/", className: "underline text-sm" }, "← Clientes"),
      h("p", { className: "text-red-700 mt-2", role: "alert" }, e.message));
    return;
  }
  if (!atual()) return;
  const recarregar = () => tela === telaAtual ? viewDetalhe(id, tela) : Promise.resolve();
  const pref = d.cliente.preferencias;
  const pendentes = d.alertas.filter((a) => a.estado === "pendente");
  const tratados = d.alertas.filter((a) => a.estado === "tratado");

  const itemAlerta = (a) =>
    h("li", { className: "border-t border-slate-100 py-2 first:border-0" },
      h("div", { className: "flex flex-wrap items-center gap-2" },
        h("span", { className: `text-xs px-2 py-1 rounded ${COR_PRIORIDADE[a.prioridade]}` }, ROTULO_PRIORIDADE[a.prioridade]),
        h("strong", {}, a.rotulo)),
      h("p", { className: "text-sm" }, a.motivo),
      h("p", { className: "text-xs text-slate-500" }, `${fmtFonte(a.fonte)}${a.fonte.descricao ? " · " + a.fonte.descricao : ""}`),
      a.estado === "pendente"
        ? h("button", { className: "mt-1 text-sm underline", onClick: async (ev) => {
            ev.target.disabled = true;
            try { await api("/api/alertas/tratar", { method: "POST", corpo: { cliente_id: d.cliente.id, chave_ocorrencia: a.chave_ocorrencia } }); await recarregar(); }
            catch (e) { ev.target.disabled = false; ev.target.after(h("span", { className: "text-red-700 text-sm ml-2", role: "alert" }, e.message)); }
          } }, "Marcar como tratado")
        : h("span", { className: "text-xs text-slate-500" }, "Tratado"));

  const formInteracao = formulario(async (fd) => {
      const corpo = { canal: fd.get("canal"), texto: fd.get("texto"), proximos_passos: fd.get("proximos_passos") };
      if (fd.get("ocorrida_em")) corpo.ocorrida_em = fd.get("ocorrida_em");
      await api(`/api/clientes/${id}/interacoes`, { method: "POST", corpo });
      await recarregar();
    },
    campo("Canal", h("select", { name: "canal", className: estiloControle },
      ...Object.entries(CANAIS).map(([v, t]) => h("option", { value: v, selected: v === pref.canal_preferido }, t)))),
    campo("O que aconteceu", h("textarea", { name: "texto", rows: 3, required: true, className: estiloControle })),
    campo("Quando ocorreu (opcional; padrão: agora)", h("input", { type: "datetime-local", name: "ocorrida_em", className: estiloControle })),
    campo("Próximos passos (opcional)", h("input", { name: "proximos_passos", className: estiloControle })),
    botao("Registrar interação"));

  const formRelacionamento = formulario(async (fd) => {
      await api(`/api/clientes/${id}/relacionamento`, { method: "POST", corpo: { estado: fd.get("estado"), justificativa: fd.get("justificativa") } });
      await recarregar();
    },
    campo("Estado", h("select", { name: "estado", className: estiloControle },
      ...Object.entries(ESTADOS).map(([v, t]) => h("option", { value: v, selected: d.relacionamento?.estado === v }, t)))),
    campo("Justificativa (obrigatória)", h("textarea", { name: "justificativa", rows: 2, required: true, className: estiloControle })),
    botao("Salvar avaliação"));

  const formPreferencias = formulario(async (fd) => {
      await api(`/api/clientes/${id}/preferencias`, { method: "PATCH", corpo: {
        canal_preferido: fd.get("canal_preferido") || null,
        intervalo_minimo_dias: Number(fd.get("intervalo_minimo_dias")),
        permite_assuntos_pessoais: fd.get("permite") === "on",
      } });
      await recarregar();
    },
    campo("Canal preferido", h("select", { name: "canal_preferido", className: estiloControle },
      h("option", { value: "" }, "Sem preferência"),
      ...Object.entries(CANAIS).map(([v, t]) => h("option", { value: v, selected: v === pref.canal_preferido }, t)))),
    campo("Intervalo mínimo entre contatos", h("select", { name: "intervalo_minimo_dias", className: estiloControle },
      ...[7, 14, 30].map((n) => h("option", { value: n, selected: n === pref.intervalo_minimo_dias }, `${n} dias`)))),
    h("label", { className: "flex items-center gap-2 text-sm mb-2" },
      h("input", { type: "checkbox", name: "permite", checked: pref.permite_assuntos_pessoais }),
      "Permite assuntos pessoais"),
    botao("Salvar preferências"));

  montar(
    h("a", { href: "#/", className: "underline text-sm" }, "← Clientes"),
    h("h1", { className: "text-xl font-semibold mt-2" }, d.cliente.nome),
    h("div", { className: "flex flex-wrap gap-2 items-center my-2" },
      tagPrioridade(d.prioridade),
      h("span", { className: "text-sm" }, rotuloRelacionamento(d.relacionamento))),
    secao("Resumo",
      h("ul", { className: "text-sm" }, ...d.resumo.fatos.map((f) =>
        h("li", { className: "mb-1" }, f.texto, h("span", { className: "block text-xs text-slate-500" }, fmtFonte(f.fonte))))),
      d.resumo.ausencias.length ? h("ul", { className: "text-sm text-slate-600 mt-1" }, ...d.resumo.ausencias.map((t) => h("li", {}, t))) : null),
    secao(`Alertas pendentes (${pendentes.length})`,
      pendentes.length ? h("ul", {}, ...pendentes.map(itemAlerta)) : aviso("Nenhum alerta pendente.")),
    tratados.length ? secao(`Alertas tratados (${tratados.length})`, h("ul", {}, ...tratados.map(itemAlerta))) : null,
    secao("Registrar interação", formInteracao),
    secao("Histórico de interações",
      d.interacoes.length
        ? h("ul", {}, ...d.interacoes.map((i) =>
            h("li", { className: "border-t border-slate-100 py-2 first:border-0 text-sm" },
              h("strong", {}, `${CANAIS[i.canal]} · ${fmtData(i.ocorrida_em)}`),
              h("p", {}, i.texto),
              i.proximos_passos ? h("p", { className: "text-slate-600" }, `Próximos passos: ${i.proximos_passos}`) : null,
              h("p", { className: "text-xs text-slate-500" }, `Registrada em ${fmtData(i.registrada_em)}`))))
        : aviso("Nenhuma interação registrada.")),
    secao("Posições",
      d.posicoes.length
        ? h("ul", { className: "text-sm" }, ...d.posicoes.map((p) =>
            h("li", { className: "mb-1" }, `${p.ativo} · R$ ${p.valor} · vence em ${fmtDia(p.vencimento)}`,
              h("span", { className: "block text-xs text-slate-500" }, p.fonte))))
        : aviso("Nenhuma posição cadastrada.")),
    secao("Datas importantes",
      d.datas_importantes.length
        ? h("ul", { className: "text-sm" }, ...d.datas_importantes.map((data) =>
            h("li", { className: "mb-1" },
              `Aniversário ${data.vinculo === "cliente" ? "do cliente" : `de familiar (${data.descricao})`} · ${String(data.dia).padStart(2, "0")}/${String(data.mes).padStart(2, "0")}`,
              h("span", { className: "block text-xs text-slate-500" }, `data_importante #${data.id} · ${data.fonte}`))))
        : aviso("Nenhuma data importante cadastrada.")),
    secao("Histórico de avaliações",
      d.historico_avaliacoes.length
        ? h("ul", { className: "text-sm" }, ...d.historico_avaliacoes.map((avaliacao) =>
            h("li", { className: "border-t border-slate-100 py-2 first:border-0" },
              h("strong", {}, `Relacionamento: ${ESTADOS[avaliacao.estado]} · ${fmtData(avaliacao.avaliada_em)}`),
              h("p", {}, avaliacao.justificativa),
              h("p", { className: "text-xs text-slate-500" }, `Assessor #${avaliacao.assessor_id} · avaliacao_relacionamento #${avaliacao.id}`))))
        : aviso("Não avaliado")),
    secao("Avaliar relacionamento", formRelacionamento),
    secao("Preferências de contato", formPreferencias));
}

// ---------- Roteamento ----------
function rotear() {
  const tela = ++telaAtual;
  montar(aviso("Carregando…"));
  const m = location.hash.match(/^#\/clientes\/(\d+)$/);
  (m ? viewDetalhe(Number(m[1]), tela) : viewLista(tela)).catch((e) => {
    if (tela === telaAtual) montar(h("p", { className: "text-red-700", role: "alert" }, `Erro ao carregar: ${e.message}`));
  });
}
window.addEventListener("hashchange", rotear);
rotear();
