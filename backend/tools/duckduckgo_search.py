import httpx

def duckduckgo_search(query: str):
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
        "skip_disambig": 1
    }

    response = httpx.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Search failed."}

    data = response.json()
    result = {
        "heading": data.get("Heading"),
        "abstract": data.get("AbstractText"),
        "source": data.get("AbstractSource"),
        "url": data.get("AbstractURL"),
        "related_topics": [topic.get("Text") for topic in data.get("RelatedTopics", []) if "Text" in topic]
    }
    return result
