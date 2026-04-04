"""
main.py — FastAPI application entry point.

Run with:
    cd codeatlas/backend
    uvicorn app.main:app --reload --port 8000

API docs available at:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.logging import get_logger
from app.db.database import engine
from app.db.models import Base

logger = get_logger("main")

# Create all DB tables on startup (safe to run multiple times)
Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized.")

app = FastAPI(
    title="CodeAtlas",
    description=(
        "Semantic code search platform.\n\n"
        "Upload a repository, run the 4 worker scripts, then search your codebase "
        "using natural language queries."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the React dev server to call the API without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # CRA default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

logger.info("CodeAtlas API ready at http://localhost:8000")
logger.info("Swagger docs:  http://localhost:8000/docs")
