# FILE: app/main.py
"""
The web API, made with FastAPI.

Run it with:
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs to try it in the browser.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import config, rag, store

app = FastAPI(
    title="Document Q&A Assistant",
    description="Ask questions about your PDF documents. Answers include citations.",
    version="1.0",
)

# The index is loaded once, the first time someone asks a question
index = {"vectors": None, "chunks": None}


def get_index():
    if index["vectors"] is None:
        vectors, chunks = store.load_index(config.INDEX_FOLDER)
        index["vectors"] = vectors
        index["chunks"] = chunks
    return index["vectors"], index["chunks"]


# Pydantic models describe (and check) the JSON that goes in and out of the API
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, examples=["What is the deadline to enroll?"])
    top_k: int = Field(default=config.TOP_K, ge=1, le=10)


class Source(BaseModel):
    number: int
    source: str
    page: int
    score: float
    preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    model: str
    seconds: float


@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {"status": "ok"}


@app.get("/stats")
def stats():
    """How many chunks and documents are in the index."""
    try:
        vectors, chunks = get_index()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))

    files = sorted(set(chunk["source"] for chunk in chunks))
    return {"chunks": len(chunks), "documents": files}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Ask a question. The answer uses only your documents and cites them."""
    try:
        vectors, chunks = get_index()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error))

    try:
        return rag.answer_question(request.question, vectors, chunks, request.top_k)
    except Exception as error:
        # For example: wrong API key, no internet, rate limit
        raise HTTPException(status_code=502, detail=f"LLM error: {error}")