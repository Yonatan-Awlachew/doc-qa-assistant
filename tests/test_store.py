"""Tests for the per-document vector store. No API key needed."""
import numpy as np

from app import store


def test_cosine_similarity_values():
    vectors = np.array([[1, 0, 0], [0, 1, 0]], dtype="float32")
    scores = store.cosine_similarity([1, 0, 0], vectors)
    assert round(float(scores[0]), 3) == 1.0
    assert round(float(scores[1]), 3) == 0.0


def test_save_and_load_several_documents():
    store.save_document_index("doc1", [[1, 0], [0, 1]], [{"text": "a"}, {"text": "b"}])
    store.save_document_index("doc2", [[1, 1]], [{"text": "c"}])

    vectors, chunks = store.load_documents(["doc1", "doc2"])
    assert vectors.shape == (3, 2)                      # 2 + 1 rows, put together
    assert [c["text"] for c in chunks] == ["a", "b", "c"]

    vectors, chunks = store.load_documents(["doc2"])    # only one document
    assert len(chunks) == 1


def test_delete_document_index():
    store.save_document_index("doc1", [[1, 0]], [{"text": "a"}])
    store.delete_document_index("doc1")
    vectors, chunks = store.load_documents(["doc1"])
    assert vectors is None
    assert chunks == []


def test_search_returns_most_similar_first():
    vectors = np.array([[1, 0], [0, 1]], dtype="float32")
    chunks = [{"text": "cats"}, {"text": "dogs"}]
    results = store.search([0.1, 0.9], vectors, chunks, top_k=1)
    assert results[0]["text"] == "dogs"