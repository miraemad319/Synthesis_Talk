from fastapi import APIRouter, Cookie, Body
from pydantic import BaseModel
from backend.utils.session_store import conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()

class NoteInput(BaseModel):
    note: str

class ExplainInput(BaseModel):
    query: str

@router.post("/note/")
def save_note(note_input: NoteInput, session_id: str = Cookie(default=None)):
    """
    Stores a user-defined note in the session's conversation history.
    """
    if not session_id:
        return {"error": "Missing session ID"}

    note_text = f"[NOTE] {note_input.note}"
    conversation_histories.setdefault(session_id, []).append({"role": "user", "content": note_text})
    persist()
    return {"message": "Note saved."}

@router.post("/explain/")
def explain_query(explain_input: ExplainInput, session_id: str = Cookie(default=None)):
    """
    Sends an explanation query to the LLM with enhanced instruction.
    """
    query = f"Please explain the following concept in simple terms:\n\n{explain_input.query}"
    
    conversation_histories.setdefault(session_id, []).append({
        "role": "user",
        "content": query
    })

    response = react_with_llm(conversation_histories[session_id])

    conversation_histories[session_id].append({
        "role": "assistant",
        "content": response
    })

    persist()
    return {"response": response}
