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
                "content": search_context,
                "timestamp": datetime.now().isoformat()
            })
            persist()

        logger.info(f"[SEARCH] Completed search for: {query}")
        
        # Format response for frontend compatibility
        return {
            "query": query,
            "results": [
                {
                    "title": f"Search Results for: {query}",
                    "snippet": search_results[:500] + "..." if len(search_results) > 500 else search_results,
                    "url": sources[0] if sources else "",
                    "source": "DuckDuckGo Search",
                    "publishedDate": datetime.now().isoformat()
                }
            ],
            "total_results": 1,
            "verified": result.verified,
            "sources": sources,
            "cached": result.cached
        }

    except Exception as e:
        logger.error(f"[SEARCH] Search failed for query '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Search operation failed: {str(e)}")

@router.post("/search/")
def search_post(
    request: SearchRequest,
    session_id: str = Cookie(default=None)
):
    """
    POST version of search endpoint for complex requests.
    """
    return search(
        query=request.query,
        session_id=session_id,
        verify=request.verify_facts,
        use_cache=True
    )

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
            "timestamp": datetime.now().isoformat(),
            "verification_status": "completed"
        }
        
        # Add to session if available
        if session_id and session_id in conversation_histories:
            fact_check_entry = f"[FACT-CHECK] Claim: {claim}\nAnalysis: {analysis[:500]}..."
            conversation_histories[session_id].append({
                "role": "system",
                "content": fact_check_entry,
                "timestamp": datetime.now().isoformat()
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
                searches.append({
                    "query": query, 
                    "timestamp": msg.get("timestamp", "recent")
                })
    
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

@router.post("/search/documents")
def search_documents(
    request: dict,
    session_id: str = Cookie(default=None)
):
    """
    Search within uploaded documents for the session.
    """
    try:
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Import here to avoid circular imports
        from backend.utils.session_store import document_store
        from backend.utils.concept_linker import find_relevant_chunks
        
        # Get documents for session
        docs = document_store.get(session_id, [])
        if not docs:
            return {
                "query": query,
                "results": [],
                "message": "No documents uploaded for this session"
            }
        
        # Convert to format expected by concept_linker
        doc_chunks = []
        for entry in docs:
            if len(entry) >= 2:
                chunk_text, filename = entry[0], entry[1]
                doc_chunks.append((chunk_text, filename))
        
        # Find relevant chunks
        relevant_chunks = find_relevant_chunks(query, doc_chunks, top_k=5)
        
        # Format results
        results = []
        for chunk_text, filename in relevant_chunks:
            results.append({
                "title": f"Excerpt from {filename}",
                "snippet": chunk_text[:300] + "..." if len(chunk_text) > 300 else chunk_text,
                "source": filename,
                "type": "document"
            })
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "searched_documents": len(set(filename for _, filename in doc_chunks))
        }
        
    except Exception as e:
        logger.error(f"[SEARCH] Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")

@router.post("/search/combined")
def search_combined(
    request: dict,
    session_id: str = Cookie(default=None)
):
    """
    Perform both web and document search and combine results.
    """
    try:
        query = request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Perform web search
        web_results = search(query=query, session_id=session_id, verify=False, use_cache=True)
        
        # Perform document search
        doc_results = search_documents(request, session_id)
        
        # Combine results
        combined_results = {
            "query": query,
            "web_results": web_results.get("results", []),
            "document_results": doc_results.get("results", []),
            "total_web_results": web_results.get("total_results", 0),
            "total_document_results": doc_results.get("total_results", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return combined_results
        
    except Exception as e:
        logger.error(f"[SEARCH] Combined search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Combined search failed: {str(e)}")