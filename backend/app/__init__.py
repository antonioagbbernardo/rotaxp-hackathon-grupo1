from pathlib import Path
import os

from dotenv import dotenv_values
from flask import Flask, render_template

from .clock import Clock


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.update(
        DATABASE=str(Path(app.instance_path) / "app.db"),
        CLOCK=Clock(),  # relógio único e injetável (America/Sao_Paulo)
    )
    locais = dotenv_values(Path(app.root_path).parent / ".env")
    app.config.update(
        GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY", locais.get("GEMINI_API_KEY", "")),
        GEMINI_MODEL=os.environ.get("GEMINI_MODEL", locais.get("GEMINI_MODEL", "gemini-3.5-flash-lite")),
    )
    if config:
        app.config.update(config)

    from . import api, db, fontes, seed

    db.init_app(app)
    seed.init_app(app)
    fontes.init_app(app)
    with app.app_context():
        db.init_db()  # CREATE IF NOT EXISTS: a API não falha em base nova
    app.register_blueprint(api.bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
