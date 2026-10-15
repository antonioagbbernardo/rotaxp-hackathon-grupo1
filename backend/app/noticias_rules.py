"""Regras puras de notícias: catálogo, elegibilidade, URLs e saída do provedor."""
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .clock import formatar_utc

CATALOGO = {
    'mercado': {'nome': 'Mercado financeiro · notícias gerais', 'q': '"mercado financeiro" OR "taxa Selic" OR "economia brasileira"'},
    'formula-1': {'nome': 'Fórmula 1', 'q': '"Fórmula 1" OR "Formula 1" OR F1'},
    'palmeiras': {'nome': 'Palmeiras', 'q': 'Palmeiras AND futebol'},
    'corinthians': {'nome': 'Corinthians', 'q': 'Corinthians AND futebol'},
    'futebol': {'nome': 'Futebol', 'q': 'futebol AND (brasileiro OR campeonato OR seleção)'},
    'cafe': {'nome': 'Café', 'q': '"café especial" OR "cultura do café" OR cafeterias'},
}


def assuntos_do_interesse(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if unicodedata.category(c) != 'Mn')
    if re.search(r'\b(?:nao (?:gosta|acompanha|tem interesse|se interessa|quer noticias)|deixou de|parou de)\b', texto):
        return []
    padroes = {'formula-1': r'\b(?:formula\s*1|f1)\b', 'palmeiras': r'\bpalmeiras\b', 'corinthians': r'\bcorinthians\b',
               'futebol': r'\bfutebol\b', 'cafe': r'\b(?:cafe|cafes|cafeterias?)\b'}
    return [assunto for assunto, padrao in padroes.items() if re.search(padrao, texto)]


class ErroNoticias(Exception):
    def __init__(self, mensagem, campo='noticias', status=400, codigo='noticias_invalidas'):
        self.mensagem, self.campo, self.status, self.codigo = mensagem, campo, status, codigo

    def resposta(self):
        return {'codigo': self.codigo, 'campo': self.campo, 'mensagem': self.mensagem, 'status': self.status}


def versao_consulta(assunto, catalogo=None):
    parametros = {'q': (catalogo or CATALOGO)[assunto]['q'], 'language': 'pt', 'sortBy': 'publishedAt',
                  'searchIn': 'title,description', 'dias': 7, 'pageSize': 10, 'page': 1, 'versao': 1}
    return hashlib.sha256(json.dumps(parametros, sort_keys=True).encode()).hexdigest()


def interesse_elegivel(item):
    return (item['categoria'] == 'interesse' and item['tipo'] == 'fato'
            and item['estado'] in ('confirmado', 'corrigido') and item['sujeito'] == 'cliente'
            and item['evidencia_atual'] and not item['conflitos'] and not item['bloqueado']
            and item['elegivel_contato'])


def normalizar_url(valor):
    try:
        if not isinstance(valor, str) or not 1 <= len(valor) <= 3000 or any(c.isspace() or ord(c) < 32 for c in valor):
            raise ValueError()
        p = urlsplit(valor)
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
            raise ValueError()
        porta = p.port  # valida a porta antes de aceitar o link
        host = p.hostname.lower()
        if ':' in host:
            host = f'[{host}]'
        if porta and not (p.scheme == 'https' and porta == 443 or p.scheme == 'http' and porta == 80):
            host += f':{porta}'
        query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                 if not k.casefold().startswith('utm_') and k.casefold() not in ('gclid', 'fbclid', 'msclkid')]
        return urlunsplit((p.scheme, host, p.path or '/', urlencode(sorted(query)), ''))
    except (ValueError, TypeError):
        raise ErroNoticias('O provedor retornou um link inválido.', status=502, codigo='saida_noticias_invalida') from None


class ArtigosValidados(list):
    rejeitados = 0


def _validar_artigo(a, agora):
    if not isinstance(a, dict):
        raise ValueError()
    if a.get('title') in (None, '[Removed]'):
        return None
    titulo, fonte, descricao = a.get('title'), a.get('source'), a.get('description')
    if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 500:
        raise ValueError()
    if not isinstance(fonte, dict) or not isinstance(fonte.get('name'), str) or not fonte['name'].strip() or len(fonte['name']) > 200:
        raise ValueError()
    if descricao is not None and (not isinstance(descricao, str) or len(descricao) > 5000):
        raise ValueError()
    publicada = datetime.fromisoformat(a['publishedAt'])
    if publicada.tzinfo is None or publicada > agora:
        raise ValueError()
    url = normalizar_url(a.get('url'))
    if publicada < agora - timedelta(days=7):
        return None
    return {'url':url,'title':titulo.strip(),'description':(descricao or '').strip()[:300],
            'source':fonte['name'].strip(),'publishedAt':formatar_utc(publicada)}


def validar_artigos(dados, agora):
    def invalida():
        raise ErroNoticias('O provedor retornou notícias fora do formato esperado.', status=502, codigo='saida_noticias_invalida')
    if not isinstance(dados, dict) or dados.get('status') != 'ok' or not isinstance(dados.get('articles'), list) or len(dados['articles']) > 10:
        invalida()
    artigos, rejeitados = {}, 0
    for a in dados['articles']:
        try:
            artigo = _validar_artigo(a, agora)
        except (ValueError, TypeError, KeyError, ErroNoticias):
            rejeitados += 1
            continue
        if artigo:
            artigos.setdefault(artigo['url'], artigo)
    if rejeitados and not artigos:
        invalida()  # Preservar o cache quando o lote inteiro é inutilizável.
    resultado = ArtigosValidados(artigos.values())
    resultado.rejeitados = rejeitados
    return resultado
