"""
parser_worker.py — Step 2 of the CodeAtlas pipeline.

What it does:
    - Reads all Repository records with status=cloned
    - Walks every .py file in the repo directory
    - Uses Python's `ast` module to extract:
        * Function definitions (def / async def)
        * Class definitions
    - Creates one CodeChunk DB row per extracted unit
    - Sets status → parsed

Why AST instead of regex?
    The ast module understands Python syntax: it handles decorators,
    multiline signatures, nested functions, and gives exact line numbers.
    Regex breaks on edge cases. AST doesn't.

Run:
    cd codeatlas
    python workers/parser_worker.py
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import CodeChunk, Repository, RepoStatus

logger = get_logger("parser_worker")

# Directories to skip when walking the repo
SKIP_DIRS = {
    "venv", ".venv", "env", ".env",
    "__pycache__", ".git", ".hg", ".svn",
    "node_modules", "dist", "build", ".tox",
    "site-packages", "eggs", ".eggs",
}


def should_skip(path: Path) -> bool:
    """Return True if any part of the path is in SKIP_DIRS."""
    return any(part in SKIP_DIRS for part in path.parts)


def extract_chunks_from_file(
    file_path: Path,
    repo_root: Path,
) -> list[dict]:
    """
    Parse one .py file and return a list of chunk dicts.
    Each dict maps directly to CodeChunk column names.
    """
    chunks = []
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"    Cannot read {file_path}: {e}")
        return []

    relative_path = str(file_path.relative_to(repo_root))
    lines = source.splitlines()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        logger.warning(f"    Syntax error in {relative_path}: {e}")
        return []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
        start = node.lineno - 1  # ast is 1-indexed, lines list is 0-indexed
        end   = getattr(node, "end_lineno", min(start + 50, len(lines)))

        # Grab the source lines for this node
        code_snippet = "\n".join(lines[start:end])

        # Skip very short stubs (probably pass-only)
        if len(code_snippet.strip()) < 10:
            continue

        chunks.append({
            "file_path":  relative_path,
            "chunk_type": chunk_type,
            "name":       node.name,
            "code":       code_snippet,
            "start_line": node.lineno,
            "end_line":   end,
        })

    return chunks


def parse_repo(repo: Repository, db) -> int:
    """
    Walk all .py files in repo.local_path, extract chunks, insert into DB.
    Returns the number of chunks created.
    """
    repo_path = Path(repo.local_path)
    if not repo_path.exists():
        raise FileNotFoundError(f"Repo directory not found: {repo_path}")

    py_files = [
        f for f in repo_path.rglob("*.py")
        if not should_skip(f.relative_to(repo_path))
    ]
    logger.info(f"  Found {len(py_files)} Python file(s)")

    total = 0
    batch = []

    for py_file in py_files:
        file_chunks = extract_chunks_from_file(py_file, repo_path)
        for chunk_data in file_chunks:
            batch.append(CodeChunk(repo_id=repo.id, **chunk_data))
        total += len(file_chunks)

        # Bulk insert every 500 chunks to keep memory low
        if len(batch) >= 500:
            db.bulk_save_objects(batch)
            db.flush()
            batch = []

    if batch:
        db.bulk_save_objects(batch)

    db.commit()
    return total


def run():
    db = SessionLocal()
    try:
        repos = (
            db.query(Repository)
            .filter(Repository.status == RepoStatus.cloned)
            .all()
        )

        if not repos:
            logger.info("No cloned repos found. Nothing to parse.")
            return

        logger.info(f"Found {len(repos)} cloned repo(s).")

        for repo in repos:
            logger.info(f"Parsing repo id={repo.id} name={repo.name!r}")
            try:
                count = parse_repo(repo, db)
                repo.status = RepoStatus.parsed
                repo.error_msg = None
                logger.info(f"  ✓ Extracted {count} code chunks")
            except Exception as e:
                repo.status = RepoStatus.failed
                repo.error_msg = str(e)
                logger.error(f"  ✗ Failed: {e}")
            finally:
                db.commit()

        logger.info("parser_worker finished.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
