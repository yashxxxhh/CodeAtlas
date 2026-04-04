"""
index_worker.py — Step 4 (final) of the CodeAtlas pipeline.

What it does:
    - Reads all Repository records with status=embedded
    - Loads the .npy embedding files saved by embedding_worker
    - Adds vectors to a FAISS index (creates it if it doesn't exist yet)
    - Maintains a chunk_id_map: list[int] where position = faiss_id
    - Saves the FAISS index and chunk_id_map to disk
    - Updates CodeChunk.faiss_id in the database
    - Sets status → indexed

FAISS index type: IndexFlatIP (Inner Product)
    - After L2 normalization, inner product = cosine similarity
    - Exact search (no approximation) — fine for <500k vectors
    - No training required

Run:
    cd codeatlas
    python workers/index_worker.py
"""

import json
import sys
from pathlib import Path

import faiss
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import CodeChunk, Repository, RepoStatus

logger = get_logger("index_worker")

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def load_or_create_index() -> tuple[faiss.Index, list[int]]:
    """
    Load the existing FAISS index from disk, or create a fresh one.
    Returns (index, chunk_id_map).
    chunk_id_map[i] = DB id of the chunk at FAISS position i.
    """
    index_path = settings.faiss_index_path
    map_path   = settings.chunk_id_map_path

    if Path(index_path).exists() and Path(map_path).exists():
        logger.info(f"Loading existing FAISS index: {index_path}")
        index = faiss.read_index(index_path)
        with open(map_path, "r") as f:
            chunk_id_map = json.load(f)
        logger.info(f"  Loaded {index.ntotal} existing vectors.")
    else:
        logger.info(f"Creating new FAISS IndexFlatIP (dim={EMBEDDING_DIM})")
        index = faiss.IndexFlatIP(EMBEDDING_DIM)
        chunk_id_map = []

    return index, chunk_id_map


def save_index(index: faiss.Index, chunk_id_map: list[int]) -> None:
    """Persist the FAISS index and chunk_id_map to disk."""
    Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, settings.faiss_index_path)
    with open(settings.chunk_id_map_path, "w") as f:
        json.dump(chunk_id_map, f)
    logger.info(f"  Saved FAISS index ({index.ntotal} total vectors) → {settings.faiss_index_path}")


def index_repo(repo: Repository, db) -> int:
    """
    Add one repo's embeddings to the FAISS index.
    Returns the number of vectors added.
    """
    base = Path(settings.data_dir) / "repos"
    embed_path = base / f"embeddings_{repo.id}.npy"
    ids_path   = base / f"chunk_ids_{repo.id}.npy"

    if not embed_path.exists():
        raise FileNotFoundError(
            f"Embeddings not found: {embed_path}\n"
            "Make sure embedding_worker ran successfully first."
        )

    embeddings   = np.load(str(embed_path)).astype("float32")
    chunk_db_ids = np.load(str(ids_path)).tolist()

    if embeddings.shape[0] == 0:
        logger.warning(f"  Empty embeddings for repo {repo.id}. Skipping.")
        return 0

    # Normalize vectors (in case embedding_worker didn't pre-normalize)
    faiss.normalize_L2(embeddings)

    index, chunk_id_map = load_or_create_index()

    # Assign FAISS positions starting from current total
    start_pos = index.ntotal
    new_faiss_ids = list(range(start_pos, start_pos + len(chunk_db_ids)))

    # Update DB records with their FAISS positions
    for chunk_db_id, faiss_id in zip(chunk_db_ids, new_faiss_ids):
        chunk = db.query(CodeChunk).filter(CodeChunk.id == int(chunk_db_id)).first()
        if chunk:
            chunk.faiss_id = faiss_id

    # Extend the chunk_id_map
    chunk_id_map.extend([int(x) for x in chunk_db_ids])

    # Add vectors to FAISS
    index.add(embeddings)

    db.commit()
    save_index(index, chunk_id_map)

    return len(chunk_db_ids)


def run():
    db = SessionLocal()
    try:
        repos = (
            db.query(Repository)
            .filter(Repository.status == RepoStatus.embedded)
            .all()
        )

        if not repos:
            logger.info("No embedded repos found. Nothing to index.")
            return

        logger.info(f"Found {len(repos)} embedded repo(s).")

        for repo in repos:
            logger.info(f"Indexing repo id={repo.id} name={repo.name!r}")
            try:
                count = index_repo(repo, db)
                repo.status = RepoStatus.indexed
                repo.error_msg = None
                logger.info(f"  ✓ Indexed {count} vectors")
            except Exception as e:
                repo.status = RepoStatus.failed
                repo.error_msg = str(e)
                logger.error(f"  ✗ Failed: {e}")
            finally:
                db.commit()

        logger.info("index_worker finished. Your repo is now searchable!")
    finally:
        db.close()


if __name__ == "__main__":
    run()
