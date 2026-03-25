import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = os.getenv("APP_NAME", "CodeAtlas")
    DEBUG = os.getenv("DEBUG", "False")

    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")

    REPOSITORY_STORAGE = os.getenv("REPOSITORY_STORAGE")
    VECTOR_INDEX_PATH = os.getenv("VECTOR_INDEX_PATH")

settings = Settings()