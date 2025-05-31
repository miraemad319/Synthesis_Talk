from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Pydantic model for the POST body
class SwitchContextRequest(BaseModel):
    context_id: str


# In‐memory storage of contexts for demonstration. 
# Replace with your own persistence or session‐based logic.
_contexts = [
    {
        "id": "default",
        "topic": "Getting Started",
        "sources": [],   # start empty
    }
]
_current_context: Optional[str] = "default"


@router.get("/context/", response_model=dict)
async def get_contexts():
    """
    Return all available contexts and the ID of the currently‐active context.
    Response:
      {
        "contexts": [
          { "id": "default", "topic": "Getting Started", "sources": ["…"] },
          …
        ],
        "current": "default"
      }
    """
    return {"contexts": _contexts, "current": _current_context}


@router.post("/context/", response_model=dict)
async def switch_context(request: SwitchContextRequest):
    """
    Switch to a different context. Expects a JSON body { "context_id": "<id>" }.
    Returns: { "current": "<new_id>" }
    """
    global _current_context

    # Verify the requested ID exists:
    valid_ids = {ctx["id"] for ctx in _contexts}
    if request.context_id not in valid_ids:
        raise HTTPException(status_code=400, detail="Invalid context_id")

    _current_context = request.context_id
    return {"current": _current_context}
