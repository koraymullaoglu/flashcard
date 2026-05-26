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
    session = requests.Session()

    auth_json = {"username": "e2e", "password": "e2e"}
    session.post(f"{live_server}/api/auth/register", json=auth_json, timeout=5)
    login_resp = session.post(f"{live_server}/api/auth/login", json=auth_json, timeout=5)
    token = login_resp.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    deck_response = session.post(
        f"{live_server}/api/decks",
        json={"name": "E2E Deck", "description": "Gercek HTTP akisi"},
        headers=headers,
        timeout=5,
    )
    deck_id = deck_response.json()["data"]["id"]

    card_response = session.post(
        f"{live_server}/api/decks/{deck_id}/flashcards",
        json={"front": "HTTP nedir?", "back": "Bir protokol"},
        headers=headers,
        timeout=5,
    )
    flashcard_id = card_response.json()["data"]["id"]

    review_response = session.patch(
        f"{live_server}/api/flashcards/{flashcard_id}/review",
        json={"difficulty": "easy"},
        headers=headers,
        timeout=5,
    )
    delete_response = session.delete(
        f"{live_server}/api/flashcards/{flashcard_id}",
        headers=headers,
        timeout=5,
    )

    assert deck_response.status_code == 201
    assert card_response.status_code == 201
    assert review_response.json()["data"]["review_count"] == 1
    assert delete_response.status_code == 200
