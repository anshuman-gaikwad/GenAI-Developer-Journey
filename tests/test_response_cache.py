
"""Tests for the GrahakNyay in-memory response cache."""

from unittest.mock import patch

import pytest

from app.response_cache import (
    CACHE_MAX_ENTRIES,
    clear_cache,
    get_cached_response,
    set_cached_response,
)


@pytest.fixture(autouse=True)
def empty_cache():
    """Start and finish every test with an empty cache."""
    clear_cache()
    yield
    clear_cache()


def test_cache_miss():
    assert get_cached_response("unknown question") is None


def test_cache_hit():
    response = {"answer": "Consumer rights information", "citations": []}

    set_cached_response("question one", response)

    assert get_cached_response("question one") == response


def test_cache_expiry():
    response = {"answer": "Temporary answer"}

    with patch("app.response_cache.time.monotonic", return_value=100.0):
        set_cached_response("question", response)

    with patch("app.response_cache.time.monotonic", return_value=401.0):
        assert get_cached_response("question") is None


def test_cached_response_is_independent():
    response = {"answer": "Original answer", "citations": []}

    set_cached_response("question", response)

    cached = get_cached_response("question")
    cached["answer"] = "Modified answer"

    assert get_cached_response("question")["answer"] == "Original answer"


def test_cache_max_entries():
    for index in range(CACHE_MAX_ENTRIES + 1):
        set_cached_response(
            f"question-{index}",
            {"answer": f"answer-{index}"},
        )

    assert get_cached_response("question-0") is None
    assert get_cached_response(f"question-{CACHE_MAX_ENTRIES}") is not None


def test_ask_endpoint_uses_cache():
    """An approved question should call RAG only once."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app

    question = "What is an unfair trade practice?"

    fake_result = {
        "answer": "An unfair trade practice can mislead consumers.",
        "citations": [
            {
                "title": "Unfair Trade Practice",
                "source": "Consumer Protection Act, 2019",
                "page": "Section 2(47)",
            }
        ],
    }

    with patch("app.main.answer_question", return_value=fake_result) as mock_rag:
        client = TestClient(app)

        first = client.post("/ask", json={"question": question})
        second = client.post("/ask", json={"question": question})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert mock_rag.call_count == 1


def test_ask_endpoint_bypasses_cache():
    """Questions outside the allowlist should always call RAG."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app

    question = "My washing machine stopped working after delivery."

    fake_result = {
        "answer": "You may have consumer remedies.",
        "citations": [],
    }

    with patch("app.main.answer_question", return_value=fake_result) as mock_rag:
        client = TestClient(app)

        first = client.post("/ask", json={"question": question})
        second = client.post("/ask", json={"question": question})

    assert first.status_code == 200
    assert second.status_code == 200
    assert mock_rag.call_count == 2


def test_cached_citations_are_independent():
    """Changing a returned citation must not change the cached version."""
    response = {
        "answer": "Consumer information",
        "citations": [{"title": "Original citation"}],
    }

    set_cached_response("citation-question", response)

    cached = get_cached_response("citation-question")
    cached["citations"][0]["title"] = "Modified citation"

    assert (
        get_cached_response("citation-question")["citations"][0]["title"]
        == "Original citation"
    )
