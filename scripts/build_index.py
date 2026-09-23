# FILE: scripts/build_index.py
"""
Run this once (and again every time you add or change PDFs):
    python -m scripts.build_index

It does: read PDFs -> cut into chunks -> make embeddings -> save the index.
"""
from app import config, llm, store
from app.chunker import chunk_pages
from app.loader import load_all_pdfs


def main():
    print("1/4 Reading PDFs from", config.DOCS_FOLDER)
    pages = load_all_pdfs(config.DOCS_FOLDER)
    if len(pages) == 0:
        print("No PDF text found. Put some PDF files in data/docs/ and try again.")
        return

    print("2/4 Cutting text into chunks")
    chunks = chunk_pages(pages, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    print(f"    {len(pages)} pages -> {len(chunks)} chunks")

    print("3/4 Creating embeddings (this can take a minute)")
    texts = [chunk["text"] for chunk in chunks]
    vectors = llm.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    print(f"    each vector has {len(vectors[0])} numbers")

    print("4/4 Saving the index to", config.INDEX_FOLDER)
    store.save_index(vectors, chunks, config.INDEX_FOLDER)
    print("Done!")


if __name__ == "__main__":
    main() 