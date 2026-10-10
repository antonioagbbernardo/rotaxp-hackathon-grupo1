import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from app.contexto_rules import ErroContexto
from app.ia_gemini import GeminiExtractor


def envelope(itens=None, fim="STOP"):
    return json.dumps({"candidates": [{"finishReason": fim, "content": {"parts": [
        {"text": "raciocínio privado", "thought": True},
        {"text": json.dumps({"itens": itens or []})}]}}]}).encode()


def test_ca54_rest_usa_header_schema_timeout_sem_ferramentas():
    def transporte(req, timeout):
        assert timeout == 30 and req.get_header("X-goog-api-key") == "chave-ficticia"
        assert "chave-ficticia" not in req.full_url
        corpo = json.loads(req.data)
        formato = corpo["generationConfig"]["responseFormat"]["text"]
        assert formato["mimeType"] == "APPLICATION_JSON"
        assert not {"responseMimeType", "responseJsonSchema"}.intersection(corpo["generationConfig"])
        assert "tools" not in corpo
        schema = formato["schema"]
        def conferir(valor):
            if isinstance(valor, dict):
                assert not {"pattern", "minLength", "maxLength", "minItems", "maxItems"}.intersection(valor)
                for filho in valor.values():
                    conferir(filho)
            elif isinstance(valor, list):
                for filho in valor:
                    conferir(filho)
        conferir(schema)
        return BytesIO(envelope())
    e = GeminiExtractor("chave-ficticia", transporte=transporte)
    assert e.extrair([]) == {"itens": []}


@pytest.mark.parametrize("falha,status", [(TimeoutError("segredo"), 503), (URLError("segredo"), 503),
    (HTTPError("https://x", 429, "segredo", {}, None), 503),
    (HTTPError("https://x", 403, "segredo", {}, None), 503)])
def test_ca54_falha_http_sem_expor_resposta_bruta(falha, status):
    def transporte(*a, **k):
        raise falha
    with pytest.raises(ErroContexto) as info:
        GeminiExtractor("segredo", transporte=transporte).extrair([])
    assert info.value.status == status and "segredo" not in info.value.mensagem


@pytest.mark.parametrize("bruto", [b"nao json", b"{}", envelope(fim="MAX_TOKENS"),
                                   b"x" * 1_000_001])
def test_ca50_resposta_invalida_truncada_ou_grande(bruto):
    with pytest.raises(ErroContexto) as info:
        GeminiExtractor("chave-ficticia", transporte=lambda *a, **k: BytesIO(bruto)).extrair([])
    assert info.value.status == 502


def test_ca54_chave_ausente_nem_chama_transporte():
    def nao_chamar(*a, **k):
        pytest.fail("Provedor não deve ser chamado sem chave")
    with pytest.raises(ErroContexto) as info:
        GeminiExtractor("", transporte=nao_chamar).extrair([])
    assert info.value.status == 503
