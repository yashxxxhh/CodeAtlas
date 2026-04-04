# ⬡ CodeAtlas — Semantic Code Search Platform

Search your codebase with plain English.  
Upload a repo → parse it → generate embeddings → search with natural language.

**Entirely free. No paid APIs. Runs 100% locally.**

---

## What it does

1. You upload a ZIP file or provide a public Git URL
2. Four workers process it: clone → parse → embed → index
3. You search with natural language: *"functions that validate JWT tokens"*
4. CodeAtlas returns ranked results with file path, line number, and code preview

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Workers | Plain Python scripts |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector store | FAISS (local, in-process) |
| Frontend | React + Tailwind CSS + Vite |

---

## Project structure

```
codeatlas/
├── backend/
│   └── app/
│       ├── api/routes.py          # HTTP endpoints
│       ├── core/config.py         # Settings from .env
│       ├── core/logging.py        # Shared logger
│       ├── db/database.py         # SQLAlchemy engine + session
│       ├── db/models.py           # Repository + CodeChunk ORM models
│       ├── services/search_service.py  # FAISS search logic
│       └── main.py                # FastAPI app entry point
│
├── workers/
│   ├── clone_worker.py            # Step 1: git clone / unzip
│   ├── parser_worker.py           # Step 2: AST-extract functions/classes
│   ├── embedding_worker.py        # Step 3: sentence-transformers
│   └── index_worker.py            # Step 4: FAISS upsert
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── SearchBar.jsx
│           ├── ResultsList.jsx
│           ├── CodePreview.jsx    # Syntax-highlighted preview
│           ├── UploadRepo.jsx
│           └── RepoList.jsx       # Status tracker with pipeline progress
│
├── configs/.env                   # Environment variables
├── data/repos/                    # Cloned repos + .npy embedding files
├── data/faiss_index/              # FAISS index + chunk ID map
├── run_pipeline.py                # Run all 4 workers at once
├── requirements.txt
└── docker-compose.yml             # PostgreSQL
```

---

## Quick start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL) — or a local Postgres install

---

### Step 1 — Start PostgreSQL

```bash
docker compose up -d postgres
```

Wait for it to be healthy:

```bash
docker compose ps
```

---

### Step 2 — Install Python dependencies

```bash
# From the codeatlas/ root directory
pip install -r requirements.txt
```

The `sentence-transformers` model (~80MB) downloads automatically on first use.

---

### Step 3 — Start the backend API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify it's running:
```
http://localhost:8000/api/health
http://localhost:8000/docs          ← Swagger UI
```

---

### Step 4 — Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:5173**

---

### Step 5 — Add a repository

**Option A: via the UI**
1. Click "Upload Repo" in the nav
2. Upload a `.zip` file of your project, or paste a public Git URL
3. Submit

**Option B: via API**
```bash
# ZIP upload
curl -X POST http://localhost:8000/api/upload \
  -F "file=@myproject.zip" \
  -F "repo_name=myproject"

# Git URL
curl -X POST http://localhost:8000/api/register-git \
  -F "repo_name=flask" \
  -F "git_url=https://github.com/pallets/flask.git"
```

---

### Step 6 — Run the pipeline

**Option A: Run all workers at once**
```bash
# From codeatlas/ root
python run_pipeline.py
```

**Option B: Run workers individually (for debugging)**
```bash
python workers/clone_worker.py
python workers/parser_worker.py
python workers/embedding_worker.py
python workers/index_worker.py
```

Workers print their progress to stdout. Each worker sets the repo's status:
`pending → cloned → parsed → embedded → indexed`

---

### Step 7 — Search

Go to **http://localhost:5173** and type a natural language query:

- *"functions that handle HTTP authentication"*
- *"class that manages database connection pooling"*
- *"recursive tree traversal"*
- *"error handling and logging middleware"*

Or via API:
```bash
curl "http://localhost:8000/api/search?query=parse+jwt+token&top_k=5"
```

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/upload` | Upload a ZIP repo |
| `POST` | `/api/register-git` | Register a Git URL |
| `GET` | `/api/repos` | List all repos + status |
| `GET` | `/api/status/{id}` | Get repo status |
| `GET` | `/api/chunks/{id}` | List code chunks for a repo |
| `GET` | `/api/search?query=...&top_k=5` | Semantic search |
| `POST` | `/api/reload-index` | Reload FAISS index from disk |

---

## How it works (data flow)

```
Upload ZIP / Git URL
  ↓
Repository row created (status=pending)
  ↓
clone_worker
  → extracts ZIP or runs git clone
  → status = cloned
  ↓
parser_worker
  → walks .py files
  → ast.parse() → extracts functions and classes
  → creates CodeChunk rows in Postgres
  → status = parsed
  ↓
embedding_worker
  → loads sentence-transformers model
  → encodes each chunk as a 384-dim float32 vector
  → saves embeddings_{id}.npy + chunk_ids_{id}.npy
  → status = embedded
  ↓
index_worker
  → loads FAISS IndexFlatIP
  → L2-normalizes vectors (→ cosine similarity)
  → adds vectors to index
  → updates CodeChunk.faiss_id in DB
  → saves index.faiss + chunk_ids.json
  → status = indexed

Search query
  → embed query with same model
  → FAISS top-k similarity search
  → map faiss positions → DB chunk IDs
  → fetch CodeChunk + Repository from Postgres
  → return ranked results
```

---

## Configuration

Edit `configs/.env`:

```env
DATA_DIR=./data
FAISS_INDEX_PATH=./data/faiss_index/index.faiss
CHUNK_ID_MAP_PATH=./data/faiss_index/chunk_ids.json
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_RESULTS=10
```

---

## Extending CodeAtlas

| Feature | How |
|---|---|
| Support JS/TS | Add a Tree-sitter parser in `parser_worker.py` |
| Auto-run workers | Add Celery + Redis; trigger from the upload endpoint |
| Better search | Add BM25 hybrid search + RRF reranking |
| Auth | Add FastAPI middleware + JWT |
| Larger scale | Switch `IndexFlatIP` to `IndexIVFFlat` for ANN search |
| More languages | Add parsers for Go, Java, Rust using tree-sitter |

---

## Troubleshooting

**"FAISS index not found"**
→ Run all 4 workers after uploading a repo.

**"git clone failed"**
→ Check the URL is public. Private repos need SSH key setup.

**Embeddings take a long time**
→ Normal on first run (model download). Subsequent runs are fast.

**CORS errors in browser**
→ Make sure the backend is running on port 8000. The Vite proxy handles `/api`.

**Postgres connection error**
→ Run `docker compose up -d postgres` and wait 10s for it to initialize.
