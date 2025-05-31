from fastapi import APIRouter, Request, HTTPException, Body, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import logging

from backend.utils.session_store import conversation_histories, document_store, persist
from backend.utils.helpers import extract_search_query
from backend.utils.concept_linker import find_relevant_chunks
from backend.llm import react_with_llm
from backend.duckduckgo_search import duckduckgo_search

logging.basicConfig(level=logging.INFO)
router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat/")
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    user_message = chat_request.message

    # 1) Create a new session if none provided
    is_new_session = False
    if session_id is None:
        session_id = str(uuid.uuid4())
        is_new_session = True
        logging.info(f"[CHAT] New session started: {session_id}")

    # 2) Log user message
    logging.info(f"[CHAT] Session {session_id} | User: {user_message}")

    # 3) Initialize conversation history for this session if missing
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # 4) Append user message to history
    conversation_histories[session_id].append({"role": "user", "content": user_message})
    persist()

    # 5) If the user triggered a web search, add that context
    search_query = extract_search_query(user_message)
    if search_query:
        search_results = duckduckgo_search(search_query)
        system_msg = f"Search results for '{search_query}':\n{search_results}"
        conversation_histories[session_id].append({"role": "system", "content": system_msg})
        logging.info(f"[CHAT] Session {session_id} | Web search context appended")
        persist()

    # 6) Pull in relevant document chunks for this session
    # document_store.get(session_id, []) returns a list of (chunk_text, filename) tuples
    relevant = find_relevant_chunks(user_message, document_store.get(session_id, []))

    # DEBUG: print out exactly what chunks were returned
    logging.info(f"[DEBUG chat] document_store[{session_id}] = {document_store.get(session_id, [])}")
    logging.info(f"[DEBUG chat] relevant_chunks = {relevant}")

    if relevant:
        # Build a string of “Relevant documents:” context
        doc_context = "\n".join(f"[From {fname}]\n{chunk}" for chunk, fname in relevant)
        # If it’s too long, truncate to 2000 characters
        doc_context = doc_context[:2000]
        conversation_histories[session_id].append({
            "role": "system",
            "content": f"Relevant documents:\n{doc_context.strip()}"
        })
        logging.info(f"[CHAT] Session {session_id} | Document context appended")
        persist()

    # 7) Call the LLM with the full conversation history
    try:
        assistant_reply = react_with_llm(conversation_histories[session_id])
    except Exception as e:
        logging.error(f"[CHAT] LLM call failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # 8) Save the assistant's reply
    conversation_histories[session_id].append({"role": "assistant", "content": assistant_reply})
    persist()

    # 9) Build JSON response and set cookie on first session
    response = JSONResponse(content={"reply": assistant_reply})
    if is_new_session:
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

@router.post("/clear/")
async def clear_history(session_id: Optional[str] = Cookie(default=None)):
    if session_id and session_id in conversation_histories:
        conversation_histories[session_id] = []
        persist()
        return {"message": "Conversation history cleared."}
    return {"message": "No session found to clear."}


