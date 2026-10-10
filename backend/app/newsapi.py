"""NewsAPI REST: consulta fixa, sem dados do cliente ou captura do artigo completo."""
import json
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .noticias_rules import ErroNoticias


class SemRedirecionamento(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # não repassar X-Api-Key para outro destino


abrir = build_opener(SemRedirecionamento()).open


def erro_provedor(status, codigo=None):
    if codigo == 'apiKeyExhausted':
        return ErroNoticias('Cota do NewsAPI esgotada. A coleta foi suspensa pelo dia local.', status=503, codigo='cota_externa')
    if status == 429 or codigo == 'rateLimited':
        return ErroNoticias('NewsAPI limitou as consultas. Aguarde 30 minutos.', status=503, codigo='limite_provedor')
    if status in (401, 403) or codigo in ('apiKeyInvalid', 'apiKeyMissing', 'apiKeyDisabled'):
        return ErroNoticias('NewsAPI recusou a credencial. Confira a configuração no backend.', status=503, codigo='credencial_recusada')
    return ErroNoticias('NewsAPI indisponível. O último resultado foi preservado.', status=503, codigo='provedor_indisponivel')


class NewsAPI:
    def __init__(self, chave):
        self.chave = chave

    def buscar(self, consulta, agora):
        if not self.chave:
            raise ErroNoticias('Configure NEWSAPI_API_KEY no backend e reinicie o servidor.', status=503, codigo='noticias_nao_configuradas')
        parametros = {'q': consulta['q'], 'language': 'pt', 'sortBy': 'publishedAt', 'searchIn': 'title,description',
                      'from': (agora - timedelta(days=7)).isoformat(), 'to': agora.isoformat(), 'pageSize': 10, 'page': 1}
        req = Request('https://newsapi.org/v2/everything?' + urlencode(parametros),
                      headers={'X-Api-Key': self.chave, 'User-Agent': 'XPPulse-MVP/1.0'})
        try:
            with abrir(req, timeout=15) as resposta:
                bruto = resposta.read(1000001)
        except HTTPError as e:
            codigo = None
            try:
                dados = json.loads(e.read(10000))
                if isinstance(dados, dict):
                    codigo = dados.get('code')
            except (ValueError, OSError):
                pass
            raise erro_provedor(e.code, codigo) from None
        except (URLError, TimeoutError, OSError):
            raise erro_provedor(503) from None
        try:
            if len(bruto) > 1000000:
                raise ValueError()
            dados = json.loads(bruto)
            if not isinstance(dados, dict):
                raise ValueError()
        except (ValueError, TypeError):
            raise ErroNoticias('Resposta do NewsAPI inválida ou grande demais.', status=502, codigo='saida_noticias_invalida') from None
        if dados.get('status') == 'error':
            raise erro_provedor(503, dados.get('code'))
        return dados
