# FILE: app/chunker.py
"""
Step 2 of RAG: cut long text into small pieces called "chunks".

Why? An LLM works better with a few short, relevant pieces than with a whole book.
We use an overlap so a sentence cut in half at the end of one chunk
also appears at the start of the next chunk.
"""


def split_text(text, chunk_size, overlap):
    """Split one text into pieces of about chunk_size characters."""
    if overlap >= chunk_size // 2:
        raise ValueError("overlap must be smaller than half of chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end]

        # Try not to cut a word in half: stop at the last space (if it is not too early)
        if end < len(text):
            last_space = piece.rfind(" ")
            if last_space > chunk_size // 2:
                piece = piece[:last_space]

        chunks.append(piece.strip())

        if end >= len(text):
            break
        # Move forward, but go back "overlap" characters
        start = start + len(piece) - overlap

    return chunks


def chunk_pages(pages, chunk_size, overlap):
    """Split every page into chunks and keep source + page for each chunk."""
    all_chunks = []
    for page in pages:
        pieces = split_text(page["text"], chunk_size, overlap)
        for piece in pieces:
            all_chunks.append({
                "id": len(all_chunks),
                "source": page["source"],
                "page": page["page"],
                "text": piece,
            })
    return all_chunks