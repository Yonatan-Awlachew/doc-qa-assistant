# Document Q&A Assistant (RAG API)

Ask questions about your own PDF documents and get short answers **with citations** (file + page).
Built with Python, FastAPI, Google Gemini (LLM + embeddings), NumPy and Docker.

## How it works

```
                     BUILD THE INDEX (once)
PDFs ──► read text per page ──► split into chunks ──► embeddings ──► data/index/
                                                                      (vectors.npy + chunks.json)

                     ANSWER A QUESTION (every request)
question ──► embedding ──► cosine similarity vs all chunks ──► top-k chunks
         ──► prompt (rules + numbered chunks + question) ──► LLM ──► answer with [1], [2] + sources
```

## Project structure

```
doc-qa-assistant/
├── app/
│   ├── config.py      # settings read from .env
│   ├── loader.py      # PDF -> text per page
│   ├── chunker.py     # text -> overlapping chunks
│   ├── llm.py         # Gemini calls: embeddings + answer generation
│   ├── store.py       # tiny NumPy vector store + cosine search
│   ├── rag.py         # retrieve -> build prompt -> generate
│   └── main.py        # FastAPI app: /health, /stats, /ask
├── scripts/
│   ├── build_index.py # builds the index from data/docs
│   └── ask_cli.py     # ask questions from the terminal
├── eval/
│   ├── questions.json # test questions with expected page + keywords
│   └── run_eval.py    # retrieval hit rate + answer pass rate
├── tests/             # pytest tests (Gemini is mocked, no key needed)
├── data/docs/         # put your PDFs here
├── data/index/        # generated index
├── Dockerfile
└── requirements.txt
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then paste your Gemini API key in .env

# put PDFs in data/docs/, then:
python -m scripts.build_index
uvicorn app.main:app --reload      # open http://127.0.0.1:8000/docs
```

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When does enrollment close?"}'
```

## Tests and evaluation

```bash
pytest                     # unit + API tests, no API key needed
python -m eval.run_eval    # quality on real questions (uses the API)
```

| Metric | Result |
|---|---|
| Retrieval hit rate | _fill in after running eval_ |
| Answer pass rate | _fill in after running eval_ |

## Docker

```bash
docker build -t doc-qa .
docker run -p 8000:8000 --env-file .env doc-qa
```

## Design choices

- **NumPy instead of a vector database**: a few thousand chunks fit in memory and search in milliseconds; a vector DB (Chroma, FAISS, pgvector) is the next step for larger collections.
- **Chunks of ~800 characters with 150 overlap**: small enough to be specific, big enough to keep context; overlap avoids losing sentences cut at a boundary.
- **Low temperature (0.1) + "answer only from context" rule**: reduces invented answers; the eval includes an out-of-scope question to check this.
- **All LLM calls in one file (`llm.py`)**: switching to OpenAI or a local model only changes that file.

## Limitations and next steps

- Scanned PDFs (images) have no text: they would need OCR.
- Keyword-based answer check is simple; an LLM-as-judge could grade answers better.
- Next: hybrid search (keywords + vectors), re-ranking, a small web UI, an n8n workflow calling `/ask`.