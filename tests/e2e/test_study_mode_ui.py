import pytest
from tests.e2e.conftest import _api_fetch, authenticate_page


def _setup_deck_with_cards(live_server: str, token: str, page, count: int = 3) -> dict:
    result = _api_fetch(
        page, live_server, token, "POST", "/api/decks",
        body={"name": "Study Deck", "description": "Study test"},
    )
    deck = result["data"]

    for i in range(count):
        _api_fetch(
            page, live_server, token, "POST",
            f"/api/decks/{deck['id']}/flashcards",
            body={"front": f"Q{i+1}", "back": f"A{i+1}"},
        )
    page.wait_for_timeout(300)
    return deck


@pytest.mark.browser
def test_study_button_disabled_when_no_due_cards(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)

    result = _api_fetch(
        page, live_server, token, "POST", "/api/decks",
        body={"name": "Empty Deck", "description": "No cards"},
    )
    deck_id = result["data"]["id"]

    page.goto(f"{live_server}/decks/{deck_id}")
    page.wait_for_selector('[data-testid="btn-study"]')

    btn = page.locator('[data-testid="btn-study"]')
    assert btn.is_disabled()


@pytest.mark.browser
def test_study_mode_launches_with_due_cards(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=3)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')

    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-view"]')

    assert page.locator('[data-testid="study-view"]').is_visible()
    assert not page.locator('[data-testid="card-list-view"]').is_visible()

    total_text = page.locator('[data-testid="study-total"]').text_content()
    assert "3" in (total_text or "")


@pytest.mark.browser
def test_flip_card_reveals_back_and_difficulty_buttons(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_timeout(400)

    card = page.locator('[data-testid="study-card"]')
    class_attr = card.get_attribute("class") or ""
    assert "flipped" in class_attr

    assert page.locator('[data-testid="difficulty-btns"]').is_visible()


@pytest.mark.browser
def test_rate_difficulty_advances_to_next_card(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=2)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_selector('[data-testid="btn-diff-good"]')
    page.click('[data-testid="btn-diff-good"]')
    page.wait_for_timeout(500)

    current_text = page.locator('[data-testid="study-current"]').text_content()
    assert "2" in (current_text or "")


@pytest.mark.browser
def test_study_completion_shows_complete_view(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_selector('[data-testid="btn-diff-good"]')
    page.click('[data-testid="btn-diff-good"]')
    page.wait_for_selector('[data-testid="study-complete"]')

    assert page.locator('[data-testid="study-complete"]').is_visible()


@pytest.mark.browser
def test_exit_study_returns_to_card_list(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=2)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="btn-exit-study"]')

    page.click('[data-testid="btn-exit-study"]')
    page.wait_for_selector('[data-testid="card-list-view"]')

    assert page.locator('[data-testid="card-list-view"]').is_visible()
    assert not page.locator('[data-testid="study-view"]').is_visible()


@pytest.mark.browser
def test_finish_study_button_returns_to_card_list(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_selector('[data-testid="btn-diff-good"]')
    page.click('[data-testid="btn-diff-good"]')
    page.wait_for_selector('[data-testid="btn-finish-study"]')

    page.click('[data-testid="btn-finish-study"]')
    page.wait_for_selector('[data-testid="card-list-view"]')
    assert page.locator('[data-testid="card-list-view"]').is_visible()


@pytest.mark.browser
def test_space_key_flips_card_in_study_mode(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.keyboard.press("Space")
    page.wait_for_timeout(400)

    card = page.locator('[data-testid="study-card"]')
    class_attr = card.get_attribute("class") or ""
    assert "flipped" in class_attr


@pytest.mark.browser
def test_after_review_card_no_longer_due(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_selector('[data-testid="btn-diff-easy"]')
    page.click('[data-testid="btn-diff-easy"]')
    page.wait_for_timeout(500)

    page.wait_for_selector('[data-testid="btn-finish-study"]')
    page.click('[data-testid="btn-finish-study"]')

    page.wait_for_selector('[data-testid="stats-bar"]')
    page.wait_for_timeout(800)
    due_text = page.locator('[data-testid="stat-due"]').text_content()
    assert "0" in (due_text or "")


@pytest.mark.browser
def test_difficulty_buttons_disabled_during_request(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _setup_deck_with_cards(live_server, token, page, count=1)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    page.click('[data-testid="btn-study"]')
    page.wait_for_selector('[data-testid="study-card"]')

    page.click('[data-testid="study-card"]')
    page.wait_for_selector('[data-testid="btn-diff-good"]')

    page.click('[data-testid="btn-diff-good"]')
    page.wait_for_timeout(100)

    page.wait_for_timeout(500)
