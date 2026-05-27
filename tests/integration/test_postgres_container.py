import os
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from testcontainers.postgres import PostgresContainer
from tests.factories import DeckFactory, FlashcardFactory

from app import create_app
from extensions import db

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_TESTCONTAINERS") != "true",
        reason="Docker gerektirdigi icin varsayilan test kosusunda kapali.",
    ),
]


@pytest.fixture(scope="module")
def postgres_database_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine") as postgres:
        database_url = postgres.get_connection_url().replace(
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            1,
        )
        yield database_url.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.fixture()
def postgres_app(postgres_database_url: str) -> Iterator[Flask]:
    app = create_app(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=postgres_database_url,
        JWT_SECRET="test-jwt-secret-that-is-at-least-32-bytes",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def postgres_client(postgres_app: Flask) -> FlaskClient:
    return postgres_app.test_client()


def _auth_headers(client: FlaskClient) -> dict[str, str]:
    client.post("/api/auth/register", json={"username": "tc-user", "password": "test"})
    response = client.post("/api/auth/login", json={"username": "tc-user", "password": "test"})
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_deck_with_real_postgresql_container(postgres_client: FlaskClient) -> None:
    headers = _auth_headers(postgres_client)
    deck_payload = DeckFactory.payload(name="PostgreSQL Container", description="Gercek DB testi")

    response = postgres_client.post("/api/decks", json=deck_payload, headers=headers)

    assert response.status_code == 201
    assert response.get_json()["data"]["name"] == deck_payload["name"]
    assert response.get_json()["data"]["description"] == deck_payload["description"]


def test_create_flashcard_with_real_postgresql_container(postgres_client: FlaskClient) -> None:
    headers = _auth_headers(postgres_client)
    deck_response = postgres_client.post(
        "/api/decks",
        json=DeckFactory.payload(name="Kart Deck", description=None),
        headers=headers,
    )
    deck_id = deck_response.get_json()["data"]["id"]
    flashcard_payload = FlashcardFactory.payload(
        front="PostgreSQL nedir?",
        back="Iliskisel veritabani",
    )

    response = postgres_client.post(
        f"/api/decks/{deck_id}/flashcards",
        json=flashcard_payload,
        headers=headers,
    )
    deck_detail = postgres_client.get(f"/api/decks/{deck_id}", headers=headers)

    assert response.status_code == 201
    assert response.get_json()["data"]["front"] == flashcard_payload["front"]
    assert deck_detail.get_json()["data"]["flashcard_count"] == 1


def test_review_and_delete_flashcard_with_real_postgresql_container(
    postgres_client: FlaskClient,
) -> None:
    headers = _auth_headers(postgres_client)
    deck_response = postgres_client.post(
        "/api/decks",
        json=DeckFactory.payload(name="Review Deck", description="Silme ve review testi"),
        headers=headers,
    )
    deck_id = deck_response.get_json()["data"]["id"]
    flashcard_response = postgres_client.post(
        f"/api/decks/{deck_id}/flashcards",
        json=FlashcardFactory.payload(front="SM-2", back="Aralikli tekrar"),
        headers=headers,
    )
    flashcard_id = flashcard_response.get_json()["data"]["id"]

    review_response = postgres_client.patch(
        f"/api/flashcards/{flashcard_id}/review",
        json={"difficulty": "good"},
        headers=headers,
    )
    delete_response = postgres_client.delete(
        f"/api/flashcards/{flashcard_id}",
        headers=headers,
    )
    deck_detail = postgres_client.get(f"/api/decks/{deck_id}", headers=headers)

    assert review_response.status_code == 200
    assert review_response.get_json()["data"]["review_count"] == 1
    assert review_response.get_json()["data"]["difficulty"] == "good"
    assert delete_response.status_code == 200
    assert deck_detail.get_json()["data"]["flashcard_count"] == 0
