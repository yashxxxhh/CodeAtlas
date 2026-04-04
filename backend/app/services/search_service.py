"""
search_service.py — Core semantic search logic.

Steps:
  1. Load sentence-transformers model (once, cached in module scope)
  2. Load FAISS index + chunk_id map (once, cached in module scope)
  3. Embed the query string
  4. Search FAISS for top-k nearest vectors
  5. Map FAISS positions → DB chunk IDs
  6. Fetch CodeChunk + Repository metadata from Postgres
  7. Return ranked result list
"""

import json
from pathlib import Path
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import CodeChunk, Repository

logger = get_logger("search_service")

# Module-level singletons — loaded once per process, reused on every request
_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.Index] = None
_chunk_id_map: Optional[list] = None


def _load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Model loaded.")
    return _model


def _load_index() -> tuple:
    global _index, _chunk_id_map
    if _index is None:
        index_path = settings.faiss_index_path
        map_path = settings.chunk_id_map_path

        if not Path(index_path).exists():
            raise FileNotFoundError(
                "FAISS index not found. Please run all 4 workers first: "
                "clone_worker → parser_worker → embedding_worker → index_worker"
            )

        logger.info(f"Loading FAISS index from {index_path}")
        _index = faiss.read_index(index_path)

        with open(map_path, "r") as f:
            _chunk_id_map = json.load(f)

        logger.info(f"FAISS index loaded: {_index.ntotal} vectors")
    return _index, _chunk_id_map


def reload_index():
    """Force reload the FAISS index (call after index_worker runs)."""
    global _index, _chunk_id_map
    _index = None
    _chunk_id_map = None
    logger.info("FAISS index cache cleared — will reload on next search.")


def search_code(query: str, top_k: int, db: Session) -> list[dict]:
    """
    Run semantic search and return enriched results from DB.

    Args:
        query: Natural language search string
        top_k: Number of results to return
        db: SQLAlchemy session

    Returns:
        List of result dicts with chunk + repo metadata
    """
    model = _load_model()
    index, chunk_id_map = _load_index()

    if index.ntotal == 0:
        return []

    # Embed and normalize the query vector
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    # Clamp top_k to available vectors
    k = min(top_k, index.ntotal)

    # FAISS search returns distances and flat indices
    distances, indices = index.search(query_vec, k)

    results = []
    for dist, faiss_idx in zip(distances[0], indices[0]):
        if faiss_idx < 0 or faiss_idx >= len(chunk_id_map):
            continue  # FAISS pads with -1 when fewer results than k

        chunk_db_id = chunk_id_map[int(faiss_idx)]
        chunk: Optional[CodeChunk] = (
            db.query(CodeChunk).filter(CodeChunk.id == chunk_db_id).first()
        )
        if not chunk:
            continue

        repo: Optional[Repository] = (
            db.query(Repository).filter(Repository.id == chunk.repo_id).first()
        )

        results.append({
            "score": round(float(dist), 4),
            "chunk_id": chunk.id,
            "repo_id": chunk.repo_id,
            "repo_name": repo.name if repo else "unknown",
            "file_path": chunk.file_path,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "code": chunk.code,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        })

    return results
