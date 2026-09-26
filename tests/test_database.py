"""Tests for the SQLite documents table (uses a temporary database)."""
from app import database


def test_add_list_get_delete():
    database.add_document("id1", "a.pdf", ".pdf", 3, 10)
    database.add_document("id2", "b.txt", ".txt", 1, 2)

    documents = database.list_documents()
    assert len(documents) == 2

    doc = database.get_document("id1")
    assert doc["filename"] == "a.pdf"
    assert doc["pages"] == 3

    database.delete_document("id1")
    assert database.get_document("id1") is None
    assert len(database.list_documents()) == 1


def test_unknown_document_is_none():
    assert database.get_document("does-not-exist") is None