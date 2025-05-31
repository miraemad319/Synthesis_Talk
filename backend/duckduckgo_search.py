import httpx
import asyncio
import time
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Structured search result"""
    heading: str
    abstract: str
    source: str
    url: str
    related_topics: List[str]
    search_query: str
    timestamp: float

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_minute: int = 30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def can_make_call(self) -> bool:
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        return len(self.calls) < self.calls_per_minute
    
    def record_call(self):
        self.calls.append(time.time())

# Global rate limiter instance
rate_limiter = RateLimiter()

async def duckduckgo_search_async(query: str, max_retries: int = 3) -> SearchResult:
    """Async version of DuckDuckGo search with enhanced error handling and rate limiting"""
    
    # Check rate limit
    if not rate_limiter.can_make_call():
        logger.warning("Rate limit exceeded, waiting...")
        await asyncio.sleep(2)
        if not rate_limiter.can_make_call():
            raise Exception("Rate limit exceeded. Please try again later.")
    
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
        "skip_disambig": 1,
        "safe_search": "moderate"
    }
    
    for attempt in range(max_retries):
        try:
            rate_limiter.record_call()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return _parse_search_response(data, query)
                
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                
                else:
                    logger.error(f"Search API returned status {response.status_code}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Search failed with status {response.status_code}")
        
        except httpx.TimeoutException:
            logger.warning(f"Search timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise Exception("Search timed out after multiple attempts")
            await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Search error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"Search failed: {str(e)}")
            await asyncio.sleep(1)
    
    raise Exception("Search failed after all retry attempts")

def duckduckgo_search(query: str) -> str:
    """Synchronous wrapper for the async search function"""
    try:
        # Run the async function in a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If we're already in an async context, create a new loop
            import threading
            result = None
            exception = None
            
            def run_search():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(duckduckgo_search_async(query))
                    new_loop.close()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_search)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return _format_search_result(result)
        else:
            result = loop.run_until_complete(duckduckgo_search_async(query))
            return _format_search_result(result)
    
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        return f"Search failed: {str(e)}\n\nQuery: {query}\nPlease try rephrasing your search or try again later."

def _parse_search_response(data: Dict, query: str) -> SearchResult:
    """Parse DuckDuckGo API response into structured result"""
    heading = data.get("Heading", "No heading available")
    abstract = data.get("AbstractText", "No abstract available.")
    source = data.get("AbstractSource", "Unknown source")
    url = data.get("AbstractURL", "")
    
    # Extract related topics
    related_topics = []
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict) and "Text" in topic:
            related_topics.append(topic["Text"])
        elif isinstance(topic, dict) and "Topics" in topic:
            # Handle nested topics
            for subtopic in topic["Topics"]:
                if isinstance(subtopic, dict) and "Text" in subtopic:
                    related_topics.append(subtopic["Text"])
    
    return SearchResult(
        heading=heading,
        abstract=abstract,
        source=source,
        url=url,
        related_topics=related_topics[:10],  # Limit to top 10
        search_query=query,
        timestamp=time.time()
    )

def _format_search_result(result: SearchResult) -> str:
    """Format search result for display"""
    if not result.abstract or result.abstract == "No abstract available.":
        # If no abstract, try to provide something useful
        formatted_result = [
            f"Search Query: {result.search_query}",
            f"Heading: {result.heading}",
            f"Limited information available for this query.",
        ]
        
        if result.url:
            formatted_result.append(f"Reference URL: {result.url}")
        
        if result.related_topics:
            formatted_result.append("\nRelated Topics:")
            formatted_result.extend([f"- {topic}" for topic in result.related_topics[:5]])
        
        formatted_result.append("\nSuggestion: Try a more specific search query or search for related terms.")
        
    else:
        formatted_result = [
            f"Search Query: {result.search_query}",
            f"Topic: {result.heading}",
            f"Summary: {result.abstract}",
        ]
        
        if result.source:
            formatted_result.append(f"Source: {result.source}")
        
        if result.url:
            formatted_result.append(f"Reference URL: {result.url}")
        
        if result.related_topics:
            formatted_result.append("\nRelated Topics:")
            formatted_result.extend([f"- {topic}" for topic in result.related_topics[:5]])
    
    return "\n".join(formatted_result)

def search_multiple_queries(queries: List[str], max_concurrent: int = 3) -> Dict[str, str]:
    """Search multiple queries concurrently with rate limiting"""
    async def search_all():
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_semaphore(query):
            async with semaphore:
                try:
                    result = await duckduckgo_search_async(query)
                    return query, _format_search_result(result)
                except Exception as e:
                    return query, f"Search failed for '{query}': {str(e)}"
        
        tasks = [search_with_semaphore(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Handle nested async context
            import threading
            result = None
            exception = None
            
            def run_searches():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(search_all())
                    new_loop.close()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_searches)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
        else:
            return loop.run_until_complete(search_all())
    
    except Exception as e:
        logger.error(f"Multiple search failed: {e}")
        return {query: f"Search failed: {str(e)}" for query in queries}

# Utility function for testing
def test_search():
    """Test function for the search functionality"""
    test_queries = [
        "artificial intelligence machine learning",
        "climate change global warming",
        "quantum computing applications"
    ]
    
    print("Testing single search...")
    result = duckduckgo_search("artificial intelligence")
    print(result)
    print("\n" + "="*50 + "\n")
    
    print("Testing multiple search...")
    results = search_multiple_queries(test_queries)
    for query, result in results.items():
        print(f"Query: {query}")
        print(f"Result: {result[:200]}...")
        print("\n" + "-"*30 + "\n")

if __name__ == "__main__":
    test_search()