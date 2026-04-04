"""
config.py — Central settings loaded from configs/.env
All other modules import `settings` from here.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://codeatlas:lucky8800@localhost:5432/mydb"
    data_dir: str = "./data"
    faiss_index_path: str = "./data/faiss_index/index.faiss"
    chunk_id_map_path: str = "./data/faiss_index/chunk_ids.json"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_results: int = 10

    class Config:
        env_file = "configs/.env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure required directories exist at import time
Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
Path(f"{settings.data_dir}/repos").mkdir(parents=True, exist_ok=True)
