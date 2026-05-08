# Incident Insight Agent

A production-pattern RAG (Retrieval-Augmented Generation) service that suggests resolutions for production incidents by retrieving similar past incidents from a vector store and grounding LLM output in that retrieved context.

Built as a learning project to demonstrate end-to-end LLM application engineering: prompt design, vector embeddings, semantic retrieval, RAG orchestration, and serving via a REST API.

---

## What it does

You give it a new incident description. It:
1. **Retrieves** the top 3 most semantically similar past incidents from a ChromaDB vector store
2. **Augments** the LLM prompt with those retrieved incidents as grounding context
3. **Generates** a concrete, technical resolution suggestion that cites the past incidents it drew from

Example:

```bash
$ curl -X POST http://localhost:8000/resolve \
  -H "Content-Type: application/json" \
  -d '{"description": "Payment service returning 500 errors, customers cannot checkout"}'
```

Returns:
```json
{
  "query": "Payment service returning 500 errors, customers cannot checkout",
  "resolution": "This sounds very similar to INC-001. My first action would be to check the database connection pool for the payment service. If exhausted, increase pool size and add a connection timeout, then restart payment-service pods.",
  "retrieved_incidents": [
    {"id": "INC-001", "title": "Payment API returning 500 errors"},
    {"id": "INC-009", "title": "Auth service 503 errors after deploy"},
    {"id": "INC-008", "title": "Search service returning stale results"}
  ]
}
```

---

## Architecture


┌──────────────────────────────────┐
              │  Client (curl / Swagger / app)   │
              └────────────────┬─────────────────┘
                               │ POST /resolve
                               ▼
              ┌──────────────────────────────────┐
              │  FastAPI service (src/api.py)    │
              │  Pydantic validation, OpenAPI    │
              └────────────────┬─────────────────┘
                               │ resolve_incident()
                               ▼
              ┌──────────────────────────────────┐
              │  RAG chain (src/rag_resolver.py) │
              │  LangChain LCEL pipeline         │
              └─────┬────────────────────────┬───┘
                    │                        │
              retrieve                  generate
                    │                        │
                    ▼                        ▼
          ┌─────────────────┐     ┌──────────────────┐
          │  ChromaDB       │     │  Gemini          │
          │  (gemini-       │     │  (gemini-2.5-    │
          │   embedding-    │     │   flash-lite)    │
          │   001)          │     │                  │
          └─────────────────┘     └──────────────────┘


---

## Tech stack

- **Python 3.12**
- **LangChain** — chain orchestration, prompt templates, LCEL
- **Google Gemini API** — `gemini-embedding-001` for embeddings, `gemini-2.5-flash-lite` for generation
- **ChromaDB** — local vector store for semantic retrieval
- **FastAPI** + **Uvicorn** — REST API + ASGI server
- **Pydantic** — request/response validation

---

## Running it locally

### 1. Clone and install

```bash
git clone https://github.com/Hari-TN/incident-insight-agent.git
cd incident-insight-agent

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure secrets

Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

```bash
cp .env.example .env
# then edit .env and paste your real key
```

### 3. Build the vector knowledge base

This embeds the 10 sample incidents into ChromaDB. Run once.

```bash
python src/build_kb.py
```

### 4. Run the API

```bash
uvicorn src.api:app --reload --port 8000 --host 0.0.0.0
```

Then open `http://localhost:8000/docs` to try it via Swagger UI.

---

## Project structure

incident-insight-agent/
├── src/
│   ├── init.py
│   ├── api.py              # FastAPI app: /resolve, /health endpoints
│   ├── rag_resolver.py     # RAG pipeline (retriever | prompt | LLM | parser)
│   ├── build_kb.py         # One-time script to seed ChromaDB
│   ├── search_kb.py        # CLI tool to test semantic search standalone
│   ├── hello_langchain.py  # Minimal first LangChain script (Phase 1)
│   └── incidents.py        # Sample incident data
├── chroma_db/              # ChromaDB persistent store (git-ignored)
├── .env                    # Secrets (git-ignored)
├── .env.example            # Template for .env
├── requirements.txt
└── README.md

---

## Design decisions worth noting

- **Model names live in env vars** (`CHAT_MODEL`, `EMBEDDING_MODEL`). LLM providers deprecate models frequently; this project actually hit two deprecations during development. Putting model IDs in config means a deprecation is a one-line ops change, not a code change.
- **Lazy singleton initialization** for the chain. The RAG chain (embeddings + DB connection + LLM client) is built once on first request and reused. Avoids rebuilding expensive resources on every API call.
- **Anti-hallucination prompt instruction.** The system prompt explicitly tells the model to say so honestly if the retrieved context isn't relevant, rather than inventing an answer. This was an actual debugging lesson — early in development the API returned hallucinated incident IDs because the retriever was silently returning empty results.
- **Absolute paths for the vector store.** `chroma_db/` is resolved relative to the source file's location, so the retriever works whether you launch from project root, from `src/`, or as an imported module from a web server.
- **Separation of library code from script code.** The CLI and the API both import from `rag_resolver.py`'s functions; the file's `__main__` block only fires when run directly. Standard Python idiom.

---

## What I'd add next

- Authentication / API keys for the `/resolve` endpoint
- Structured logging (currently using `print` for errors)
- Retry logic with exponential backoff around LLM calls (handles rate limits gracefully)
- Replace the in-process `Chroma` client with a hosted vector DB (Pinecone, Weaviate) for multi-instance deployment
- Real evaluation: a test set of incidents with expected retrieval matches, scored automatically
- Streaming responses (the LLM call currently blocks until complete)

---

## Author

Built by [Harishankaran Babu](https://www.linkedin.com/in/harishankaran-b-a23755289/) as a hands-on RAG learning project.