CodeAtlas – Semantic Code Search Platform

CodeAtlas is a developer-focused platform that allows you to search, explore, and analyze code across multiple repositories in a fast and intelligent way. It combines modern backend and frontend technologies with AI-powered embeddings to deliver accurate and relevant search results.

Features
Repository Ingestion: Upload ZIP files, clone Git repos, or connect Git accounts.
Code Parsing & Indexing: Automatically extracts functions, classes, and comments for searchable indexing.
Semantic Search: Uses embeddings and vector search to provide relevant code snippets and function-level results.
Modern UI: Responsive React interface with repository dashboard, search results panel, and code preview.
Extensible Architecture: Clean modular backend built with FastAPI and PostgreSQL, designed for scaling and adding more AI features.
Tech Stack
Backend: FastAPI, Python, PostgreSQL, SQLAlchemy
Frontend: React, Tailwind CSS
AI: Embedding models, vector database for semantic search
Workers: Asynchronous processing for repository ingestion, parsing, and indexing
Getting Started
Clone the repository.
Set up .env and settings.yaml for database and storage paths.
Run uvicorn main:app --reload for local development.
Access the frontend to upload repositories and search code.
