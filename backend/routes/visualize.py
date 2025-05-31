# backend/routes/visualize.py

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse
from collections import Counter

from backend.utils.session_store import document_store

router = APIRouter()

@router.get("/visualize/")
async def visualize_keywords(session_id: str = Cookie(default=None)):
    """
    Count how many chunks each filename contributed in this session,
    and return JSON: { data: [ { name: filename, value: count }, … ] }
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    # Build a frequency count of how many chunks came from each file
    freq = Counter()
    for chunk, filename in docs:
        freq[filename] += 1

    # Transform into [{"name": filename,"value": count}, …]
    data = [{"name": fn, "value": cnt} for fn, cnt in freq.items()]

    # If you want a specific sort order (e.g. descending by count), you can do:
    # data.sort(key=lambda x: x["value"], reverse=True)

    return JSONResponse(content={"data": data})


