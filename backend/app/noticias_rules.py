"""Regras puras de notícias: catálogo, elegibilidade, URLs e saída do provedor."""
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .clock import formatar_utc

CATALOGO = {
    'formula-1': {'nome': 'Fórmula 1', 'q': '"Fórmula 1" OR "Formula 1" OR F1'},
    'palmeiras': {'nome': 'Palmeiras', 'q': 'Palmeiras AND futebol'},
    'corinthians': {'nome': 'Corinthians', 'q': 'Corinthians AND futebol'},
}


class ErroNoticias(Exception):
    def __init__(self, mensagem, campo='noticias', status=400, codigo='noticias_invalidas'):
        self.mensagem, self.campo, self.status, self.codigo = mensagem, campo, status, codigo

    def resposta(self):
        return {'codigo': self.codigo, 'campo': self.campo, 'mensagem': self.mensagem, 'status': self.status}


def versao_consulta(assunto):
    parametros = {'q': CATALOGO[assunto]['q'], 'language': 'pt', 'sortBy': 'publishedAt',
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


def validar_artigos(dados, agora):
    def invalida():
        raise ErroNoticias('O provedor retornou notícias fora do formato esperado.', status=502, codigo='saida_noticias_invalida')
    if not isinstance(dados, dict) or dados.get('status') != 'ok' or not isinstance(dados.get('articles'), list) or len(dados['articles']) > 10:
        invalida()
    artigos = {}
    for a in dados['articles']:
        if not isinstance(a, dict):
            invalida()
        if a.get('title') == '[Removed]':
            continue
        titulo, fonte, descricao = a.get('title'), a.get('source'), a.get('description')
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 500:
            invalida()
        if not isinstance(fonte, dict) or not isinstance(fonte.get('name'), str) or not fonte['name'].strip() or len(fonte['name']) > 200:
            invalida()
        if descricao is not None and (not isinstance(descricao, str) or len(descricao) > 5000):
            invalida()
        try:
            publicada = datetime.fromisoformat(a['publishedAt'])
            if publicada.tzinfo is None or publicada > agora:
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            invalida()
        url = normalizar_url(a.get('url'))
        if publicada < agora - timedelta(days=7):
            continue
        artigos.setdefault(url, {'url': url, 'title': titulo.strip(), 'description': (descricao or '').strip()[:300],
                                 'source': fonte['name'].strip(), 'publishedAt': formatar_utc(publicada)})
    return list(artigos.values())
