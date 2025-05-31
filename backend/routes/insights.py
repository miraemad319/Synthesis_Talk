# backend/routes/insights.py

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse
import json

from backend.utils.session_store import document_store, conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()

@router.get("/insights/")
async def generate_insights(session_id: str = Cookie(default=None)):
    print(f"[DEBUG /insights/] session_id cookie:", session_id)
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    print(f"[DEBUG /insights/] document_store for {session_id}:", docs)
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    all_text = "\n".join(chunk for chunk, _ in docs)
    if not all_text.strip():
        raise HTTPException(status_code=400, detail="No content available for generating insights.")

    # Build a JSON‐output prompt
    prompt = (
        "You are an AI research assistant. "
        "Please analyze the following document and return a JSON with\n"
        "  \"paragraph\": \"<a concise summary>\",\n"
        "  \"bullets\": [\"<bullet1>\", \"<bullet2>\", \"<bullet3>\"]\n"
        f"Document Text:\n{all_text[:3000]}\n"
        "Return ONLY valid JSON."
    )

    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    try:
        llm_response = react_with_llm([{"role": "user", "content": prompt}])
        parsed = json.loads(llm_response)
        paragraph = parsed.get("paragraph", "")
        bullets = parsed.get("bullets", [])
        if not isinstance(bullets, list):
            bullets = []
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=500, detail="LLM did not return valid JSON for insights.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {e}")

    conversation_histories[session_id].append({"role": "assistant", "content": llm_response})
    persist()

    print(f"[DEBUG /insights/] returning:", {"paragraph": paragraph, "bullets": bullets})
    return JSONResponse(content={"paragraph": paragraph, "bullets": bullets})

