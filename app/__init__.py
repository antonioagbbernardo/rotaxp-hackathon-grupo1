from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, render_template

TZ = ZoneInfo("America/Sao_Paulo")


def hoje_sp() -> date:
    return datetime.now(TZ).date()


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    app.config.update(
        DATABASE=str(Path(app.instance_path) / "app.db"),
        HOJE=hoje_sp,  # relógio injetável: callable que devolve a data de hoje
    )
    if config:
        app.config.update(config)

    from . import api, db, seed

    db.init_app(app)
    seed.init_app(app)
    app.register_blueprint(api.bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    return app
