from pathlib import Path
import os

from dotenv import dotenv_values
from flask import Flask, render_template, send_from_directory

from .clock import Clock


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.update(
        DATABASE=str(Path(app.instance_path) / "app.db"),
        CLOCK=Clock(),  # relógio único e injetável (America/Sao_Paulo)
        FRONTEND_DIST=str(Path(app.root_path).parents[1] / "frontend" / "dist"),
    )
    locais = dotenv_values(Path(app.root_path).parent / ".env")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", locais.get("SECRET_KEY", "")),
        GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY", locais.get("GEMINI_API_KEY", "")),
        GEMINI_MODEL=os.environ.get("GEMINI_MODEL", locais.get("GEMINI_MODEL", "gemini-3.5-flash-lite")),
        OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", locais.get("OPENAI_API_KEY", "")),
        OPENAI_MODEL=os.environ.get("OPENAI_MODEL", locais.get("OPENAI_MODEL", "gpt-4.1-mini")),
        NEWSAPI_API_KEY=(os.environ.get("NEWSAPI_API_KEY") or os.environ.get("NEWSAPI_KEY")
            or locais.get("NEWSAPI_API_KEY") or locais.get("NEWSAPI_KEY") or ""),
        NEWSAPI_LIMITE_DIARIO=os.environ.get("NEWSAPI_LIMITE_DIARIO", locais.get("NEWSAPI_LIMITE_DIARIO", "20")),
        GOOGLE_CALENDAR_CLIENT_ID=os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", locais.get("GOOGLE_CALENDAR_CLIENT_ID", "")),
        GOOGLE_CALENDAR_CLIENT_SECRET=os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", locais.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")),
        GOOGLE_CALENDAR_REDIRECT_URI=os.environ.get("GOOGLE_CALENDAR_REDIRECT_URI", locais.get("GOOGLE_CALENDAR_REDIRECT_URI", "")),
    )
    if config:
        app.config.update(config)

    from . import agendador, api, autenticacao, db, fontes, noticias, seed

    db.init_app(app)
    seed.init_app(app)
    fontes.init_app(app)
    noticias.init_app(app)
    agendador.init_app(app)
    with app.app_context():
        db.init_db()  # CREATE IF NOT EXISTS: a API não falha em base nova
    app.register_blueprint(api.bp)
    autenticacao.init_app(app)

    @app.get("/login")
    def login_frontend():
        dist = Path(app.config["FRONTEND_DIST"])
        if (dist / "index.html").is_file():
            return send_from_directory(dist, "index.html")
        return "Compile o frontend com npm run build para acessar o XP Pulse.", 503

    @app.get("/")
    def index():
        dist = Path(app.config["FRONTEND_DIST"])
        if (dist / "index.html").is_file():
            return send_from_directory(dist, "index.html")
        return render_template("index.html")

    @app.get("/assets/<path:nome>")
    def assets_frontend(nome):
        return send_from_directory(Path(app.config["FRONTEND_DIST"]) / "assets", nome)

    @app.get("/favicon.svg")
    def favicon_frontend():
        return send_from_directory(Path(app.config["FRONTEND_DIST"]), "favicon.svg")

    @app.get("/legacy")
    def interface_anterior():
        return render_template("index.html")

    return app
