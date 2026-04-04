"""
embedding_worker.py — Step 3 of the CodeAtlas pipeline.

What it does:
    - Reads all Repository records with status=parsed
    - Loads all CodeChunk rows for each repo
    - Builds a text string for each chunk (type + name + file + code)
    - Encodes them with sentence-transformers (local, free, ~80MB download once)
    - Saves embeddings to disk as numpy arrays for index_worker
    - Sets status → embedded

Embedding model: all-MiniLM-L6-v2
    - 384-dimensional vectors
    - Fast, small, excellent at semantic similarity
    - Downloads automatically on first run

Run:
    cd codeatlas
    python workers/embedding_worker.py
"""

import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import CodeChunk, Repository, RepoStatus

logger = get_logger("embedding_worker")

# Global model cache — loaded once, reused for all repos
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading model: {settings.embedding_model}")
        logger.info("  (First run: model will download ~80MB — this is normal)")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("  Model ready.")
    return _model


def build_text_for_chunk(chunk: CodeChunk) -> str:
    """
    Combine metadata + code into a single string for embedding.

    Why include metadata?
        Pure code embedding often misses intent. Adding the function name,
        type, and file path gives the model extra semantic signal — especially
        helpful for short functions with descriptive names.
    """
    return (
        f"{chunk.chunk_type}: {chunk.name}\n"
        f"file: {chunk.file_path}\n"
        f"---\n"
        f"{chunk.code}"
    )


def embed_repo(repo: Repository, db) -> tuple[int, Path, Path]:
    """
    Embed all chunks for one repo.
    Saves results to disk and returns (chunk_count, embed_path, ids_path).
    """
    chunks = (
        db.query(CodeChunk)
        .filter(CodeChunk.repo_id == repo.id)
        .all()
    )

    if not chunks:
        logger.warning(f"  No chunks found for repo {repo.id}. Skipping.")
        return 0, None, None

    logger.info(f"  Encoding {len(chunks)} chunks...")
    model = get_model()

    texts = [build_text_for_chunk(c) for c in chunks]

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # Pre-normalize so FAISS uses cosine similarity
    )

    # Save embeddings and corresponding DB IDs to disk
    base = Path(settings.data_dir) / "repos"
    embed_path = base / f"embeddings_{repo.id}.npy"
    ids_path   = base / f"chunk_ids_{repo.id}.npy"

    np.save(str(embed_path), embeddings.astype("float32"))
    np.save(str(ids_path),   np.array([c.id for c in chunks], dtype=np.int64))

    logger.info(f"  Saved embeddings ({embeddings.shape}) → {embed_path}")
    return len(chunks), embed_path, ids_path


def run():
    db = SessionLocal()
    try:
        repos = (
            db.query(Repository)
            .filter(Repository.status == RepoStatus.parsed)
            .all()
        )

        if not repos:
            logger.info("No parsed repos found. Nothing to embed.")
            return

        logger.info(f"Found {len(repos)} parsed repo(s).")

        for repo in repos:
            logger.info(f"Embedding repo id={repo.id} name={repo.name!r}")
            try:
                count, _, _ = embed_repo(repo, db)
                repo.status = RepoStatus.embedded
                repo.error_msg = None
                logger.info(f"  ✓ Embedded {count} chunks")
            except Exception as e:
                repo.status = RepoStatus.failed
                repo.error_msg = str(e)
                logger.error(f"  ✗ Failed: {e}")
            finally:
                db.commit()

        logger.info("embedding_worker finished.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
