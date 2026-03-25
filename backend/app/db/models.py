from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class RepositoryStatus(enum.Enum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    source_type = Column(String, nullable=False)
    url = Column(String, nullable=True)
    status = Column(Enum(RepositoryStatus), default=RepositoryStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    files = relationship("File", back_populates="repository")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    path = Column(String, nullable=False)
    language = Column(String)
    size = Column(Integer)

    repository = relationship("Repository", back_populates="files")
    symbols = relationship("Symbol", back_populates="file")

class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    name = Column(String)
    type = Column(String)
    start_line = Column(Integer)
    end_line = Column(Integer)
    content = Column(String)

    file = relationship("File", back_populates="symbols")