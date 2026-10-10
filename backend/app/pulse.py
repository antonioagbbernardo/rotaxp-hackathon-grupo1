"""Adaptador do painel React; consulta registros sem chamar IA ou enviar contato."""
from decimal import Decimal
import re
import unicodedata

from flask import current_app

from . import contexto
from .clock import TZ, formatar_utc, parse_instante
from .db import get_db
from .fontes import consultar_fontes
from .resumo import montar_resumo
from . import resumo_ia
from . import noticias
from .resumo_ia_rules import apresentar_fato


def referencia(fonte):
    ids = fonte["id_fonte"]
    if isinstance(ids, list):
        ids = ", ".join(map(str, ids))
    return f"{fonte['tipo_fonte']} #{ids}" + (f" · {fonte['data_referencia']}" if fonte.get("data_referencia") else "")


def montar_carteira(posicoes, perfil, itens, fontes):
    valores = {}
    for p in posicoes:
        ativo = ''.join(ch for ch in unicodedata.normalize('NFD', p['ativo'].casefold()) if unicodedata.category(ch) != 'Mn')
        classe = ('fixedIncome' if re.search(r'\b(cdb|lci|lca|cra|cri|tesouro|debenture|renda fixa)\b', ativo)
                  else 'funds' if re.search(r'\b(fundo|fundos|fii|etf)\b', ativo)
                  else 'stocks' if re.search(r'\b(acao|acoes)\b', ativo) else 'other')
        valores[classe] = valores.get(classe, Decimal('0')) + Decimal(p['valor'])
    total = sum(valores.values(), Decimal('0'))
    alocacao = []
    if total > 0:
        percentuais = {k: v * 100 / total for k, v in valores.items() if v > 0}
        inteiros = {k: int(v) for k, v in percentuais.items()}
        for k in sorted(percentuais, key=lambda k: percentuais[k] - inteiros[k], reverse=True)[:100 - sum(inteiros.values())]:
            inteiros[k] += 1
        alocacao = [{'asset': k, 'percent': v} for k, v in inteiros.items()]
    objetivos = [i for i in itens if i['categoria'] == 'objetivo' and i['tipo'] == 'fato'
                 and i['sujeito'] == 'cliente' and i['estado'] in ('confirmado', 'corrigido', 'pendente')
                 and i['evidencia_atual'] and not i['conflitos'] and not i['bloqueado']]
    objetivos.sort(key=lambda i: (i['estado'] != 'pendente', i['gerado_em']), reverse=True)
    objetivo = next((i['valor_revisado'] or i['valor_original'] for i in objetivos), None)
    if not objetivo:
        objetivo = next((f['conteudo']['objetivo'] for f in fontes if f['atual'] and f['tipo'] == 'formulario'
                         and isinstance(f['conteudo'], dict) and isinstance(f['conteudo'].get('objetivo'), str)
                         and f['conteudo']['objetivo'].strip()), None)
    if not objetivo and 'objetivo:' in (perfil or '').casefold():
        objetivo = re.split(r'objetivo:', perfil, flags=re.IGNORECASE)[1].strip()
    objetivo = re.sub(r'^Dados fictícios:\s*', '', objetivo or 'Não informado', flags=re.IGNORECASE)
    return {'total': format(total, '.2f') if posicoes else None, 'goal': objetivo,
            'profile': (perfil or '').split(';')[0].strip() or 'Não informado', 'allocation': alocacao}


