import pytest
import requests
from tests.e2e.conftest import REQUEST_TIMEOUT_SECONDS, _auth_session
from tests.factories import DeckFactory, FlashcardFactory


def _create_deck(
    session: requests.Session,
    live_server: str,
    headers: dict[str, str],
    **overrides: object,
) -> requests.Response:
    deck_payload = DeckFactory.payload(**overrides)
    return session.post(
        f"{live_server}/api/decks",
        json=deck_payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def _create_flashcard(
    session: requests.Session,
    live_server: str,
    deck_id: int,
    headers: dict[str, str],
    **overrides: object,
) -> requests.Response:
    flashcard_payload = FlashcardFactory.payload(**overrides)
    return session.post(
        f"{live_server}/api/decks/{deck_id}/flashcards",
        json=flashcard_payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


@pytest.mark.e2e
def test_user_can_create_deck_and_see_it_in_list(live_server: str) -> None:
    session, headers = _auth_session(live_server)
    deck_response = _create_deck(
        session,
        live_server,
        headers=headers,
        name="E2E Deck",
        description="Gercek HTTP akisi",
    )
    list_response = session.get(
        f"{live_server}/api/decks",
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    assert deck_response.status_code == 201
    assert list_response.status_code == 200
    assert any(
        deck["name"] == "E2E Deck" for deck in list_response.json()["data"]
    )


@pytest.mark.e2e
def test_user_can_create_flashcard_and_review_it_out_of_due_list(live_server: str) -> None:
    session, headers = _auth_session(live_server)
    deck_response = _create_deck(
        session,
        live_server,
        headers=headers,
        name="Review Deck",
        description="Kart olusturma ve review akisi",
    )
    deck_id = deck_response.json()["data"]["id"]

    card_response = _create_flashcard(
        session,
        live_server,
        deck_id,
        headers=headers,
        front="HTTP nedir?",
        back="Bir protokol",
    )
    flashcard_id = card_response.json()["data"]["id"]
    due_before_review = session.get(
        f"{live_server}/api/decks/{deck_id}?due_only=true",
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    review_response = session.patch(
        f"{live_server}/api/flashcards/{flashcard_id}/review",
        json={"difficulty": "easy"},
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    due_after_review = session.get(
        f"{live_server}/api/decks/{deck_id}?due_only=true",
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    assert deck_response.status_code == 201
    assert card_response.status_code == 201
    assert due_before_review.status_code == 200
    assert len(due_before_review.json()["data"]["flashcards"]) == 1
    assert review_response.status_code == 200
    assert review_response.json()["data"]["review_count"] == 1
    assert review_response.json()["data"]["difficulty"] == "easy"
    assert len(due_after_review.json()["data"]["flashcards"]) == 0


@pytest.mark.e2e
def test_user_can_delete_flashcard_and_deck_detail_reflects_it(live_server: str) -> None:
    session, headers = _auth_session(live_server)
    deck_response = _create_deck(
        session,
        live_server,
        headers=headers,
        name="Delete Deck",
        description="Silme akisi",
    )
    deck_id = deck_response.json()["data"]["id"]
    card_response = _create_flashcard(
        session,
        live_server,
        deck_id,
        headers=headers,
        front="Silinecek soru",
        back="Silinecek cevap",
    )
    flashcard_id = card_response.json()["data"]["id"]

    delete_response = session.delete(
        f"{live_server}/api/flashcards/{flashcard_id}",
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    deck_detail_response = session.get(
        f"{live_server}/api/decks/{deck_id}",
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    assert deck_response.status_code == 201
    assert card_response.status_code == 201
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["deleted"] is True
    assert deck_detail_response.status_code == 200
    assert deck_detail_response.json()["data"]["flashcard_count"] == 0
    assert deck_detail_response.json()["data"]["flashcards"] == []
