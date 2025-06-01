from fastapi import APIRouter, Cookie, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
from datetime import datetime

from backend.duckduckgo_search import duckduckgo_search
from backend.utils.session_store import conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    query: str
    verify_facts: bool = False
    session_context: bool = True

class SearchResult(BaseModel):
    query: str
    results: str
    verified: bool = False
    sources: List[str] = []
    cached: bool = False

# Simple in-memory cache for search results
search_cache: Dict[str, SearchResult] = {}

@router.get("/search/")
def search(
    query: str = Query(..., description="Search query"),
    session_id: str = Cookie(default=None),
    verify: bool = Query(default=False, description="Verify facts using LLM"),
    use_cache: bool = Query(default=True, description="Use cached results if available")
):
    """
    Enhanced search endpoint with fact verification and caching.
    """
    try:
        # Check cache first
        cache_key = f"{query.lower().strip()}"
        if use_cache and cache_key in search_cache:
            cached_result = search_cache[cache_key]
            logger.info(f"[SEARCH] Returning cached result for: {query}")
            return cached_result.dict()

        # Perform web search
        search_results = duckduckgo_search(query)
        
        # Extract sources from search results
        sources = []
        if "Source:" in search_results and "URL:" in search_results:
            lines = search_results.split('\n')
            for line in lines:
                if line.startswith("Source:") or line.startswith("URL:"):
                    source = line.split(':', 1)[1].strip()
                    if source and source not in sources:
                        sources.append(source)

        result = SearchResult(
            query=query,
            results=search_results,
            sources=sources,
            cached=False
        )

        # Fact verification if requested
        if verify and session_id:
            try:
                verification_prompt = f"""
                Please analyze the following search results for accuracy and reliability:
                
                Query: {query}
                Results: {search_results[:1500]}
                
                Evaluate:
                1. Are the facts presented accurate?
                2. Are the sources reliable?
                3. Is any information potentially misleading?
                4. What additional context might be helpful?
                
                Provide a brief verification summary.
                """
                
                verification_history = [{"role": "user", "content": verification_prompt}]
                verification_result = react_with_llm(verification_history)
                
                result.results += f"\n\nFact Verification:\n{verification_result}"
                result.verified = True
                
                logger.info(f"[SEARCH] Fact verification completed for: {query}")
                
            except Exception as e:
                logger.error(f"[SEARCH] Fact verification failed: {e}")
                result.results += "\n\nNote: Fact verification was requested but failed."

        # Cache the result
        if use_cache:
            search_cache[cache_key] = result

        # Add to session history if session exists
        if session_id and session_id in conversation_histories:
            search_context = f"[SEARCH] Query: {query}\nResults: {search_results[:800]}"
            conversation_histories[session_id].append({
                "role": "system", 
                "content": search_context
            })
            persist()

        logger.info(f"[SEARCH] Completed search for: {query}")
        return result.dict()

    except Exception as e:
        logger.error(f"[SEARCH] Search failed for query '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Search operation failed: {str(e)}")

@router.post("/search/verify/")
def verify_claim(
    claim: str = Query(..., description="Claim to verify"),
    session_id: str = Cookie(default=None)
):
    """
    Verify a specific claim by searching and using LLM analysis.
    """
    try:
        # Search for information about the claim
        search_query = f"fact check {claim}"
        search_results = duckduckgo_search(search_query)
        
        # Use LLM to analyze the claim
        verification_prompt = f"""
        Please fact-check the following claim using the search results provided:
        
        Claim: "{claim}"
        
        Search Results:
        {search_results[:2000]}
        
        Analysis Framework:
        1. **Accuracy**: Is the claim factually correct?
        2. **Evidence**: What evidence supports or contradicts it?
        3. **Sources**: How reliable are the available sources?
        4. **Context**: What important context should be considered?
        5. **Conclusion**: True, False, Partially True, or Insufficient Evidence?
        
        Provide a structured fact-check analysis.
        """
        
        verification_history = [{"role": "user", "content": verification_prompt}]
        analysis = react_with_llm(verification_history)
        
        result = {
            "claim": claim,
            "analysis": analysis,
            "search_results": search_results,
            "timestamp": str(datetime.now())
        }
        
        # Add to session if available
        if session_id and session_id in conversation_histories:
            fact_check_entry = f"[FACT-CHECK] Claim: {claim}\nAnalysis: {analysis[:500]}..."
            conversation_histories[session_id].append({
                "role": "system",
                "content": fact_check_entry
            })
            persist()
        
        return result
        
    except Exception as e:
        logger.error(f"[SEARCH] Claim verification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.get("/search/history/")
def get_search_history(session_id: str = Cookie(default=None)):
    """
    Get search history for the current session.
    """
    if not session_id or session_id not in conversation_histories:
        return {"searches": []}
    
    # Extract search entries from conversation history
    searches = []
    for msg in conversation_histories[session_id]:
        if msg["role"] == "system" and msg["content"].startswith("[SEARCH]"):
            content = msg["content"]
            lines = content.split('\n')
            query_line = next((line for line in lines if line.startswith("[SEARCH] Query:")), "")
            if query_line:
                query = query_line.replace("[SEARCH] Query:", "").strip()
                searches.append({"query": query, "timestamp": "recent"})
    
    return {"searches": searches[-10:]}  # Return last 10 searches

@router.delete("/search/cache/")
def clear_search_cache():
    """
    Clear the search cache.
    """
    global search_cache
    cache_size = len(search_cache)
    search_cache.clear()
    return {"message": f"Search cache cleared. Removed {cache_size} cached results."}
