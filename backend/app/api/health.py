# backend/app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}