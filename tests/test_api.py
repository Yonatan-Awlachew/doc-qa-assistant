# FILE: tests/test_api.py
"""
Tests for the API. We replace ("mock") the Gemini calls with fake functions,
so the tests run without internet, without an API key and for free.
"""
import numpy as np
from fastapi.testclient import TestClient

from app import llm, main

client = TestClient(main.app)

FAKE_CHUNKS = [
    {"id": 0, "source": "rules.pdf", "page": 4, "text": "Enrollment closes on 30 September."},
    {"id": 1, "source": "rules.pdf", "page": 9, "text": "The library opens at 8:00."},
]
FAKE_VECTORS = np.array([[1, 0], [0, 1]], dtype="float32")


def fake_embed_texts(texts, task_type="RETRIEVAL_DOCUMENT", batch_size=50):
    return [[1.0, 0.0] for _ in texts]  # always "similar" to chunk 0


def fake_generate_answer(prompt):
    return "Enrollment closes on 30 September [1]."


def setup_fakes(monkeypatch):
    monkeypatch.setattr(llm, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(llm, "generate_answer", fake_generate_answer)
    main.index["vectors"] = FAKE_VECTORS
    main.index["chunks"] = FAKE_CHUNKS


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_answer_and_sources(monkeypatch):
    setup_fakes(monkeypatch)
    response = client.post("/ask", json={"question": "When does enrollment close?", "top_k": 1})
    assert response.status_code == 200
    data = response.json()
    assert "30 September" in data["answer"]
    assert data["sources"][0]["source"] == "rules.pdf"
    assert data["sources"][0]["page"] == 4


def test_question_too_short_is_rejected(monkeypatch):
    setup_fakes(monkeypatch)
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 422  # 422 = the input JSON is not valid


def test_stats(monkeypatch):
    setup_fakes(monkeypatch)
    response = client.get("/stats")
    assert response.json() == {"chunks": 2, "documents": ["rules.pdf"]}