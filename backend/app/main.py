# backend/app/main.py

from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.logger import logger
from app.db.database import engine, Base

# Import routers directly from their modules
from app.api.repositories import router as repo_router
from app.api.search import router as search_router
from app.api.health import router as health_router

# Create database tables if not exist (for dev)
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# Assemble API router here in main.py
api_router = APIRouter()
api_router.include_router(health_router, prefix="/health")
api_router.include_router(repo_router, prefix="/repositories")
api_router.include_router(search_router, prefix="/search")

# Include API router in the app
app.include_router(api_router)

logger.info(f"{settings.APP_NAME} starting...")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Backend API started")