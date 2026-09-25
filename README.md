# Document Q&A Assistant (RAG API)

Ask questions about your own PDF documents and get short answers **with citations** (file + page).
Built with Python, FastAPI, NumPy and Docker. The AI provider is chosen in `.env`: Google Gemini, or any OpenAI-compatible service (Groq, OpenRouter, Mistral, Ollama...).

## How it works

```
                     BUILD THE INDEX (once)
PDFs ──► read text per page ──► split into chunks ──► embeddings ──► data/index/
                                                                      (vectors.npy + chunks.json)

                     ANSWER A QUESTION (every request)
question ──► embedding ──► cosine similarity vs all chunks ──► top-k chunks
         ──► prompt (rules + numbered chunks + question) ──► LLM ──► answer with [1], [2] + sources
```

## Features

- **Answers with citations**: every fact points to a numbered source (file + page).
- **"I could not find this"**: the model must answer only from the documents.
- **Web page** at `/` and interactive API docs at `/docs`.
- **Switch AI provider without touching the code**: Gemini or any OpenAI-compatible API, set in `.env`.
- **Automatic retry** on temporary errors (503 overloaded, 429 rate limit).
- **Transparent answers** (v1.1): each answer shows which model wrote it and how long it took; the temperature is configurable.

## Project structure

```
doc-qa-assistant/
├── app/
│   ├── config.py      # settings read from .env
│   ├── loader.py      # PDF -> text per page
│   ├── chunker.py     # text -> overlapping chunks
│   ├── llm.py         # AI calls (Gemini or OpenAI-compatible): embeddings + answers + retry
│   ├── store.py       # tiny NumPy vector store + cosine search
│   ├── rag.py         # retrieve -> build prompt -> generate
│   └── main.py        # FastAPI app: /, /health, /stats, /ask
├── static/
│   └── index.html     # simple web page to ask questions
├── scripts/
│   ├── build_index.py # builds the index from data/docs
│   └── ask_cli.py     # ask questions from the terminal
├── eval/
│   ├── questions.json # test questions with expected page + keywords
│   └── run_eval.py    # retrieval hit rate + answer pass rate
├── tests/             # pytest tests (the AI is mocked, no key needed)
├── data/docs/         # put your PDFs here
├── data/index/        # generated index
├── start.sh           # starts the server on port 8000
├── .env.example       # copy to .env and add your key(s)
├── Dockerfile
└── requirements.txt
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then paste your API key(s) in .env

# put PDFs in data/docs/, then:
python -m scripts.build_index
./start.sh                         # or: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:
- http://127.0.0.1:8000 → web page
- http://127.0.0.1:8000/docs → API documentation

Example request:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "When does enrollment close?"}'
```

Example response (shortened):

```json
{
  "question": "When does enrollment close?",
  "answer": "Enrollment closes on 30 September [1].",
  "sources": [{"number": 1, "source": "guide.pdf", "page": 4, "score": 0.83, "preview": "..."}],
  "model": "gemini-3.5-flash",
  "seconds": 1.42
}
```

## Choose the AI provider

Everything is set in `.env`, no code changes needed. Examples:

| Setup | `.env` lines |
|---|---|
| Gemini for everything (default) | `CHAT_PROVIDER=gemini`, `CHAT_MODEL=gemini-3.5-flash`, `GEMINI_API_KEY=...` |
| Groq for chat + Gemini for embeddings | `CHAT_PROVIDER=openai`, `CHAT_BASE_URL=https://api.groq.com/openai/v1`, `CHAT_API_KEY=...`, `CHAT_MODEL=openai/gpt-oss-120b` |

Other options (OpenRouter, Mistral, Ollama, OpenAI) are in `.env.example`.
`CHAT_TEMPERATURE` (default `0.1`) controls how creative the answers are: 0 = most factual.

> If you change the **embedding** provider or model, rebuild the index with `python -m scripts.build_index` (vectors from different models cannot be compared).

Model names change over time: check the provider's model list if you get a "model not found" error.

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
- **All AI calls in one file (`llm.py`)**: chat and embeddings can use different providers; switching provider or model is a `.env` change.
- **Retry only on temporary errors**: 503/429 are retried (2 s, then 4 s); a wrong key or model fails at once with a clear message.
- **Model name and response time in every answer**: makes it easy to compare providers (for example Gemini vs Groq) on the same questions.

## Limitations and next steps

- Scanned PDFs (images) have no text: they would need OCR.
- Keyword-based answer check is simple; an LLM-as-judge could grade answers better.
- Documents are fixed (indexed before the app starts). Next: upload documents from the web page (v2).
- Next: hybrid search (keywords + vectors), re-ranking, an n8n workflow calling `/ask`.