"""
NEW in v2: a small SQLite database with ONE table: the list of uploaded documents.

The vectors are NOT stored here (they are in storage/index/<id>/).
Here we keep the "metadata": name, type, pages, chunks, upload time.

Table "documents":
    id          TEXT     random id, e.g. "3f2a9c..." (also the folder name in storage/index)
    filename    TEXT     the original name shown to the user
    file_type   TEXT     ".pdf", ".docx", ".txt", ".md"
    pages       INTEGER
    chunks      INTEGER
    uploaded_at TEXT     "2026-09-24 14:05:00"
"""
import os
import sqlite3

from app import config

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    pages       INTEGER NOT NULL,
    chunks      INTEGER NOT NULL,
    uploaded_at TEXT NOT NULL
)
"""


def get_connection():
    """Open the database (and create the table the first time)."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row   # rows behave like dictionaries: row["filename"]
    connection.execute(CREATE_TABLE)
    return connection


def add_document(doc_id, filename, file_type, pages, chunks):
    connection = get_connection()
    connection.execute(
        "INSERT INTO documents (id, filename, file_type, pages, chunks, uploaded_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))",
        (doc_id, filename, file_type, pages, chunks),   # "?" = safe placeholders (no SQL injection)
    )
    connection.commit()
    connection.close()


def list_documents():
    connection = get_connection()
    rows = connection.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_document(doc_id):
    connection = get_connection()
    row = connection.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    connection.close()
    if row is None:
        return None
    return dict(row)


def delete_document(doc_id):
    connection = get_connection()
    connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    connection.commit()
    connection.close()