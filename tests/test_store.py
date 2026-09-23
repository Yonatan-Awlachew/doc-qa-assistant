# FILE: tests/test_store.py
"""Tests for the tiny vector store. No API key needed."""
import numpy as np

from app import store

CHUNKS = [
    {"id": 0, "source": "a.pdf", "page": 1, "text": "cats"},
    {"id": 1, "source": "a.pdf", "page": 2, "text": "dogs"},
    {"id": 2, "source": "b.pdf", "page": 1, "text": "cars"},
]
VECTORS = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype="float32")


def test_cosine_similarity_values():
    scores = store.cosine_similarity([1, 0, 0], VECTORS)
    assert round(float(scores[0]), 3) == 1.0  # same direction
    assert round(float(scores[1]), 3) == 0.0  # perpendicular = unrelated


def test_search_returns_most_similar_first():
    results = store.search([0.1, 0.9, 0.0], VECTORS, CHUNKS, top_k=2)
    assert len(results) == 2
    assert results[0]["text"] == "dogs"
    assert results[0]["score"] >= results[1]["score"]


def test_save_and_load(tmp_path):
    store.save_index(VECTORS, CHUNKS, str(tmp_path))
    vectors, chunks = store.load_index(str(tmp_path))
    assert vectors.shape == (3, 3)
    assert chunks[2]["text"] == "cars"