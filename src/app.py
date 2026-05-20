from flask import Flask

from config import Config
from controllers.deck_controller import deck_bp
from extensions import db


def create_app(config_object: type[Config] | None = None, **config_overrides: object) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    app.config.update(config_overrides)

    db.init_app(app)
    app.register_blueprint(deck_bp)

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.cli.command("init-db")
    def init_db() -> None:
        with app.app_context():
            db.create_all()
        print("Database tables created.")

    return app


app = create_app()
