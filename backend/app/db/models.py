"""
models.py — ORM models for the two core tables.

Repository  → tracks a repo and its processing status (state machine)
CodeChunk   → one row per extracted function/class from the repo
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class RepoStatus(str, enum.Enum):
    pending  = "pending"   # Uploaded, not yet cloned/extracted
    cloned   = "cloned"    # Repo files are on disk
    parsed   = "parsed"    # Code chunks extracted into DB
    embedded = "embedded"  # Embeddings generated and saved to disk
    indexed  = "indexed"   # Vectors loaded into FAISS
    failed   = "failed"    # Something went wrong (see error_msg)


class Repository(Base):
    __tablename__ = "repositories"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    source_url = Column(String(1024), nullable=True)   # Git URL if provided
    local_path = Column(String(1024), nullable=True)   # Absolute path on disk
    status     = Column(SAEnum(RepoStatus), default=RepoStatus.pending, nullable=False)
    error_msg  = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship(
        "CodeChunk",
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Repository id={self.id} name={self.name!r} status={self.status}>"


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id         = Column(Integer, primary_key=True, index=True)
    repo_id    = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    file_path  = Column(String(1024), nullable=False)   # Relative to repo root
    chunk_type = Column(String(50), nullable=False)     # "function" | "class"
    name       = Column(String(255), nullable=False)    # Function or class name
    code       = Column(Text, nullable=False)            # Raw source snippet
    start_line = Column(Integer, nullable=True)
    end_line   = Column(Integer, nullable=True)
    faiss_id   = Column(Integer, nullable=True, index=True)  # Position in FAISS index

    repository = relationship("Repository", back_populates="chunks")

    def __repr__(self):
        return f"<CodeChunk id={self.id} name={self.name!r} type={self.chunk_type}>"
