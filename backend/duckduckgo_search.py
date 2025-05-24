import httpx

def duckduckgo_search(query: str) -> str:
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
        return "Search failed or returned an error."

    data = response.json()

    heading = data.get("Heading", "No heading")
    abstract = data.get("AbstractText", "No abstract available.")
    source = data.get("AbstractSource", "")
    url = data.get("AbstractURL", "")
    related = [topic.get("Text") for topic in data.get("RelatedTopics", []) if "Text" in topic]

    result_parts = [
        f"Heading: {heading}",
        f"Abstract: {abstract}",
        f"Source: {source}",
        f"URL: {url}",
    ]

    if related:
        result_parts.append("Related Topics:\n" + "\n".join(f"- {text}" for text in related[:5]))

    return "\n".join(result_parts)
