"""
NEW in v2: what happens when a user uploads a file.

    check the file -> save it -> read text -> chunks -> embeddings -> save index -> add to database

It is the same pipeline as v1's build_index script, but for ONE file,
called by the API while the app is running.

Errors are raised as UploadError with an HTTP status code,
so main.py can send a clear message to the web page.
"""
import os
import uuid

from app import config, database, llm, store
from app.chunker import chunk_pages
from app.loader import count_pdf_pages, load_file


class UploadError(Exception):
    """A problem with the uploaded file that the user should see."""

    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def check_file(filename, content):
    """Reject files we do not want, BEFORE doing any expensive work."""
    extension = os.path.splitext(filename)[1].lower()
    if extension not in config.ALLOWED_EXTENSIONS:
        allowed = ", ".join(config.ALLOWED_EXTENSIONS)
        raise UploadError(415, f"File type '{extension}' is not supported. Allowed: {allowed}")

    if len(content) == 0:
        raise UploadError(422, "The file is empty.")

    if len(content) > config.MAX_FILE_MB * 1024 * 1024:
        raise UploadError(413, f"The file is larger than {config.MAX_FILE_MB} MB.")

    # A real PDF always starts with "%PDF". This catches files that are only renamed to .pdf
    if extension == ".pdf" and not content.startswith(b"%PDF"):
        raise UploadError(415, "This file is not a valid PDF.")

    return extension


def ingest_file(filename, content):
    """
    Full pipeline for one uploaded file.
    filename = the name chosen by the user (only shown, never used as a path)
    content  = the bytes of the file
    Returns the database record of the new document.
    """
    extension = check_file(filename, content)

    # 1. Save with a RANDOM name: a user could send a name like "../../app/main.py"
    doc_id = uuid.uuid4().hex
    os.makedirs(config.UPLOADS_FOLDER, exist_ok=True)
    saved_path = os.path.join(config.UPLOADS_FOLDER, doc_id + extension)
    with open(saved_path, "wb") as f:
        f.write(content)

    try:
        # 2. Page limit (for PDFs we can count pages before reading them)
        if extension == ".pdf" and count_pdf_pages(saved_path) > config.MAX_PAGES:
            raise UploadError(422, f"The PDF has more than {config.MAX_PAGES} pages.")

        # 3. Read the text
        try:
            pages = load_file(saved_path, filename)
        except UploadError:
            raise
        except Exception:
            raise UploadError(422, "The file could not be read. Is it damaged or password-protected?")

        if len(pages) == 0:
            raise UploadError(422, "No text found. Scanned PDFs (images) are not supported yet.")

        # 4. Chunks, with the document id in every chunk
        chunks = chunk_pages(pages, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        for chunk in chunks:
            chunk["document_id"] = doc_id

        # 5. Embeddings (the slow part: it calls the AI provider)
        texts = [chunk["text"] for chunk in chunks]
        vectors = llm.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

        # 6. Save the index and the database record
        store.save_document_index(doc_id, vectors, chunks)
        database.add_document(doc_id, filename, extension, len(pages), len(chunks))

    except Exception:
        # Something went wrong: remove what we created, so nothing half-finished stays
        if os.path.exists(saved_path):
            os.remove(saved_path)
        store.delete_document_index(doc_id)
        raise

    return database.get_document(doc_id)


def delete_document(doc_id):
    """Remove the file, its index and its database record. Returns False if it does not exist."""
    document = database.get_document(doc_id)
    if document is None:
        return False

    saved_path = os.path.join(config.UPLOADS_FOLDER, doc_id + document["file_type"])
    if os.path.exists(saved_path):
        os.remove(saved_path)
    store.delete_document_index(doc_id)
    database.delete_document(doc_id)
    return True