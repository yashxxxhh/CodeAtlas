"""
routes.py — All HTTP endpoints for CodeAtlas.

Endpoints:
  GET  /health              → Health check
  POST /upload              → Upload a ZIP file
  POST /register-git        → Register a Git URL
  GET  /status/{repo_id}    → Get processing status
  GET  /repos               → List all repositories
  GET  /chunks/{repo_id}    → List code chunks for a repo
  GET  /search              → Semantic code search
  POST /reload-index        → Force reload FAISS index cache
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import CodeChunk, Repository, RepoStatus
from app.services.search_service import reload_index, search_code

router = APIRouter()
logger = get_logger("routes")


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health", tags=["system"])
def health():
    """Simple liveness check."""
    return {"status": "ok", "service": "CodeAtlas"}


# ── Repository ingestion ───────────────────────────────────────────────────────

@router.post("/upload", tags=["repos"])
async def upload_repo(
    file: UploadFile = File(...),
    repo_name: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Accept a ZIP file upload.
    Saves to disk, creates a Repository record with status=pending.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are supported.")

    repos_dir = Path(settings.data_dir) / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)

    # Use a safe filename
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._-")
    save_path = repos_dir / safe_name

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    repo = Repository(
        name=repo_name.strip(),
        source_url=None,
        local_path=str(save_path),
        status=RepoStatus.pending,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    logger.info(f"Uploaded repo id={repo.id} name={repo.name!r} file={save_path}")
    return {
        "repo_id": repo.id,
        "name": repo.name,
        "status": repo.status,
        "message": "Upload successful. Run the 4 workers to process this repo.",
    }


@router.post("/register-git", tags=["repos"])
def register_git_repo(
    repo_name: str = Form(...),
    git_url: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Register a public Git URL (no upload needed).
    clone_worker will handle the actual git clone.
    """
    repo = Repository(
        name=repo_name.strip(),
        source_url=git_url.strip(),
        local_path=None,
        status=RepoStatus.pending,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    logger.info(f"Registered git repo id={repo.id} url={git_url!r}")
    return {
        "repo_id": repo.id,
        "name": repo.name,
        "status": repo.status,
        "message": "Git URL registered. Run the 4 workers to process this repo.",
    }


# ── Status & listing ───────────────────────────────────────────────────────────

@router.get("/status/{repo_id}", tags=["repos"])
def get_repo_status(repo_id: int, db: Session = Depends(get_db)):
    """Get current processing status for a specific repo."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository {repo_id} not found.")
    return {
        "repo_id": repo.id,
        "name": repo.name,
        "status": repo.status,
        "error": repo.error_msg,
        "created_at": repo.created_at,
        "updated_at": repo.updated_at,
    }


@router.get("/repos", tags=["repos"])
def list_repos(db: Session = Depends(get_db)):
    """List all repositories with their current status."""
    repos = db.query(Repository).order_by(Repository.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "status": r.status,
            "source_url": r.source_url,
            "chunk_count": len(r.chunks),
            "created_at": r.created_at,
        }
        for r in repos
    ]


@router.get("/chunks/{repo_id}", tags=["repos"])
def list_chunks(repo_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """List code chunks for a specific repo (for debugging/inspection)."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository {repo_id} not found.")

    chunks = (
        db.query(CodeChunk)
        .filter(CodeChunk.repo_id == repo_id)
        .limit(limit)
        .all()
    )
    return {
        "repo_id": repo_id,
        "repo_name": repo.name,
        "total_shown": len(chunks),
        "chunks": [
            {
                "id": c.id,
                "type": c.chunk_type,
                "name": c.name,
                "file": c.file_path,
                "line": c.start_line,
                "faiss_id": c.faiss_id,
            }
            for c in chunks
        ],
    }


# ── Search ─────────────────────────────────────────────────────────────────────

@router.get("/search", tags=["search"])
def search(
    query: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    """
    Semantic code search.
    Embeds the query, runs FAISS similarity search, returns enriched results.
    """
    query = query.strip()
    if not query:
        raise HTTPException(400, "Query cannot be empty.")

    top_k = max(1, min(top_k, settings.max_results))

    try:
        results = search_code(query=query, top_k=top_k, db=db)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(500, f"Search failed: {str(e)}")

    logger.info(f"Search: {query!r} → {len(results)} results")
    return {
        "query": query,
        "top_k": top_k,
        "count": len(results),
        "results": results,
    }


@router.post("/reload-index", tags=["system"])
def trigger_reload():
    """Force the search service to reload the FAISS index from disk."""
    reload_index()
    return {"message": "FAISS index cache cleared. Will reload on next search."}
