// Interface do MVP: lista priorizada, detalhe com resumo/alertas e formulários.
// Todo texto vindo da API entra via nodes de texto (sem innerHTML).
const app = document.getElementById("app");

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
  if (!resp.ok) throw new Error(dados.erro?.mensagem
    ? `${dados.erro.campo ? dados.erro.campo + ": " : ""}${dados.erro.mensagem}` : `Erro ${resp.status}`);
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
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (form.dataset.enviando) return;
    form.dataset.enviando = "true";
    const botoes = [...form.querySelectorAll("button")];
    botoes.forEach((b) => { b.disabled = true; });
    erro.textContent = "";
    try {
      await onEnviar(new FormData(form));
    } catch (e) {
      erro.textContent = e.message;
    } finally {
      delete form.dataset.enviando;
      botoes.forEach((b) => { b.disabled = false; });
    }
  });
  return form;
}

// ---------- Lista ----------
async function viewLista() {
  const estado = { q: "", prioridade: "" };
  const lista = h("div");
  const pendencias = h("div");
  const resultadoImportacao = h("p", { className: "text-sm mt-2", role: "status" });
  async function carregarPendencias() {
    try {
      const { pendencias: docs } = await api("/api/fontes/pendencias");
      pendencias.replaceChildren(docs.length
        ? h("ul", { className: "text-sm" }, ...docs.map((f) =>
            h("li", { className: "border-t border-slate-100 py-2 first:border-0" },
              `${f.origem} · ${f.registro_id} · versão ${f.versao}${f.atual ? " atual" : " anterior"}`,
              h("p", {}, `ID recebido: ${f.cliente_referencia ?? "não informado"}. Sem associação a cliente.`))))
        : aviso("Nenhuma fonte com identidade pendente."));
    } catch (e) {
      pendencias.replaceChildren(h("p", { className: "text-red-700 text-sm", role: "alert" }, e.message));
    }
  }
  const enviarArquivo = botao("Importar fonte fictícia");
  const formFonte = formulario(async (fd) => {
    resultadoImportacao.textContent = "Importando…";
    try {
      const arquivo = fd.get("arquivo");
      if (!arquivo || !arquivo.size) throw new Error("Selecione um arquivo JSON fictício.");
      let corpo;
      try { corpo = JSON.parse(await arquivo.text()); }
      catch { throw new Error("O arquivo deve conter JSON válido."); }
      const r = await api("/api/fontes/importar", { method: "POST", corpo });
      resultadoImportacao.textContent = `${r.importados} documento(s) importado(s), ${r.reutilizados} reutilizado(s), ${r.pendentes} com identidade pendente neste lote.`;
      await Promise.all([carregar(), carregarPendencias()]);
    } catch (e) {
      resultadoImportacao.textContent = "Importação não concluída. Corrija o arquivo e tente novamente.";
      throw e;
    } finally {
      enviarArquivo.disabled = false;
    }
  }, campo("Arquivo JSON fictício", h("input", { type: "file", name: "arquivo", accept: ".json,application/json", required: true, className: estiloControle })),
    enviarArquivo, resultadoImportacao);
  async function carregar() {
    const params = new URLSearchParams();
    if (estado.q) params.set("q", estado.q);
    if (estado.prioridade) params.set("prioridade", estado.prioridade);
    try {
      const { clientes } = await api(`/api/clientes?${params}`);
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
      lista.replaceChildren(h("p", { className: "text-red-700", role: "alert" }, e.message));
    }
  }
  const busca = h("input", { type: "search", placeholder: "Buscar por nome", className: estiloControle, "aria-label": "Buscar por nome" });
  busca.addEventListener("input", () => { estado.q = busca.value; carregar(); });
  const filtro = h("select", { className: estiloControle, "aria-label": "Filtrar por prioridade" },
    h("option", { value: "" }, "Todas as prioridades"),
    ...Object.entries(ROTULO_PRIORIDADE).map(([v, t]) => h("option", { value: v }, t)));
  filtro.addEventListener("change", () => { estado.prioridade = filtro.value; carregar(); });
  app.replaceChildren(h("div", { className: "grid gap-2 mb-3 sm:grid-cols-2" }, busca, filtro), lista,
    secao("Fontes existentes — demonstração",
      aviso("Importe o JSON fictício fornecido para a demo. No cliente, processe o contexto com IA e revise as propostas com suas evidências."), formFonte),
    secao("Identidades pendentes", aviso("Estes documentos não entram no histórico de nenhum cliente. Resolução manual será uma próxima etapa."), pendencias));
  await Promise.all([carregar(), carregarPendencias()]);
}

