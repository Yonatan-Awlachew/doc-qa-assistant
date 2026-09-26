"""
Step 3 of RAG: the vector store.

v1: ONE big index for all documents (rebuilt every time).
v2: ONE small index PER DOCUMENT, in storage/index/<document id>/
      vectors.npy  -> one row of numbers per chunk
      chunks.json  -> text, file name, page of each chunk (same order)
So we can add or delete one document without touching the others,
and search only in the documents the user selected.
"""
import json
import os
import shutil

import numpy as np

from app import config


def document_folder(doc_id):
    return os.path.join(config.INDEX_FOLDER, doc_id)


def save_document_index(doc_id, vectors, chunks):
    folder = document_folder(doc_id)
    os.makedirs(folder, exist_ok=True)
    np.save(os.path.join(folder, "vectors.npy"), np.array(vectors, dtype="float32"))
    with open(os.path.join(folder, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)


def delete_document_index(doc_id):
    folder = document_folder(doc_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)   # delete the folder and everything inside


def load_documents(doc_ids):
    """
    Load the indexes of several documents and put them together,
    so we can search them all at once.
    """
    all_vectors = []
    all_chunks = []
    for doc_id in doc_ids:
        folder = document_folder(doc_id)
        if not os.path.exists(folder):
            continue
        all_vectors.append(np.load(os.path.join(folder, "vectors.npy")))
        with open(os.path.join(folder, "chunks.json"), "r", encoding="utf-8") as f:
            all_chunks.extend(json.load(f))

    if len(all_vectors) == 0:
        return None, []
    return np.vstack(all_vectors), all_chunks   # vstack = put the tables one under the other


def cosine_similarity(query_vector, all_vectors):
    """
    Cosine similarity = how much two vectors point in the same direction.
    1.0 = same meaning, 0 = unrelated. Returns one score per chunk.
    """
    query = np.array(query_vector, dtype="float32")
    dot_products = all_vectors @ query
    norms = np.linalg.norm(all_vectors, axis=1) * np.linalg.norm(query)
    return dot_products / (norms + 1e-10)


def search(query_vector, vectors, chunks, top_k):
    """Return the top_k most similar chunks, each with its score."""
    scores = cosine_similarity(query_vector, vectors)
    best_positions = np.argsort(scores)[::-1][:top_k]

    results = []
    for position in best_positions:
        chunk = dict(chunks[position])
        chunk["score"] = round(float(scores[position]), 4)
        results.append(chunk)
    return results