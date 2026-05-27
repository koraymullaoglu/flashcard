import json
import os
import time

import boto3
import pytest
import requests
from docker.errors import DockerException
from testcontainers.core.container import DockerContainer

from app import create_app
from extensions import db


def _auth_headers(client) -> dict[str, str]:
    client.post("/api/auth/register", json={"username": "s3-user", "password": "test"})
    resp = client.post("/api/auth/login", json={"username": "s3-user", "password": "test"})
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def _wait_for_localstack(endpoint_url: str, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            response = requests.get(f"{endpoint_url}/_localstack/health", timeout=1)
            if response.ok:
                return
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(0.5)

    raise RuntimeError(f"LocalStack hazir olmadi: {last_error}")


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_LOCALSTACK_TESTS") != "true",
    reason="LocalStack testi Docker gerektirdigi icin varsayilan kosuda kapali.",
)
def test_export_deck_creates_s3_object_on_localstack() -> None:
    container = None
    endpoint_url = os.getenv("LOCALSTACK_S3_ENDPOINT_URL")
    if endpoint_url:
        _wait_for_localstack(endpoint_url)
    else:
        try:
            container = (
                DockerContainer("localstack/localstack:3.8.1")
                .with_env("SERVICES", "s3")
                .with_env("AWS_DEFAULT_REGION", "us-east-1")
                .with_exposed_ports(4566)
            )
            container.start()
        except DockerException as exc:
            pytest.skip(f"Docker daemon kullanilamadigi icin LocalStack testi atlandi: {exc}")

        endpoint_url = (
            f"http://{container.get_container_host_ip()}:{container.get_exposed_port(4566)}"
        )
        _wait_for_localstack(endpoint_url)

    try:
        app = create_app(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            JWT_SECRET="test-jwt-secret-that-is-at-least-32-bytes",
            S3_BUCKET_NAME="flashcard-exports",
            S3_REGION="us-east-1",
            S3_ENDPOINT_URL=endpoint_url,
            S3_EXPORT_PREFIX="exports",
            AWS_ACCESS_KEY_ID="test",
            AWS_SECRET_ACCESS_KEY="test",
        )

        with app.app_context():
            db.create_all()
            client = app.test_client()
            headers = _auth_headers(client)

            deck_response = client.post(
                "/api/decks",
                json={"name": "AWS Backup", "description": "LocalStack export testi"},
                headers=headers,
            )
            deck_id = deck_response.get_json()["data"]["id"]

            client.post(
                f"/api/decks/{deck_id}/flashcards",
                json={"front": "S3 nedir?", "back": "Object storage"},
                headers=headers,
            )

            export_response = client.post(f"/api/decks/{deck_id}/export", headers=headers)

            assert export_response.status_code == 200
            export_data = export_response.get_json()["data"]
            assert export_data["bucket"] == "flashcard-exports"
            assert export_data["key"].startswith("exports/user-1/deck-")

            s3_client = boto3.client(
                "s3",
                region_name="us-east-1",
                endpoint_url=endpoint_url,
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            objects = s3_client.list_objects_v2(Bucket="flashcard-exports")
            assert any(
                item["Key"] == export_data["key"]
                for item in objects.get("Contents", [])
            )

            stored_object = s3_client.get_object(
                Bucket="flashcard-exports",
                Key=export_data["key"],
            )
            payload = json.loads(stored_object["Body"].read().decode("utf-8"))

            assert payload["deck"]["id"] == deck_id
            assert payload["deck"]["flashcard_count"] == 1
            assert payload["deck"]["flashcards"][0]["front"] == "S3 nedir?"

            db.session.remove()
            db.drop_all()
            db.engine.dispose()
    finally:
        if container is not None:
            container.stop()
