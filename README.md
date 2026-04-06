# CodeAtlas — Semantic Code Search Platform

> Search your entire codebase with plain English. No more grepping through files.



## What it does

CodeAtlas lets you search code the way you think about it — by describing what it does, not by remembering exact names or keywords.

You upload a repository, CodeAtlas reads and understands every function and class in it, and then you can search with natural language:

- "functions that validate JWT tokens"
- "class that manages database connection pooling"
- "recursive file system walker"
- "error handling middleware for HTTP requests"

It returns the most relevant code snippets ranked by semantic similarity — not keyword matches.

---

## How it works

When you submit a repository, CodeAtlas runs it through a four-stage pipeline:

Parse — every Python file is analysed using the AST (Abstract Syntax Tree) module, which extracts every function and class as an individual unit of code.

Embed — each unit is converted into a 384-dimensional vector using a local sentence-transformers model. This vector captures the *meaning* of the code, not just its text.

Index — all vectors are stored in a FAISS index, a high-speed similarity search engine that can find the closest matches to any query in milliseconds.

Search — when you type a query, it is embedded with the same model, and FAISS returns the top results by cosine similarity. Each result is enriched with the file path, function name, line number, and a code preview from PostgreSQL.

Everything runs locally. No code ever leaves your machine.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector search | FAISS |
| Frontend | React + Tailwind CSS |

---

## License

MIT