import pytest
from tests.e2e.conftest import _api_fetch, authenticate_page


@pytest.mark.browser
def test_empty_deck_list_shows_empty_state(page, live_server: str) -> None:
    authenticate_page(page, live_server)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="page-title"]')

    empty_state = page.locator('[data-testid="empty-state"]')
    assert empty_state.is_visible()


@pytest.mark.browser
def test_deck_grid_shows_deck_cards(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)

    for name in ["Python", "JavaScript"]:
        _api_fetch(
            page, live_server, token, "POST", "/api/decks",
            body={"name": name, "description": "test"},
        )
    page.wait_for_timeout(300)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="deck-grid"]')

    grid = page.locator('[data-testid="deck-grid"]')
    assert grid.is_visible()
    cards = page.locator('[data-testid^="deck-card-"]')
    assert cards.count() == 2


@pytest.mark.browser
def test_create_deck_via_modal(page, live_server: str) -> None:
    authenticate_page(page, live_server)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="btn-open-create-deck"]')

    page.click('[data-testid="btn-open-create-deck"]')
    page.wait_for_selector('[data-testid="modal-create-deck"]')

    modal = page.locator('[data-testid="modal-create-deck"]')
    assert modal.is_visible()

    page.fill('[data-testid="input-deck-name"]', "Yeni Deste")
    page.fill('[data-testid="input-deck-desc"]', "Aciklama")
    page.click('[data-testid="btn-submit-deck"]')

    page.wait_for_timeout(500)
    assert not page.locator('[data-testid="modal-create-deck"]').is_visible()

    page.wait_for_selector('[data-testid^="deck-card-"]')
    cards = page.locator('[data-testid^="deck-card-"]')
    assert cards.count() >= 1


@pytest.mark.browser
def test_create_deck_modal_cancel_closes(page, live_server: str) -> None:
    authenticate_page(page, live_server)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="btn-open-create-deck"]')
    page.click('[data-testid="btn-open-create-deck"]')
    page.wait_for_selector('[data-testid="modal-create-deck"]')

    page.click('[data-testid="btn-cancel-create"]')
    page.wait_for_timeout(300)
    assert not page.locator('[data-testid="modal-create-deck"]').is_visible()


@pytest.mark.browser
def test_create_deck_modal_closes_on_escape(page, live_server: str) -> None:
    authenticate_page(page, live_server)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="btn-open-create-deck"]')
    page.click('[data-testid="btn-open-create-deck"]')
    page.wait_for_selector('[data-testid="modal-create-deck"]')

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    assert not page.locator('[data-testid="modal-create-deck"]').is_visible()


@pytest.mark.browser
def test_create_deck_modal_focuses_name_field(page, live_server: str) -> None:
    authenticate_page(page, live_server)

    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="btn-open-create-deck"]')
    page.click('[data-testid="btn-open-create-deck"]')
    page.wait_for_selector('[data-testid="input-deck-name"]')

    focused = page.evaluate(
        "() => document.activeElement"
        " === document.querySelector('[data-testid=\"input-deck-name\"]')"
    )
    assert focused


@pytest.mark.browser
def test_unauthenticated_user_sees_login_link(page, live_server: str) -> None:
    page.goto(live_server + "/")
    page.wait_for_selector('[data-testid="nav-login"]')
    assert page.locator('[data-testid="nav-login"]').is_visible()


@pytest.mark.browser
def test_deck_card_links_to_deck_detail(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)

    result = _api_fetch(
        page, live_server, token, "POST", "/api/decks",
        body={"name": "Test Deck", "description": "To click"},
    )
    deck_id = result["data"]["id"]

    page.goto(live_server + "/")
    page.wait_for_selector(f'[data-testid="deck-card-{deck_id}"]')
    page.click(f'[data-testid="deck-card-{deck_id}"]')

    page.wait_for_url(f"**/decks/{deck_id}", timeout=5000)
    assert f"/decks/{deck_id}" in page.url


@pytest.mark.browser
def test_error_banner_shown_with_invalid_token(page, live_server: str) -> None:
    page.goto(live_server + "/")
    page.evaluate(
        "() => { localStorage.setItem('flashcard_token', 'invalid.token.here'); }"
    )
    page.reload()

    page.wait_for_timeout(1000)
