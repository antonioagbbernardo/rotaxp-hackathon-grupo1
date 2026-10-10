"""Preparação dos testes de domínio: login HTTP real e token de escrita."""


def cliente_autenticado(app):
    client = app.test_client()
    renovar_acesso(client)
    return client


def renovar_acesso(client):
    """Entrar novamente após avanço de dias do Clock ou reset da base fictícia."""
    sessao = client.get("/api/auth/sessao")
    assert sessao.status_code == 200
    login = client.post("/api/auth/login", json={"usuario": "admin", "senha": "admin"},
                        headers={"X-CSRF-Token": sessao.get_json()["csrf_token"]})
    assert login.status_code == 200
    client.environ_base["HTTP_X_CSRF_TOKEN"] = login.get_json()["csrf_token"]
