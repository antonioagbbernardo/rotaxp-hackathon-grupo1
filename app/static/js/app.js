// Esqueleto: lista de clientes via API JSON. T02 expande (busca, filtro, detalhe).
const app = document.getElementById("app");

const cores = { alta: "bg-red-100 text-red-800", media: "bg-amber-100 text-amber-800", baixa: "bg-slate-100 text-slate-700" };

async function carregarClientes() {
  const resp = await fetch("/api/clientes");
  if (!resp.ok) {
    app.textContent = "Erro ao carregar clientes.";
    return;
  }
  const { clientes } = await resp.json();
  app.replaceChildren(
    ...clientes.map((c) => {
      const li = document.createElement("div");
      li.className = "flex justify-between items-center bg-white rounded p-3 mb-2 shadow-sm";
      const nome = document.createElement("span");
      nome.textContent = c.nome;
      const tag = document.createElement("span");
      tag.className = `text-xs px-2 py-1 rounded ${cores[c.prioridade]}`;
      tag.textContent = `${c.prioridade} · ${c.alertas_pendentes} pendência(s)`;
      li.append(nome, tag);
      return li;
    })
  );
}

carregarClientes();