// O contexto prepara o atendimento; decisões e uso continuam com o assessor.
async function painelContexto(id, recarregar) {
  let dados;
  try { dados = await api(`/api/clientes/${id}/contexto`); }
  catch (e) {
    return secao("Contexto para preparar o atendimento",
      h("p", { className: "text-red-700 text-sm", role: "alert" }, e.message),
      botao("Tentar carregar novamente", { type: "button", onClick: recarregar }));
  }
  const status = h("p", { className: "text-sm my-2", role: "status" });
  const processar = formulario(async () => {
    status.textContent = "Analisando fontes; aguarde até 30 segundos…";
    try {
      const r = await api(`/api/clientes/${id}/contexto/processar`, { method: "POST" });
      status.textContent = r.reutilizado ? "Sem fontes novas: contexto reutilizado." : `${r.novos} proposta(s) aguardando revisão.`;
      await atualizar();
    } catch (e) { status.textContent = "Análise não concluída. O contexto anterior foi preservado."; throw e; }
  }, botao("Processar fontes novas com IA"), status);
  const listas = h("div");
  const rotulos = { pendente: "Aguardando revisão", confirmado: "Aprovado", corrigido: "Corrigido pelo assessor", descartado: "Descartado", adiado: "Adiado" };
  function item(i) {
    const acao = h("select", { name: "acao", className: estiloControle },
      ...Object.entries({ aprovar: "Aprovar", corrigir: "Corrigir", descartar: "Descartar", adiar: "Adiar" }).map(([v, t]) => h("option", { value: v }, t)));
    const valor = h("textarea", { name: "valor", className: estiloControle, rows: 2, maxLength: 500, value: i.valor_revisado || i.valor_original });
    const dia = h("input", { type: "date", name: "adiado_ate", className: estiloControle });
    const campoValor = campo("Valor corrigido", valor), campoDia = campo("Retomar revisão em", dia);
    function ajustar() {
      campoValor.hidden = acao.value !== "corrigir"; valor.required = !campoValor.hidden;
      campoDia.hidden = acao.value !== "adiar"; dia.required = !campoDia.hidden;
    }
    acao.addEventListener("change", ajustar); ajustar();
    const revisao = formulario(async (fd) => {
      const corpo = { acao: fd.get("acao"), motivo: fd.get("motivo"), revisao: i.revisao };
      if (corpo.acao === "corrigir") corpo.valor = fd.get("valor");
      if (corpo.acao === "adiar") corpo.adiado_ate = fd.get("adiado_ate");
      await api(`/api/clientes/${id}/contexto/${i.id}/revisar`, { method: "POST", corpo });
      await atualizar();
    }, campo("Decisão do assessor", acao), campoValor, campoDia,
      campo("Motivo da decisão", h("input", { name: "motivo", required: true, maxLength: 1000, className: estiloControle })), botao("Registrar decisão"));
    const assunto = formulario(async (fd) => {
      await api(`/api/clientes/${id}/assuntos/${encodeURIComponent(i.assunto)}`, { method: "POST",
        corpo: { bloqueado: !i.bloqueado, motivo: fd.get("motivo_assunto") } });
      await atualizar();
    }, aviso(i.bloqueado ? "Assunto bloqueado para contato com este cliente. O contexto permanece." : "Este assunto não está bloqueado para este cliente."),
      campo("Motivo para mudar a permissão do assunto", h("input", { name: "motivo_assunto", required: true, maxLength: 1000, className: estiloControle })),
      botao(i.bloqueado ? "Permitir assunto novamente" : "Bloquear assunto para contato"));
    return h("article", { className: "border border-slate-200 rounded p-3 my-2 min-w-0" },
      h("p", { className: "text-xs text-slate-600" }, `${rotulos[i.estado]} · ${i.tipo === "hipotese" ? "Hipótese" : "Fato extraído"} · sujeito: ${i.sujeito} · ${i.categoria}`),
      h("p", { className: "font-medium my-2 whitespace-pre-wrap" }, i.valor_revisado || i.valor_original),
      i.valor_revisado ? aviso(`Valor original da IA: ${i.valor_original}`) : null,
      i.estado === "adiado" ? aviso(`Adiado até ${fmtDia(i.adiado_ate)}`) : null,
      !i.evidencia_atual ? aviso("Evidência de versão anterior; confira a fonte atual.") : null,
      i.conflitos.length ? h("p", { className: "text-sm text-amber-800 my-2" }, `Possível divergência com item(ns) ${i.conflitos.join(", ")}. Diferença textual exige sua avaliação.`) : null,
      h("details", {}, h("summary", { className: "text-sm underline" }, "Conferir evidências e revisões"),
        ...i.evidencias.map((e) => h("div", { className: "text-sm my-2" },
          aviso(`${e.origem} · ${e.registro_id} · versão ${e.versao}${e.campo ? " · campo " + e.campo : ""}`),
          h("blockquote", { className: "whitespace-pre-wrap border-l-2 pl-2" }, e.trecho))),
        ...i.historico_revisoes.map((r) => aviso(`${fmtData(r.revisada_em)} · ${r.acao}: ${r.motivo}`))),
      h("details", { open: i.estado === "pendente", className: "my-2" }, h("summary", { className: "text-sm underline" }, "Revisar proposta"), revisao),
      h("details", {}, h("summary", { className: "text-sm underline" }, "Preferência deste assunto"), assunto));
  }
  function renderizar() {
    const pendentes = dados.itens.filter((i) => i.estado === "pendente");
    const outros = dados.itens.filter((i) => i.estado !== "pendente");
    listas.replaceChildren(aviso(`${dados.fontes_novas} fonte(s) nova(s) · ${dados.modelo}`),
      h("h3", { className: "font-semibold mt-3" }, `Fila de revisão (${pendentes.length})`),
      ...(pendentes.length ? pendentes.map(item) : [aviso("Nenhuma proposta aguardando revisão.")]),
      h("h3", { className: "font-semibold mt-3" }, `Contexto e decisões registradas (${outros.length})`), ...outros.map(item));
  }
  async function atualizar() { dados = await api(`/api/clientes/${id}/contexto`); renderizar(); }
  renderizar();
  return secao("Contexto para preparar o atendimento",
    aviso("A IA organiza propostas com fontes para poupar sua busca. Você confere, corrige e decide o que usar na relação com o investidor. Nenhuma mensagem será enviada."),
    !dados.configurado ? aviso("IA ainda sem chave configurada no backend. Seu contexto permanece disponível.") : null, processar, listas);
}

