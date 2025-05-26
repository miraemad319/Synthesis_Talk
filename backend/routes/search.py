from fastapi import APIRouter, Query
from ..duckduckgo_search import duckduckgo_search

router = APIRouter()

# GET /search/?query=... - Perform a web search and return the result
@router.get("/search/")
def search(query: str = Query(..., description="Search query")):
    """
    A simple search endpoint that performs a DuckDuckGo search using the query provided.
    """
    result = duckduckgo_search(query)
    return {
        "query": query,
        "result": result
    }
