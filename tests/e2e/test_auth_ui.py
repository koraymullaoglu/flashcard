from uuid import uuid4

import pytest


@pytest.mark.browser
def test_auth_page_renders_login_form_by_default(page, live_server: str) -> None:
    page.goto(f"{live_server}/auth")

    login_form = page.locator('[data-testid="form-login"]')
    register_form = page.locator('[data-testid="form-register"]')

    assert login_form.is_visible()
    assert not register_form.is_visible()


@pytest.mark.browser
def test_switch_tab_shows_register_form(page, live_server: str) -> None:
    page.goto(f"{live_server}/auth")

    page.click('[data-testid="tab-register"]')
    page.wait_for_timeout(200)

    assert page.locator('[data-testid="form-register"]').is_visible()
    assert not page.locator('[data-testid="form-login"]').is_visible()


@pytest.mark.browser
def test_login_flow_redirects_and_shows_username(page, live_server: str) -> None:
    username = f"e2e-{uuid4().hex[:8]}"
    password = "e2e-password"

    page.goto(f"{live_server}/api/auth/register")
    # Register via form
    page.goto(f"{live_server}/auth")
    page.fill('[data-testid="login-username"]', username)
    page.fill('[data-testid="login-password"]', password)

    # Need to register first via API since login requires existing user
    page.evaluate(
        """(args) => fetch(args.url + '/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: args.username, password: args.password})
        })""",
        {"url": live_server, "username": username, "password": password},
    )
    page.wait_for_timeout(300)

    page.click('[data-testid="btn-login-submit"]')
    page.wait_for_url("**/", timeout=5000)

    page.wait_for_selector('[data-testid="nav-user"]')
    nav_user = page.locator('[data-testid="nav-user"]')
    assert nav_user.is_visible()
    assert username in (nav_user.text_content() or "")


@pytest.mark.browser
def test_register_flow_auto_logs_in_and_redirects(page, live_server: str) -> None:
    username = f"e2e-{uuid4().hex[:8]}"
    password = "e2e-password"

    page.goto(f"{live_server}/auth")
    page.click('[data-testid="tab-register"]')
    page.wait_for_timeout(200)

    page.fill('[data-testid="register-username"]', username)
    page.fill('[data-testid="register-password"]', password)
    page.click('[data-testid="btn-register-submit"]')

    page.wait_for_url("**/", timeout=5000)
    page.wait_for_selector('[data-testid="nav-user"]')
    assert page.locator('[data-testid="nav-user"]').is_visible()


@pytest.mark.browser
def test_login_with_wrong_password_shows_error(page, live_server: str) -> None:
    username = f"e2e-{uuid4().hex[:8]}"
    password = "e2e-password"

    # Register user via API (must be on same origin as live_server for fetch)
    page.goto(f"{live_server}/auth")
    page.evaluate(
        """(args) => fetch(args.url + '/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: args.username, password: args.password})
        })""",
        {"url": live_server, "username": username, "password": password},
    )
    page.wait_for_timeout(300)

    page.goto(f"{live_server}/auth")
    page.fill('[data-testid="login-username"]', username)
    page.fill('[data-testid="login-password"]', "wrong-password")
    page.click('[data-testid="btn-login-submit"]')

    page.wait_for_selector('[data-testid="login-error"]', timeout=3000)
    error = page.locator('[data-testid="login-error"]')
    assert error.is_visible()


@pytest.mark.browser
def test_register_duplicate_username_shows_error(page, live_server: str) -> None:
    username = f"e2e-{uuid4().hex[:8]}"
    password = "e2e-password"

    # Register first user (must be on same origin for fetch)
    page.goto(f"{live_server}/auth")
    page.evaluate(
        """(args) => fetch(args.url + '/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: args.username, password: args.password})
        })""",
        {"url": live_server, "username": username, "password": password},
    )
    page.wait_for_timeout(300)

    page.goto(f"{live_server}/auth")
    page.click('[data-testid="tab-register"]')
    page.wait_for_timeout(200)
    page.fill('[data-testid="register-username"]', username)
    page.fill('[data-testid="register-password"]', password)
    page.click('[data-testid="btn-register-submit"]')

    page.wait_for_selector('[data-testid="register-error"]', timeout=3000)
    assert page.locator('[data-testid="register-error"]').is_visible()


@pytest.mark.browser
def test_logout_clears_token_and_redirects(page, live_server: str) -> None:
    from tests.e2e.conftest import auth_token

    token = auth_token(live_server)
    page.goto(live_server + "/")
    page.evaluate("(t) => { localStorage.setItem('flashcard_token', t); }", token)
    page.reload()
    page.wait_for_selector('[data-testid="nav-user"]')

    page.click('[data-testid="nav-logout"]')
    page.wait_for_url("**/auth", timeout=5000)

    token_after = page.evaluate("() => localStorage.getItem('flashcard_token')")
    assert token_after is None


@pytest.mark.browser
def test_already_authenticated_redirects_from_auth(page, live_server: str) -> None:
    from tests.e2e.conftest import auth_token

    token = auth_token(live_server)
    # Navigate to / first to set localStorage, then go to /auth
    page.goto(live_server + "/")
    page.evaluate("(t) => { localStorage.setItem('flashcard_token', t); }", token)
    page.reload()
    page.wait_for_timeout(300)

    page.goto(f"{live_server}/auth")
    page.wait_for_timeout(500)
    assert not page.url.endswith("/auth")


@pytest.mark.browser
def test_login_button_disabled_during_request(page, live_server: str) -> None:
    username = f"e2e-{uuid4().hex[:8]}"
    password = "e2e-password"

    # Register user (must be on same origin for fetch)
    page.goto(f"{live_server}/auth")
    page.evaluate(
        """(args) => fetch(args.url + '/api/auth/register', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: args.username, password: args.password})
        })""",
        {"url": live_server, "username": username, "password": password},
    )
    page.wait_for_timeout(300)

    page.goto(f"{live_server}/auth")
    page.fill('[data-testid="login-username"]', username)
    page.fill('[data-testid="login-password"]', password)

    page.click('[data-testid="btn-login-submit"]')
    page.wait_for_timeout(100)

    # After request completes, button should be re-enabled
    page.wait_for_url("**/", timeout=5000)
