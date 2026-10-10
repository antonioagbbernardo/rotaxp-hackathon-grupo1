from pathlib import Path

from flask import Flask, render_template, request

from .clock import Clock


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.update(
        DATABASE=str(Path(app.instance_path) / "app.db"),
        CLOCK=Clock(),  # relógio único e injetável (America/Sao_Paulo)
    )
    if config:
        app.config.update(config)

    from . import api, db, seed

    db.init_app(app)
    seed.init_app(app)
    with app.app_context():
        db.init_db()  # CREATE IF NOT EXISTS: a API não falha em base nova
    app.register_blueprint(api.bp)

    @app.errorhandler(404)
    @app.errorhandler(405)
    def erro_de_roteamento(erro):
        if request.path != "/api" and not request.path.startswith("/api/"):
            return erro
        codigo, mensagem = (
            ("nao_encontrado", "Rota inexistente.") if erro.code == 404 else
            ("metodo_nao_permitido", "Método não permitido para esta rota."))
        resposta = erro.get_response()  # conserva os cabeçalhos HTTP, inclusive Allow
        resposta.data = app.json.dumps({"erro": {"codigo": codigo, "campo": None, "mensagem": mensagem}})
        resposta.content_type = "application/json"
        return resposta

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