def montar_cliente(c, incluir_resumo_ia=True):
    # Mesma leitura/regras das rotas existentes, sem outra lógica de prioridade.
    from .api import _contexto, _preferencias, _relacionamento
    from .chat import notas
    from .humor import consultar as consultar_humor
    db, clock = get_db(), current_app.config["CLOCK"]
    ctx = _contexto(db, c, clock.hoje())
    rel = _relacionamento(ctx["avaliacoes"])
    humor = consultar_humor(c['id'])
    resumo = montar_resumo(dict(c), ctx["posicoes"], ctx["ultima"],
                          ctx["avaliacoes"][0] if ctx["avaliacoes"] else None, clock.hoje(), ctx["ultima_data"])
    revisao = contexto.consultar(c["id"])
    fontes_cliente = consultar_fontes(c["id"])
    formulario = next((f['conteudo'] for f in fontes_cliente if f['atual'] and f['tipo'] == 'formulario' and f['origem'] == 'demo-pulse-v2'), {})
    novidades = noticias.consultar(c['id'], revisao['itens'])
    confirmados = [i for i in revisao["itens"] if i["estado"] in ("confirmado", "corrigido")
                   and i["sujeito"] == "cliente" and i["evidencia_atual"] and not i["conflitos"]]
    pendentes = [i for i in revisao["itens"] if i["estado"] == "pendente" and i["evidencia_atual"]]
    valor = lambda i: i["valor_revisado"] or i["valor_original"]
    fontes_resumo = [referencia(f["fonte"]) for f in resumo["fatos"]]
    alertas = [a for a in ctx["alertas"] if a["estado"] == "pendente"]
    financeiros = [a for a in alertas if a["regra"] == "vencimento"]
    fontes_abertura = [referencia(a["fonte"]) for a in financeiros[:1]]
    primeiro_nome = c["nome"].split()[0]
    if financeiros:
        assunto = financeiros[0]["motivo"]
        aberturas = [
            {"tone": "Próximo", "text": f"Olá, {primeiro_nome}! Gostaria de conversar sobre um vencimento da carteira: {assunto} Podemos revisar os próximos passos?"},
            {"tone": "Formal", "text": f"Olá, {primeiro_nome}. Identifiquei um vencimento para acompanharmos: {assunto} Qual seria um bom horário para conversarmos?"},
        ]
    else:
        aberturas = [{"tone": "Neutro", "text": f"Olá, {primeiro_nome}! Podemos combinar um momento para revisar seus objetivos e os próximos passos?"}]
        fontes_abertura = [f"cliente #{c['id']} · rascunho genérico, sem informação pessoal"]
    insights = [{"kind": "concern" if a["prioridade"] == "alta" else "opportunity",
                 "title": a["rotulo"], "body": a["motivo"] + " · " + referencia(a["fonte"])} for a in alertas]
    if pendentes:
        insights.append({"kind": "concern", "title": f"{len(pendentes)} proposta(s) para revisar",
                         "body": "Confira os trechos antes de usar o contexto no atendimento."})
    instantes = [r["registrada_em"] for r in ctx["interacoes"]] + [r["avaliada_em"] for r in ctx["avaliacoes"]]
    instantes += [i["gerado_em"] for i in revisao["itens"]]
    instantes += [r["revisada_em"] for i in revisao["itens"] for r in i["historico_revisoes"]]
    atualizado = max(instantes, default=None)
    linhas_resumo = [apresentar_fato(f['texto']) for f in resumo['fatos']] + resumo['ausencias']
    cliente = {
        "photoUrl": f"/assets/avatars/{c['id']}.jpg" if 1 <= c["id"] <= 10 else None,
        "id": str(c["id"]), "name": c["nome"], "pronoun": "este cliente",
        "status": "attention" if ctx["prioridade"] in ("alta", "media") else "stable",
        "priority": ctx["prioridade"], "nextDue": ctx["proxima_pendencia"],
        "relationshipLabel": rel["rotulo"] if rel else "Não avaliado",
        "interests": list(dict.fromkeys(valor(i) for i in confirmados if i["categoria"] == "interesse")),
        "tags": [{"label": c["perfil"]}] if c["perfil"] else [],
        "sentiment": humor['sentiment'], "mood": humor,
        "headline": f"{len(alertas)} pendência(s) · {len(pendentes)} proposta(s) para revisar",
        "updatedMinutesAgo": max(0, int((clock.agora() - parse_instante(atualizado)).total_seconds() // 60)) if atualizado else None,
        "clientSince": formulario.get("cliente_desde"), "lastContactDays": (clock.hoje() - ctx["ultima_data"]).days if ctx["ultima_data"] else None,
        "whatsapp": formulario.get("whatsapp", ""), "email": formulario.get("email", ""),
        "perception": [{"id": r["id"], "month": parse_instante(r["avaliada_em"]).astimezone(TZ).strftime("%Y-%m"),
                        "sentiment": {"positivo": "positive", "negativo": "negative", "atencao": "neutral"}[r["estado"]],
                        "label": {"positivo": "Positivo", "negativo": "Negativo", "atencao": "Atenção"}[r["estado"]],
                        "reason": r["justificativa"], "date": r["avaliada_em"]} for r in reversed(ctx["avaliacoes"])],
        "portfolio": montar_carteira(ctx['posicoes'], c['perfil'], revisao['itens'], fontes_cliente),
        "news": novidades['artigos'], "newsState": {k: v for k, v in novidades.items() if k != 'artigos'},
        "assistant": {"question": "O que preciso revisar antes do contato?",
          "summary": "\n".join(linhas_resumo), "summaryItems": linhas_resumo,
          "insights": insights, "openings": aberturas, "sources": fontes_abertura,
          "summarySources": fontes_resumo},
        "context": revisao, "sourceDocuments": fontes_cliente, "alerts": ctx["alertas"],
        "interactions": ctx["interacoes"], "preferences": _preferencias(c), "positions": ctx["posicoes"],
        "summaryFacts": resumo["fatos"], "relationshipHistory": ctx["avaliacoes"],
        "advisorNotes": notas(c['id']),
    }
    if incluir_resumo_ia:
        cliente['assistant']['aiSummary'] = resumo_ia.consultar(cliente)
    return cliente


def consultar_painel():
    from .api import _norm, PRIORIDADES
    db = get_db()
    clientes = [montar_cliente(c) for c in db.execute("SELECT * FROM cliente").fetchall()]
    clientes.sort(key=lambda c: (PRIORIDADES.index(c["priority"]), c["nextDue"] or "9999-12-31", _norm(c["name"])))
    assessor = db.execute("SELECT nome FROM assessor WHERE id=1").fetchone()
    return {"advisor": {"name": assessor["nome"] if assessor else "Assessor não cadastrado", "role": "Assessor de investimentos"},
            "generatedAt": formatar_utc(current_app.config["CLOCK"].agora()), "clients": clientes}


def responder(cliente, pergunta):
    texto = "".join(ch for ch in unicodedata.normalize("NFD", pergunta.casefold()) if unicodedata.category(ch) != "Mn")
    fontes = []
    if any(k in texto for k in ("noticia", "mercado hoje")):
        if cliente['news']:
            resposta = 'Notícias coletadas para revisão; não representam análise de mercado em tempo real.\n'
            resposta += '\n'.join(f"{a['title']} · {a['source']} · publicada {a['publishedAt']} · coletada {a['collectedAt']}" for a in cliente['news'])
            estados = cliente.get('newsState', {}).get('assuntos', [])
            if any(a['estado'] != 'atualizado' for a in estados):
                resposta += '\nA coleta está desatualizada ou indisponível; confira o estado na seção Notícias.'
            fontes = [f"{a['source']} · {a['url']} · {a['publishedAt']}" for a in cliente['news']]
        else:
            resposta = 'Não há notícias disponíveis para este cliente. Confira interesses e estado da coleta na seção Notícias.'
    elif any(k in texto for k in ('reuniao', 'agenda', 'keynote', 'pauta')):
        from .reunioes import listar
        reunioes = [r for r in listar(int(cliente['id']))['reunioes'] if r['estado'] == 'agendada']
        resposta = '\n'.join(f"{r['objetivo']} · {r['inicio_em']} · " + ('pauta revisada' if r['revisada'] else 'conferir/preparar pauta') for r in reunioes) or 'Nenhuma reunião agendada para este cliente.'
        fontes = [f"reuniao #{r['id']} · objetivo/horário registrados pelo assessor" for r in reunioes]
    elif any(k in texto for k in ('lembranc', 'aniversario', 'compromisso')):
        from .lembrancas import consultar
        lembrancas = [r for r in consultar(int(cliente['id']))['lembrancas'] if r['estado'] in ('pendente', 'adiado')]
        resposta = '\n'.join(f"{r['descricao']} · {r['sujeito']} · {r['ocorrencia']} · " + ('avaliar pertinência antes de abordar' if r['pode_contatar'] else 'aguardar intervalo de contato pessoal') for r in lembrancas) or 'Nenhuma lembrança confirmada elegível para este cliente.'
        fontes = [f for r in lembrancas for f in r['fontes']]
    elif any(k in texto for k in ("prefer", "canal", "intervalo")):
        p = cliente["preferences"]
        resposta = f"Canal preferido: {p['canal_preferido'] or 'não informado'}. Intervalo mínimo: {p['intervalo_minimo_dias']} dias. Assuntos pessoais: {'permitidos' if p['permite_assuntos_pessoais'] else 'não permitidos'}."
        fontes = [f"cliente #{cliente['id']} · preferências cadastradas"]
    elif any(k in texto for k in ("perfil", "risco")):
        resposta = "Perfil cadastrado: " + (" · ".join(t["label"] for t in cliente["tags"]) or "Não informado") + ". Esta consulta não calcula risco nem recomenda investimentos."
        fontes = [f"cliente #{cliente['id']}"] if cliente["tags"] else []
    elif any(k in texto for k in ("venc", "carteira", "posic", "investimento")):
        resposta = "\n".join(f"{p['ativo']} · R$ {p['valor']} · vencimento {p['vencimento']}" for p in cliente["positions"]) or "Nenhuma posição cadastrada."
        fontes = [f"posicao #{p['id']} · {p['fonte']}" for p in cliente["positions"]]
    elif any(k in texto for k in ("ultimo contato", "ultima conversa", "conversa", "historico")):
        ultimo = cliente["interactions"][0] if cliente["interactions"] else None
        resposta = f"Último contato: {ultimo['canal']} em {ultimo['ocorrida_em']}. {ultimo['texto']}" if ultimo else "Nenhuma interação registrada."
        fontes = [f"interacao #{ultimo['id']}"] if ultimo else []
    elif any(k in texto for k in ("telefone", "whatsapp", "email", "e-mail", "contato")):
        resposta = "Números de telefone e endereços de contato não estão disponíveis nesta base."
    elif any(k in texto for k in ("interess", "gosta", "contexto", "objetiv")):
        itens = [i for i in cliente["context"]["itens"] if i["estado"] in ("confirmado", "corrigido") and i["sujeito"] == "cliente"
                 and i["evidencia_atual"] and not i["conflitos"]]
        resposta = "\n".join((i["valor_revisado"] or i["valor_original"]) + (" · assunto bloqueado para contato" if i["bloqueado"] else "") for i in itens) or "Nenhum contexto confirmado disponível. Confira as propostas na fila de revisão."
        fontes = [f"documento #{e['documento_id']} · {e['origem']} · {e['registro_id']} v{e['versao']}" for i in itens for e in i["evidencias"]]
    elif any(k in texto for k in ("resumo", "revisar", "prepar", "atencao", "pendenc", "mudou")):
        resposta = cliente["assistant"]["summary"] + " " + cliente["headline"]
        fontes = cliente["assistant"]["summarySources"]
    else:
        resposta = "Esta consulta responde sobre perfil, carteira/vencimentos, último contato, preferências, interesses revisados, notícias, reuniões, lembranças e resumo. Não há informação suficiente para responder a essa pergunta com as fontes disponíveis."
    return {"resposta": resposta, "fontes": list(dict.fromkeys(fontes)), "modo": "consulta_contexto"}
