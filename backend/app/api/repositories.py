from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models

router = APIRouter()

@router.post("/upload")
async def upload_repository(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Placeholder: save file, create repo record, enqueue worker
    repo = models.Repository(name=file.filename, source_type="upload", status="pending")
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return {"message": "Repository uploaded", "repo_id": repo.id}