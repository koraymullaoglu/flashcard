from collections.abc import Iterator
from threading import Thread

import pytest
import requests
from flask import Flask
from werkzeug.serving import make_server


@pytest.fixture()
def live_server(app: Flask) -> Iterator[str]:
    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    thread.join(timeout=5)


@pytest.mark.e2e
def test_user_can_create_review_and_delete_flashcard(live_server: str) -> None:
    deck_response = requests.post(
        f"{live_server}/api/decks",
        json={"name": "E2E Deck", "description": "Gercek HTTP akisi"},
        timeout=5,
    )
    deck_id = deck_response.json()["data"]["id"]

    card_response = requests.post(
        f"{live_server}/api/decks/{deck_id}/flashcards",
        json={"front": "HTTP nedir?", "back": "Bir protokol"},
        timeout=5,
    )
    flashcard_id = card_response.json()["data"]["id"]

    review_response = requests.patch(
        f"{live_server}/api/flashcards/{flashcard_id}/review",
        json={"difficulty": "easy"},
        timeout=5,
    )
    delete_response = requests.delete(
        f"{live_server}/api/flashcards/{flashcard_id}",
        timeout=5,
    )

    assert deck_response.status_code == 201
    assert card_response.status_code == 201
    assert review_response.json()["data"]["review_count"] == 1
    assert delete_response.status_code == 200