// ---------- Detalhe ----------
async function viewDetalhe(id) {
  let d;
  try {
    d = await api(`/api/clientes/${id}`);
  } catch (e) {
    app.replaceChildren(h("a", { href: "#/", className: "underline text-sm" }, "← Clientes"),
      h("p", { className: "text-red-700 mt-2", role: "alert" }, e.message));
    return;
  }
  const recarregar = () => viewDetalhe(id);
  const contexto = await painelContexto(id, recarregar);
  let fontes = [], erroFontes = null;
  try { ({ fontes } = await api(`/api/clientes/${id}/fontes`)); }
  catch (e) { erroFontes = e.message; }
  const fontesAtuais = new Map(fontes.filter((f) => f.atual && f.interacao_id).map((f) => [f.interacao_id, f]));
  const identificarFonte = (f) => `${f.origem} · ${f.registro_id} · versão ${f.versao}`;
  const itemFonte = (f) => h("li", { className: "border-t border-slate-100 py-2 first:border-0 text-sm" },
    h("details", {}, h("summary", { className: "font-medium" },
      `${f.tipo === "formulario" ? "Formulário" : CANAIS[f.canal]} · ${identificarFonte(f)} · ${f.atual ? "versão atual" : "versão anterior"}`),
      h("p", { className: "text-xs text-slate-500 my-2" }, `Ocorrência: ${fmtData(f.ocorrida_em)} · importação: ${fmtData(f.importada_em)}`),
      f.tipo === "formulario"
        ? h("dl", {}, ...Object.entries(f.conteudo).flatMap(([k, v]) => [h("dt", { className: "font-medium" }, k), h("dd", { className: "mb-2 whitespace-pre-wrap" }, v)]))
        : h("p", { className: "whitespace-pre-wrap" }, f.conteudo)));
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
            try { await api("/api/alertas/tratar", { method: "POST", corpo: { cliente_id: d.cliente.id, chave_ocorrencia: a.chave_ocorrencia } }); recarregar(); }
            catch (e) { ev.target.disabled = false; ev.target.after(h("span", { className: "text-red-700 text-sm ml-2", role: "alert" }, e.message)); }
          } }, "Marcar como tratado")
        : h("span", { className: "text-xs text-slate-500" }, "Tratado"));

  const formInteracao = formulario(async (fd) => {
      const corpo = { canal: fd.get("canal"), texto: fd.get("texto"), proximos_passos: fd.get("proximos_passos") };
      if (fd.get("ocorrida_em")) corpo.ocorrida_em = fd.get("ocorrida_em");
      await api(`/api/clientes/${id}/interacoes`, { method: "POST", corpo });
      recarregar();
    },
    campo("Canal", h("select", { name: "canal", className: estiloControle },
      ...Object.entries(CANAIS).map(([v, t]) => h("option", { value: v, selected: v === pref.canal_preferido }, t)))),
    campo("O que aconteceu", h("textarea", { name: "texto", rows: 3, required: true, className: estiloControle })),
    campo("Quando ocorreu (opcional; padrão: agora)", h("input", { type: "datetime-local", name: "ocorrida_em", className: estiloControle })),
    campo("Próximos passos (opcional)", h("input", { name: "proximos_passos", className: estiloControle })),
    botao("Registrar interação"));

  const formRelacionamento = formulario(async (fd) => {
      await api(`/api/clientes/${id}/relacionamento`, { method: "POST", corpo: { estado: fd.get("estado"), justificativa: fd.get("justificativa") } });
      recarregar();
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
      recarregar();
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
    secao("Fontes do cliente",
      aviso("Evidências originais do formulário e das conversas. Confirmação e correção acontecem na revisão de contexto."),
      erroFontes ? h("p", { className: "text-red-700 text-sm", role: "alert" }, erroFontes)
        : fontes.length ? h("ul", {}, ...fontes.map(itemFonte)) : aviso("Nenhuma fonte importada para este cliente.")),
    contexto,
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
              fontesAtuais.has(i.id) ? h("p", { className: "text-xs text-slate-500" }, `Fonte importada: ${identificarFonte(fontesAtuais.get(i.id))}`) : null,
              i.proximos_passos ? h("p", { className: "text-slate-600" }, `Próximos passos: ${i.proximos_passos}`) : null,
              h("p", { className: "text-xs text-slate-500" }, `Registrada em ${fmtData(i.registrada_em)}`))))
        : aviso("Nenhuma interação registrada.")),
    secao("Posições",
      d.posicoes.length
        ? h("ul", { className: "text-sm" }, ...d.posicoes.map((p) =>
            h("li", { className: "mb-1" }, `${p.ativo} · R$ ${p.valor} · vence em ${fmtDia(p.vencimento)}`,
              h("span", { className: "block text-xs text-slate-500" }, p.fonte))))
        : aviso("Nenhuma posição cadastrada.")),
    secao("Avaliar relacionamento", formRelacionamento),
    secao("Preferências de contato", formPreferencias));
}

// ---------- Roteamento ----------
function rotear() {
  const m = location.hash.match(/^#\/clientes\/(\d+)$/);
  (m ? viewDetalhe(Number(m[1])) : viewLista()).catch((e) =>
    app.replaceChildren(h("p", { className: "text-red-700", role: "alert" }, `Erro ao carregar: ${e.message}`)));
}
window.addEventListener("hashchange", rotear);
rotear();
