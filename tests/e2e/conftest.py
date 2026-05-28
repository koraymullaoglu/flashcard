from collections.abc import Iterator
from threading import Thread
from uuid import uuid4

import pytest
import requests
from flask import Flask
from werkzeug.serving import make_server

REQUEST_TIMEOUT_SECONDS = 5


@pytest.fixture()
def live_server(app: Flask) -> Iterator[str]:
    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    thread.join(timeout=5)


def _auth_session(live_server: str) -> tuple[requests.Session, dict[str, str]]:
    session = requests.Session()
    username = f"e2e-{uuid4().hex[:8]}"
    auth_payload = {"username": username, "password": "e2e-password"}

    register_response = session.post(
        f"{live_server}/api/auth/register",
        json=auth_payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    login_response = session.post(
        f"{live_server}/api/auth/login",
        json=auth_payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    token = login_response.json()["data"]["token"]

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    return session, {"Authorization": f"Bearer {token}"}


def auth_token(live_server: str) -> str:
    _, headers = _auth_session(live_server)
    return headers["Authorization"].replace("Bearer ", "")


def _api_fetch(
    page, live_server: str, token: str, method: str, path: str, body: dict | None = None
) -> dict:
    """Browser-side API call via fetch. Returns parsed JSON response."""
    return page.evaluate(
        """(args) => {
            const init = {method: args.method, headers: args.headers};
            if (args.body) init.body = JSON.stringify(args.body);
            return fetch(args.url + args.path, init).then(r => r.json());
        }""",
        {
            "url": live_server,
            "method": method,
            "path": path,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            "body": body,
        },
    )


def authenticate_page(page, live_server: str) -> str:
    token = auth_token(live_server)
    page.goto(live_server + "/")
    page.evaluate("(t) => { localStorage.setItem('flashcard_token', t); }", token)
    page.reload()
    page.wait_for_selector('[data-testid="nav-user"]')
    return token
