from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "records_loaded" in response.json()


def test_records_endpoint():
    response = client.get("/records")

    assert response.status_code == 200
    assert "records" in response.json()
    assert "total" in response.json()


def test_records_limit():
    response = client.get("/records?limit=2")

    assert response.status_code == 200
    assert response.json()["returned"] <= 2


def test_record_not_found():
    response = client.get("/records/999999")

    assert response.status_code == 404


def test_search_endpoint():
    response = client.get("/search?q=consumer")

    assert response.status_code == 200
    assert response.json()["query"] == "consumer"
    assert "results" in response.json()


def test_ask_endpoint_with_fake_rag(monkeypatch):
    def fake_answer_question(question):
        return {
            "answer": "Consumers have rights under the Consumer Protection Act.",
            "citations": [
                {
                    "title": "Consumer Protection Act, 2019",
                    "source": "consumer_act.pdf",
                    "page": 10,
                }
            ],
        }

    monkeypatch.setattr("app.main.answer_question", fake_answer_question)

    response = client.post("/ask", json={"question": "What are consumer rights?"})

    assert response.status_code == 200
    assert "Consumer Protection Act" in response.json()["answer"]
    assert len(response.json()["citations"]) == 1


def test_ask_endpoint_invalid_question():
    response = client.post("/ask", json={"question": "Hi"})

    assert response.status_code == 422


def test_agent_endpoint(monkeypatch):
    def fake_agent(**kwargs):
        return {"status": "success", "question": kwargs["question"]}

    monkeypatch.setattr("app.main.run_agent_graph", fake_agent)

    response = client.post("/agent", json={"question": "Explain consumer rights"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health_request_logs_latency(caplog):
    """Health requests should produce an API latency log."""
    import logging

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="app.main"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any(
        "api_request method=GET path=/health status=200 latency_ms="
        in record.getMessage()
        for record in caplog.records
    )

def test_ask_rejects_oversized_question():
    """Reject questions longer than 2000 characters."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/ask",
        json={"question": "A" * 2001},
    )

    assert response.status_code == 422


def test_chat_rejects_oversized_question():
    """Apply the same question limit to /chat."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "A" * 2001},
    )

    assert response.status_code == 422


def test_ask_rejects_short_question():
    """Reject questions shorter than 3 characters."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/ask",
        json={"question": "Hi"},
    )

    assert response.status_code == 422


def test_questions_rejects_oversized_question():
    """The /questions endpoint rejects questions over 2000 characters."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/questions",
        json={"question": "A" * 2001},
    )

    assert response.status_code == 422


def test_agent_rejects_oversized_question():
    """The /agent endpoint rejects questions over 2000 characters."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/agent",
        json={"question": "A" * 2001},
    )

    assert response.status_code == 422


def test_agent_allows_empty_question_for_approval_resume():
    """An agent approval-resume request may omit the question."""
    from app.main import AgentRequest

    request = AgentRequest(
        thread_id="test-thread",
        approved=True,
    )

    assert request.question == ""
    assert request.thread_id == "test-thread"
    assert request.approved is True


def test_ask_hides_internal_error_details():
    """An API failure must not expose internal configuration details."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app
    from app.response_cache import clear_cache

    clear_cache()

    client = TestClient(app)

    with patch(
        "app.main.answer_question",
        side_effect=RuntimeError("SECRET_INTERNAL_PROVIDER_ERROR"),
    ):
        response = client.post(
            "/ask",
            json={"question": "My product arrived damaged yesterday."},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Unable to generate an answer right now. Please try again later."
    )
    assert "SECRET_INTERNAL_PROVIDER_ERROR" not in response.text


def test_chat_hides_internal_error_details():
    """Chat failures must not expose provider errors."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    with patch(
        "app.main.generate_response",
        side_effect=RuntimeError("SECRET_INTERNAL_PROVIDER_ERROR"),
    ):
        response = client.post(
            "/chat",
            json={"question": "What are my consumer rights?"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Unable to generate an answer right now. Please try again later."
    )
    assert "SECRET_INTERNAL_PROVIDER_ERROR" not in response.text


def test_agent_rejects_oversized_optional_fields():
    """Agent metadata must have reasonable length limits."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/agent",
        json={
            "question": "My product is defective.",
            "thread_id": "x" * 101,
        },
    )

    assert response.status_code == 422

    response = client.post(
        "/agent",
        json={
            "question": "My product is defective.",
            "cause_date": "x" * 51,
        },
    )

    assert response.status_code == 422
