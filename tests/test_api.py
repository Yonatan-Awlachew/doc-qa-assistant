"""
API tests for v2: upload, list, delete, ask.
They use the fake AI (see conftest.py) and a temporary storage folder.
"""
from fastapi.testclient import TestClient

from app import config, main

client = TestClient(main.app)

SAMPLE_PDF = "samples/example_regulations.pdf"


def upload(filename, content):
    return client.post("/documents", files={"file": (filename, content)})


def upload_sample_pdf():
    with open(SAMPLE_PDF, "rb") as f:
        return upload("regulations.pdf", f.read())


# ---------- pages ----------

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Document Q&amp;A Assistant" in response.text


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


# ---------- upload ----------

def test_upload_pdf(fake_ai):
    response = upload_sample_pdf()
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "regulations.pdf"
    assert data["pages"] == 3
    assert data["chunks"] >= 3


def test_upload_txt(fake_ai):
    response = upload("notes.txt", b"The meeting is on Friday at 10.")
    assert response.status_code == 201
    assert response.json()["file_type"] == ".txt"


def test_wrong_file_type_is_rejected(fake_ai):
    response = upload("photo.png", b"12345")
    assert response.status_code == 415


def test_fake_pdf_is_rejected(fake_ai):
    response = upload("virus.pdf", b"this is not a pdf")
    assert response.status_code == 415


def test_empty_file_is_rejected(fake_ai):
    assert upload("empty.txt", b"").status_code == 422


def test_too_big_file_is_rejected(fake_ai, monkeypatch):
    monkeypatch.setattr(config, "MAX_FILE_MB", 0)       # every file is now "too big"
    assert upload("notes.txt", b"hello").status_code == 413


# ---------- list and delete ----------

def test_list_and_delete(fake_ai):
    doc_id = upload_sample_pdf().json()["id"]
    upload("notes.txt", b"Some notes about exams.")

    documents = client.get("/documents").json()
    assert len(documents) == 2

    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert len(client.get("/documents").json()) == 1
    assert client.delete(f"/documents/{doc_id}").status_code == 404   # already deleted


# ---------- ask ----------

def test_ask_returns_answer_and_sources(fake_ai):
    upload_sample_pdf()
    response = client.post("/ask", json={"question": "When does enrollment close?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "FAKE ANSWER [1]"
    assert data["sources"][0]["source"] == "regulations.pdf"
    assert data["model"] != ""        # the response says which model answered
    assert data["seconds"] >= 0       # and how long it took


def test_ask_only_in_selected_documents(fake_ai):
    upload_sample_pdf()
    notes_id = upload("notes.txt", b"The meeting is on Friday at 10.").json()["id"]

    response = client.post("/ask", json={"question": "When is the meeting?", "document_ids": [notes_id]})
    sources = response.json()["sources"]
    assert len(sources) > 0
    for source in sources:
        assert source["document_id"] == notes_id        # nothing from the PDF


def test_ask_without_documents(fake_ai):
    response = client.post("/ask", json={"question": "Anything here?"})
    assert response.status_code == 400


def test_question_too_short():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422