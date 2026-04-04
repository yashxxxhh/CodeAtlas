"""
clone_worker.py — Step 1 of the CodeAtlas pipeline.

What it does:
    - Reads all Repository records with status=pending
    - For Git URLs: runs `git clone --depth=1`
    - For ZIP uploads: extracts the archive to disk
    - Updates local_path and sets status → cloned

Run:
    cd codeatlas
    python workers/clone_worker.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path

# Allow imports from the backend package
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import Repository, RepoStatus

logger = get_logger("clone_worker")


def extract_zip(zip_path: str, dest_dir: Path) -> None:
    """Extract a ZIP archive into dest_dir."""
    logger.info(f"  Extracting ZIP: {zip_path} → {dest_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Security: strip any absolute paths or .. traversal
        safe_members = [
            m for m in zf.namelist()
            if not m.startswith("/") and ".." not in m
        ]
        zf.extractall(dest_dir, members=safe_members)


def clone_git(url: str, dest_dir: Path) -> None:
    """Run git clone into dest_dir."""
    logger.info(f"  Cloning: {url} → {dest_dir}")
    result = subprocess.run(
        ["git", "clone", "--depth=1", url, str(dest_dir)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed:\n{result.stderr}")


def process_repo(repo: Repository) -> str:
    """Clone or extract one repo. Returns the local directory path."""
    repos_dir = Path(settings.data_dir) / "repos"
    dest_dir = repos_dir / f"repo_{repo.id}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if repo.source_url:
        clone_git(repo.source_url, dest_dir)
    elif repo.local_path and repo.local_path.endswith(".zip"):
        extract_zip(repo.local_path, dest_dir)
    else:
        raise ValueError(
            f"Repo {repo.id} has neither a Git URL nor a ZIP path. Cannot clone."
        )

    return str(dest_dir)


def run():
    db = SessionLocal()
    try:
        pending = (
            db.query(Repository)
            .filter(Repository.status == RepoStatus.pending)
            .all()
        )

        if not pending:
            logger.info("No pending repos found. Nothing to clone.")
            return

        logger.info(f"Found {len(pending)} pending repo(s).")

        for repo in pending:
            logger.info(f"Processing repo id={repo.id} name={repo.name!r}")
            try:
                local_path = process_repo(repo)
                repo.local_path = local_path
                repo.status = RepoStatus.cloned
                repo.error_msg = None
                logger.info(f"  ✓ Cloned → {local_path}")
            except Exception as e:
                repo.status = RepoStatus.failed
                repo.error_msg = str(e)
                logger.error(f"  ✗ Failed: {e}")
            finally:
                db.commit()

        logger.info("clone_worker finished.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
