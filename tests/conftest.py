import os
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from extensions import db


@pytest.fixture()
def app() -> Iterator[Flask]:
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    app = create_app(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=database_url,
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
