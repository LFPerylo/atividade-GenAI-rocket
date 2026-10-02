from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from cinerocket.api.app import create_app
from cinerocket.container import Container


@pytest.fixture
def client(container: Container) -> Iterator[TestClient]:
    with TestClient(create_app(container)) as test_client:
        yield test_client


def test_chat_returns_answer_and_keeps_session(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"question": "Top filmes por receita"})

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["columns"] == ["titulo", "receita_brl"]
    transcript = client.get(f"/api/v1/sessions/{body['session_id']}")
    assert [turn["question"] for turn in transcript.json()] == ["Top filmes por receita"]


def test_domain_errors_are_mapped_to_http(client: TestClient) -> None:
    assert client.post("/api/v1/chat", json={"question": "   "}).status_code == 422
    assert client.get("/api/v1/sessions/inexistente").status_code == 404


def test_health_reports_components(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body == {"status": "ok", "database": True, "semantic_index": False, "models": ["scripted"]}
