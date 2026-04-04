"""
database.py — SQLAlchemy engine, session factory, and Base class.
All models inherit from Base. All sessions come from SessionLocal.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # Verify connection before use
    pool_size=5,
    max_overflow=10,
    echo=False,           # Set True to log raw SQL (debug only)
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency injection.
    Yields a database session and always closes it after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
