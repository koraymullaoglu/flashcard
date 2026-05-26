from time import sleep

from flask import Flask
from prometheus_client import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy.exc import OperationalError

from config import Config
from controllers.auth_controller import auth_bp
from controllers.deck_controller import deck_bp
from controllers.view_controller import view_bp
from extensions import db

INIT_DB_MAX_ATTEMPTS = 5
INIT_DB_RETRY_DELAY_SECONDS = 3


def create_app(config_object: type[Config] | None = None, **config_overrides: object) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    app.config.update(config_overrides)

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(deck_bp)
    app.register_blueprint(view_bp)

    PrometheusMetrics(app, registry=CollectorRegistry(auto_describe=True))

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.cli.command("init-db")
    def init_db() -> None:
        for attempt in range(1, INIT_DB_MAX_ATTEMPTS + 1):
            try:
                with app.app_context():
                    db.create_all()
                break
            except OperationalError:
                if attempt == INIT_DB_MAX_ATTEMPTS:
                    raise
                print(
                    "Database is not ready yet; "
                    f"retrying in {INIT_DB_RETRY_DELAY_SECONDS}s "
                    f"({attempt}/{INIT_DB_MAX_ATTEMPTS}).",
                    flush=True
                )
                sleep(INIT_DB_RETRY_DELAY_SECONDS)
        print("Database tables created.", flush=True)

    return app


app = create_app()
