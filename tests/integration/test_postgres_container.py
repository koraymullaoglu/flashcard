import os

import pytest
from testcontainers.postgres import PostgresContainer

from app import create_app
from extensions import db


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_TESTCONTAINERS") != "true",
    reason="Docker gerektirdigi icin varsayilan test kosusunda kapali.",
)
def test_create_deck_with_real_postgresql_container() -> None:
    with PostgresContainer("postgres:16-alpine") as postgres:
        database_url = postgres.get_connection_url().replace(
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            1,
        )
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        app = create_app(TESTING=True, SQLALCHEMY_DATABASE_URI=database_url)

        with app.app_context():
            db.create_all()
            client = app.test_client()

            response = client.post("/api/decks", json={"name": "PostgreSQL Container"})

            assert response.status_code == 201

            db.session.remove()
            db.drop_all()
            db.engine.dispose()
