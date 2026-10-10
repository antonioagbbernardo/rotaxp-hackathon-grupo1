"""Seleção de fatos e validação da síntese; sem I/O ou alteração da base."""
import hashlib
import json
import re

PROMPT_VERSAO = 'resumo-v2'


class ErroResumoIA(Exception):
    def __init__(self, mensagem, status=502, codigo='resumo_ia_invalido'):
        self.mensagem, self.status, self.codigo, self.campo = mensagem, status, codigo, 'resumo_ia'


def referencia(fonte):
    ids = fonte['id_fonte']
    if isinstance(ids, list):
        ids = ', '.join(map(str, ids))
    data = fonte.get('data_referencia')
    return f"{fonte['tipo_fonte']} #{ids}" + (f' · {data}' if data else '')


def apresentar_fato(texto):
    return re.sub(r'(\d+) dia\(s\)', lambda m: m[1] + (' dia' if m[1] == '1' else ' dias'), texto)


def montar_entrada(cliente, hoje):
    fatos = [{'id': f'fato-{n}', 'texto': apresentar_fato(f['texto']), 'fonte': referencia(f['fonte'])}
             for n, f in enumerate(cliente['summaryFacts'])
             if f['fonte']['tipo_fonte'] != 'avaliacao_relacionamento']
    ausencias = cliente['assistant']['summaryItems'][len(cliente['summaryFacts']):]
    fatos += [{'id': f'ausencia-{n}', 'texto': t, 'fonte': f"cliente #{cliente['id']} · ausência na base"}
              for n, t in enumerate(ausencias) if t != 'Não avaliado']
    alertas = [a for a in cliente['alerts'] if a['estado'] == 'pendente']
    fatos += [{'id': f'pendencia-{n}', 'texto': a['motivo'], 'prioridade': a['prioridade'],
               'fonte': referencia(a['fonte'])} for n, a in enumerate(alertas)]
    p = cliente['preferences']
    fatos.append({'id': 'preferencias', 'texto':
                  f"Canal preferido: {p['canal_preferido'] or 'não informado'}. "
                  f"Intervalo mínimo: {p['intervalo_minimo_dias']} dias. "
                  f"Assuntos pessoais: {'permitidos' if p['permite_assuntos_pessoais'] else 'não permitidos'}.",
                  'fonte': f"cliente #{cliente['id']} · preferências cadastradas"})
    for nota in cliente.get('advisorNotes', []):
        fatos.append({'id': f"nota-{nota['id']}", 'texto': nota['texto'],
                      'fonte': f"informação declarada pelo assessor · nota #{nota['id']} · {nota['registrada_em']}"})
    for item in cliente['context']['itens']:
        if (item['estado'] not in ('confirmado', 'corrigido') or item['tipo'] != 'fato' or item['sujeito'] != 'cliente'
                or not item['evidencia_atual'] or item['conflitos'] or item['bloqueado']
                or not item.get('elegivel_contato')):
            continue
        fatos.append({'id': f"contexto-{item['id']}", 'texto': item['valor_revisado'] or item['valor_original'],
                      'fonte': '; '.join(f"documento #{e['documento_id']} · {e['origem']} · {e['registro_id']} v{e['versao']}"
                                         for e in item['evidencias'])})
    return {'cliente': cliente['name'], 'cliente_id': cliente['id'], 'data_local': hoje.isoformat(),
            'prioridade_calculada': cliente['priority'],
            'fatos': fatos}


def assinatura(entrada, modelo):
    texto = json.dumps({'entrada': entrada, 'modelo': modelo, 'prompt': PROMPT_VERSAO}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()


def validar_saida(saida, entrada):
    def erro():
        raise ErroResumoIA('A síntese retornou formato ou fontes inválidos. Tente novamente.')
    if not isinstance(saida, dict) or set(saida) != {'visao_geral', 'pontos_atencao', 'antes_contato'}:
        erro()
    fontes = {f['id']: f['fonte'] for f in entrada['fatos']}
    def trecho(item, limite):
        if not isinstance(item, dict) or set(item) != {'texto', 'fontes'}:
            erro()
        texto, ids = item['texto'], item['fontes']
        if not isinstance(texto, str) or not texto.strip() or len(texto) > limite:
            erro()
        if not isinstance(ids, list) or not 1 <= len(ids) <= 5 or any(not isinstance(i, str) or i not in fontes for i in ids):
            erro()
        return {'texto': texto.strip(), 'fontes': list(dict.fromkeys(fontes[i] for i in ids))}
    resultado = {'visao_geral': trecho(saida['visao_geral'], 450)}
    for secao in ('pontos_atencao', 'antes_contato'):
        itens = saida[secao]
        if not isinstance(itens, list) or len(itens) > 3:
            erro()
        resultado[secao] = [trecho(i, 300) for i in itens]
    return resultado


TRECHO_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['texto', 'fontes'],
    'properties': {'texto': {'type': 'string'}, 'fontes': {'type': 'array', 'items': {'type': 'string'}}},
}
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['visao_geral', 'pontos_atencao', 'antes_contato'],
    'properties': {'visao_geral': TRECHO_SCHEMA, 'pontos_atencao': {'type': 'array', 'items': TRECHO_SCHEMA},
                   'antes_contato': {'type': 'array', 'items': TRECHO_SCHEMA}},
}
