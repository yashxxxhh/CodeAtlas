"""
run_pipeline.py — Run the full CodeAtlas worker pipeline in one shot.

Usage:
    cd codeatlas
    python run_pipeline.py

This runs all 4 workers in sequence:
    clone_worker → parser_worker → embedding_worker → index_worker

Useful during development. In production you'd trigger each worker
separately (or via a task queue like Celery).
"""

import sys
import time
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.logging import get_logger

logger = get_logger("pipeline")


def run_worker(name: str, module_path: str):
    logger.info(f"\n{'='*50}")
    logger.info(f"  Running {name}")
    logger.info(f"{'='*50}")
    start = time.time()

    # Import and run the worker
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, module_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run()

    elapsed = time.time() - start
    logger.info(f"  {name} completed in {elapsed:.1f}s\n")


if __name__ == "__main__":
    workers_dir = Path(__file__).parent / "workers"

    workers = [
        ("clone_worker",     str(workers_dir / "clone_worker.py")),
        ("parser_worker",    str(workers_dir / "parser_worker.py")),
        ("embedding_worker", str(workers_dir / "embedding_worker.py")),
        ("index_worker",     str(workers_dir / "index_worker.py")),
    ]

    total_start = time.time()
    logger.info("Starting CodeAtlas pipeline...")

    for worker_name, worker_path in workers:
        try:
            run_worker(worker_name, worker_path)
        except Exception as e:
            logger.error(f"Pipeline stopped at {worker_name}: {e}")
            sys.exit(1)

    total = time.time() - total_start
    logger.info(f"\n✓ Pipeline complete in {total:.1f}s")
    logger.info("Your repositories are now searchable!")
    logger.info("POST /api/reload-index to refresh the search cache.\n")
