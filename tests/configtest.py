"""
Shared test setup (pytest loads this file automatically).

1. temp_storage: every test gets its OWN empty storage folder,
   so tests never touch your real uploads.
2. fake_ai: replaces the AI provider with fake functions
   (free, offline, always the same result).
"""
import pytest

from app import config, llm


@pytest.fixture(autouse=True)          # autouse = used by every test automatically
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOADS_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setattr(config, "INDEX_FOLDER", str(tmp_path / "index"))
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "app.db"))


def fake_embed_texts(texts, task_type="RETRIEVAL_DOCUMENT", batch_size=50):
    """A very simple 'embedding': how many times each letter a-z appears."""
    vectors = []
    for text in texts:
        text = text.lower()
        vectors.append([float(text.count(letter)) for letter in "abcdefghijklmnopqrstuvwxyz"])
    return vectors


def fake_generate_answer(prompt):
    return "FAKE ANSWER [1]"


@pytest.fixture
def fake_ai(monkeypatch):
    monkeypatch.setattr(llm, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(llm, "generate_answer", fake_generate_answer)