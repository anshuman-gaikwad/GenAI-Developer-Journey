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
