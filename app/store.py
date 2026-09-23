# FILE: app/store.py
"""
Step 3 of RAG: a tiny "vector database" made with NumPy.

We save:
  - vectors.npy  -> one row of numbers per chunk
  - chunks.json  -> the text, file name and page of each chunk (same order)

To search, we compare the question vector with every chunk vector
using cosine similarity and keep the most similar chunks.
Real projects use Chroma, FAISS, pgvector... but the idea is exactly this.
"""
import json
import os
import numpy as np


def save_index(vectors, chunks, folder):
    os.makedirs(folder, exist_ok=True)
    np.save(os.path.join(folder, "vectors.npy"), np.array(vectors, dtype="float32"))
    with open(os.path.join(folder, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def load_index(folder):
    vectors_path = os.path.join(folder, "vectors.npy")
    chunks_path = os.path.join(folder, "chunks.json")
    if not os.path.exists(vectors_path) or not os.path.exists(chunks_path):
        raise FileNotFoundError("Index not found. Run: python -m scripts.build_index")

    vectors = np.load(vectors_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return vectors, chunks


def cosine_similarity(query_vector, all_vectors):
    """
    Cosine similarity = how much two vectors point in the same direction.
    1.0 = same meaning, 0 = unrelated.
    Returns one score per chunk.
    """
    query = np.array(query_vector, dtype="float32")
    dot_products = all_vectors @ query
    norms = np.linalg.norm(all_vectors, axis=1) * np.linalg.norm(query)
    return dot_products / (norms + 1e-10)  # + tiny number to never divide by zero


def search(query_vector, vectors, chunks, top_k):
    """Return the top_k most similar chunks, each with its score."""
    scores = cosine_similarity(query_vector, vectors)
    best_positions = np.argsort(scores)[::-1][:top_k]  # sort from highest to lowest

    results = []
    for position in best_positions:
        chunk = dict(chunks[position])  # copy, so we do not change the original
        chunk["score"] = round(float(scores[position]), 4)
        results.append(chunk)
    return results