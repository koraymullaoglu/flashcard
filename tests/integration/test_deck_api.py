import pytest
from flask.testing import FlaskClient
from tests.factories import DeckFactory, FlashcardFactory

from extensions import db
from models import Deck


@pytest.mark.integration
def test_create_and_get_deck_with_flashcard(client: FlaskClient) -> None:
    deck_payload = DeckFactory.build()
    create_response = client.post(
        "/api/decks",
        json={"name": deck_payload.name, "description": deck_payload.description},
    )
    deck_id = create_response.get_json()["data"]["id"]

    flashcard_payload = FlashcardFactory.build()
    flashcard_response = client.post(
        f"/api/decks/{deck_id}/flashcards",
        json={"front": flashcard_payload.front, "back": flashcard_payload.back},
    )
    get_response = client.get(f"/api/decks/{deck_id}")

    assert create_response.status_code == 201
    assert flashcard_response.status_code == 201
    assert get_response.status_code == 200
    assert len(get_response.get_json()["data"]["flashcards"]) == 1


@pytest.mark.integration
def test_duplicate_deck_name_returns_409(client: FlaskClient) -> None:
    payload = DeckFactory.build()
    client.post("/api/decks", json={"name": payload.name})

    response = client.post("/api/decks", json={"name": payload.name})

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "conflict"


@pytest.mark.integration
def test_delete_flashcard_removes_it_from_deck(client: FlaskClient) -> None:
    deck = Deck(name="Silinecek", description=None)
    db.session.add(deck)
    db.session.commit()

    flashcard_response = client.post(
        f"/api/decks/{deck.id}/flashcards",
        json={"front": "2 + 2", "back": "4"},
    )
    flashcard_id = flashcard_response.get_json()["data"]["id"]

    delete_response = client.delete(f"/api/flashcards/{flashcard_id}")
    get_response = client.get(f"/api/decks/{deck.id}")

    assert delete_response.status_code == 200
    assert get_response.get_json()["data"]["flashcard_count"] == 0


@pytest.mark.integration
def test_invalid_flashcard_payload_returns_422(client: FlaskClient) -> None:
    deck = Deck(name="Validasyon", description=None)
    db.session.add(deck)
    db.session.commit()

    response = client.post(f"/api/decks/{deck.id}/flashcards", json={"front": "", "back": "Cevap"})

    assert response.status_code == 422
