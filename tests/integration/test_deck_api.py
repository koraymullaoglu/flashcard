import pytest
from flask.testing import FlaskClient
from tests.factories import DeckFactory, FlashcardFactory

from extensions import db
from models import Deck


def _auth_headers(client: FlaskClient) -> dict[str, str]:
    client.post("/api/auth/register", json={"username": "test", "password": "test"})
    resp = client.post("/api/auth/login", json={"username": "test", "password": "test"})
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_create_and_get_deck_with_flashcard(client: FlaskClient) -> None:
    headers = _auth_headers(client)
    deck_payload = DeckFactory.build()
    create_response = client.post(
        "/api/decks",
        json={"name": deck_payload.name, "description": deck_payload.description},
        headers=headers,
    )
    deck_id = create_response.get_json()["data"]["id"]

    flashcard_payload = FlashcardFactory.build()
    flashcard_response = client.post(
        f"/api/decks/{deck_id}/flashcards",
        json={"front": flashcard_payload.front, "back": flashcard_payload.back},
        headers=headers,
    )
    get_response = client.get(f"/api/decks/{deck_id}", headers=headers)

    assert create_response.status_code == 201
    assert flashcard_response.status_code == 201
    assert get_response.status_code == 200
    assert len(get_response.get_json()["data"]["flashcards"]) == 1


@pytest.mark.integration
def test_duplicate_deck_name_returns_409(client: FlaskClient) -> None:
    headers = _auth_headers(client)
    payload = DeckFactory.build()
    client.post("/api/decks", json={"name": payload.name}, headers=headers)

    response = client.post("/api/decks", json={"name": payload.name}, headers=headers)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "conflict"


@pytest.mark.integration
def test_delete_flashcard_removes_it_from_deck(client: FlaskClient) -> None:
    headers = _auth_headers(client)
    deck = Deck(name="Silinecek", description=None, user_id=1)
    db.session.add(deck)
    db.session.commit()

    flashcard_response = client.post(
        f"/api/decks/{deck.id}/flashcards",
        json={"front": "2 + 2", "back": "4"},
        headers=headers,
    )
    flashcard_id = flashcard_response.get_json()["data"]["id"]

    delete_response = client.delete(f"/api/flashcards/{flashcard_id}", headers=headers)
    get_response = client.get(f"/api/decks/{deck.id}", headers=headers)

    assert delete_response.status_code == 200
    assert get_response.get_json()["data"]["flashcard_count"] == 0


@pytest.mark.integration
def test_invalid_flashcard_payload_returns_422(client: FlaskClient) -> None:
    headers = _auth_headers(client)
    deck = Deck(name="Validasyon", description=None, user_id=1)
    db.session.add(deck)
    db.session.commit()

    response = client.post(
        f"/api/decks/{deck.id}/flashcards",
        json={"front": "", "back": "Cevap"},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_metrics_endpoint_returns_prometheus_metrics(client: FlaskClient) -> None:
    client.get("/health")
    client.get("/missing")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")

    body = response.get_data(as_text=True)
    assert "# TYPE flask_http_request_total counter" in body
    assert "# TYPE flask_http_request_duration_seconds histogram" in body
    assert 'flask_http_request_total{method="GET",status="200"}' in body
    assert 'flask_http_request_total{method="GET",status="404"}' in body
