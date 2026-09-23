# FILE: tests/test_chunker.py
"""Tests for the chunker. Run all tests with:  pytest"""
import pytest

from app.chunker import chunk_pages, split_text


def test_short_text_is_one_chunk():
    chunks = split_text("hello world", chunk_size=100, overlap=10)
    assert chunks == ["hello world"]


def test_long_text_gives_many_chunks_of_right_size():
    text = "word " * 1000  # 5000 characters
    chunks = split_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 5
    for chunk in chunks:
        assert len(chunk) <= 500


def test_chunks_overlap():
    text = " ".join(f"w{i}" for i in range(500))
    chunks = split_text(text, chunk_size=200, overlap=50)
    # the end of chunk 0 must appear again at the start of chunk 1
    last_word_of_first = chunks[0].split()[-1]
    assert last_word_of_first in chunks[1]


def test_no_text_is_lost():
    text = " ".join(f"w{i}" for i in range(500))
    chunks = split_text(text, chunk_size=200, overlap=50)
    all_text = " ".join(chunks)
    for i in range(500):
        assert f"w{i}" in all_text


def test_bad_overlap_raises_error():
    with pytest.raises(ValueError):
        split_text("abc", chunk_size=100, overlap=80)


def test_chunk_pages_keeps_source_and_page():
    pages = [{"source": "a.pdf", "page": 2, "text": "some text " * 200}]
    chunks = chunk_pages(pages, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert chunks[0]["source"] == "a.pdf"
    assert chunks[0]["page"] == 2
    assert chunks[1]["id"] == 1