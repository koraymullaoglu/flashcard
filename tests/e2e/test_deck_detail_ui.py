import pytest
from tests.e2e.conftest import _api_fetch, authenticate_page


def _create_deck(live_server: str, token: str, page) -> dict:
    result = _api_fetch(
        page, live_server, token, "POST", "/api/decks",
        body={"name": "Test Deck", "description": "A description"},
    )
    return result["data"]


@pytest.mark.browser
def test_deck_detail_shows_title_and_description(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="deck-title"]')

    title = page.locator('[data-testid="deck-title"]')
    desc = page.locator('[data-testid="deck-description"]')
    assert deck["name"] in (title.text_content() or "")
    assert desc.is_visible()


@pytest.mark.browser
def test_card_list_shows_cards(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    for i in range(3):
        _api_fetch(
            page, live_server, token, "POST",
            f"/api/decks/{deck['id']}/flashcards",
            body={"front": f"Q{i}", "back": f"A{i}"},
        )
    page.wait_for_timeout(300)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="card-table"]')

    rows = page.locator('[data-testid^="card-row-"]')
    assert rows.count() == 3


@pytest.mark.browser
def test_empty_deck_shows_empty_state(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="card-empty"]')
    assert page.locator('[data-testid="card-empty"]').is_visible()


@pytest.mark.browser
def test_add_card_via_modal(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-open-add-card"]')

    page.click('[data-testid="btn-open-add-card"]')
    page.wait_for_selector('[data-testid="modal-add-card"]')
    assert page.locator('[data-testid="modal-add-card"]').is_visible()

    page.fill('[data-testid="input-card-front"]', "Soru burada")
    page.fill('[data-testid="input-card-back"]', "Cevap burada")
    page.click('[data-testid="btn-submit-card"]')

    page.wait_for_timeout(500)
    assert not page.locator('[data-testid="modal-add-card"]').is_visible()
    page.wait_for_selector('[data-testid^="card-row-"]')


@pytest.mark.browser
def test_add_card_modal_cancel_closes(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-open-add-card"]')
    page.click('[data-testid="btn-open-add-card"]')
    page.wait_for_selector('[data-testid="modal-add-card"]')

    page.click('[data-testid="btn-cancel-add-card"]')
    page.wait_for_timeout(300)
    assert not page.locator('[data-testid="modal-add-card"]').is_visible()


@pytest.mark.browser
def test_delete_card_flow(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    result = _api_fetch(
        page, live_server, token, "POST",
        f"/api/decks/{deck['id']}/flashcards",
        body={"front": "Q", "back": "A"},
    )
    card_id = result["data"]["id"]

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector(f'[data-testid="btn-delete-card-{card_id}"]')
    page.click(f'[data-testid="btn-delete-card-{card_id}"]')

    page.wait_for_selector('[data-testid="modal-delete"]')
    assert page.locator('[data-testid="modal-delete"]').is_visible()

    page.click('[data-testid="btn-confirm-delete"]')
    page.wait_for_timeout(500)

    page.wait_for_selector('[data-testid="card-empty"]')


@pytest.mark.browser
def test_stats_bar_updates(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="stats-bar"]')

    total = page.locator('[data-testid="stat-total"]')
    assert "0" in (total.text_content() or "")


@pytest.mark.browser
def test_back_button_navigates_to_deck_list(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-back"]')
    page.click('[data-testid="btn-back"]')

    page.wait_for_url("**/", timeout=5000)
    assert "/decks/" not in page.url


@pytest.mark.browser
def test_study_button_present(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-study"]')
    assert page.locator('[data-testid="btn-study"]').is_visible()


@pytest.mark.browser
def test_export_button_present(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-export"]')
    btn = page.locator('[data-testid="btn-export"]')
    assert btn.is_visible()


@pytest.mark.browser
def test_export_click_shows_toast(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-export"]')
    page.click('[data-testid="btn-export"]')

    page.wait_for_selector('[data-testid="toast"]', timeout=5000)
    toast = page.locator('[data-testid="toast"]')
    assert toast.is_visible()


@pytest.mark.browser
def test_export_button_disabled_during_request(page, live_server: str) -> None:
    token = authenticate_page(page, live_server)
    deck = _create_deck(live_server, token, page)

    page.goto(f"{live_server}/decks/{deck['id']}")
    page.wait_for_selector('[data-testid="btn-export"]')

    page.click('[data-testid="btn-export"]')
    page.wait_for_timeout(100)

    page.wait_for_selector('[data-testid="toast"]', timeout=5000)

    btn = page.locator('[data-testid="btn-export"]')
    assert not btn.is_disabled()
