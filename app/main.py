"""
The web API (v2: users upload their own documents).

Run it with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
Then open:
    http://127.0.0.1:8000        -> the web page
    http://127.0.0.1:8000/docs   -> the API documentation

Endpoints:
    GET    /health
    POST   /documents          upload one file (multipart/form-data)
    GET    /documents          list uploaded documents
    DELETE /documents/{id}     delete one document
    POST   /ask                ask a question (optionally only in some documents)
"""
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config, database, ingest, rag

app = FastAPI(
    title="Document Q&A Assistant",
    description="Upload documents and ask questions about them. Answers include citations.",
    version="2.0",
)

# Serve frontend/style.css and frontend/app.js at /static/style.css and /static/app.js
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ---------- data shapes (Pydantic checks the JSON that goes in and out) ----------

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    pages: int
    chunks: int
    uploaded_at: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, examples=["What is the deadline to enroll?"])
    top_k: int = Field(default=config.TOP_K, ge=1, le=10)
    document_ids: Optional[list[str]] = None   # None = search all documents


class Source(BaseModel):
    number: int
    document_id: str
    source: str
    page: int
    score: float
    preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    model: str       # which AI model wrote the answer
    seconds: float   # total time: search + answer


# ---------- pages ----------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- documents ----------

@app.post("/documents", response_model=DocumentInfo, status_code=201)
def upload_document(file: UploadFile = File(...)):
    """Upload one PDF, DOCX, TXT or MD file. It is indexed immediately."""
    # Read at most MAX_FILE_MB + 1 byte: enough to know if the file is too big
    content = file.file.read(config.MAX_FILE_MB * 1024 * 1024 + 1)
    try:
        return ingest.ingest_file(file.filename or "file", content)
    except ingest.UploadError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    except Exception as error:
        # For example: embedding provider down, wrong API key
        raise HTTPException(status_code=502, detail=f"Indexing failed: {error}")


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents():
    return database.list_documents()


@app.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str):
    if not ingest.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    # 204 = "No Content": success, nothing to send back


# ---------- questions ----------

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Ask a question. With document_ids, only those documents are searched."""
    try:
        return rag.ask(request.question, request.document_ids, request.top_k)
    except rag.NoDocumentsError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"LLM error: {error}")