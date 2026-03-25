from fastapi import APIRouter
from .repositories import router as repo_router
from .search import router as search_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health")
api_router.include_router(repo_router, prefix="/repositories")
api_router.include_router(search_router, prefix="/search")