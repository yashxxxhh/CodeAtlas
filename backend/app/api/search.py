from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/")
async def search_code(query: str = Query(..., min_length=1)):
    # Placeholder: query vector DB & return results
    return {"query": query, "results": []}