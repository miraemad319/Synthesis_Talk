from fastapi import APIRouter, Request, Body, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
import re

from ..utils.session_store import conversation_histories, document_store, persist
from ..utils.helpers import extract_search_query
from ..utils.concept_linker import find_relevant_chunks
from ..llm import react_with_llm
from ..duckduckgo_search import duckduckgo_search

# Initialize logger and router
logging.basicConfig(level=logging.INFO)
router = APIRouter()

# Define the chat request body format
class ChatRequest(BaseModel):
    message: str

# POST /chat/ - Accepts a user message and returns an LLM-generated response
@router.post("/chat/")
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    user_message = chat_request.message

    # Generate a new session ID if one doesn't exist
    if session_id is None:
        session_id = str(uuid.uuid4())
        logging.info(f"New session started: {session_id}")

    logging.info(f"User message for session {session_id}: {user_message}")

    # Initialize conversation history
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Save user message to the conversation
    conversation_histories[session_id].append({"role": "user", "content": user_message})
    persist()

    # Check if the message contains a web search trigger
    search_query = extract_search_query(user_message)
    if search_query:
        search_results = duckduckgo_search(search_query)
        context_message = f"Search results for '{search_query}':\n{search_results}"
        conversation_histories[session_id].append({"role": "system", "content": context_message})
        logging.info(f"Web search context added for session {session_id}")
        persist()

    relevant_chunks = find_relevant_chunks(user_message, document_store.get(session_id, []))
    doc_context = "\n".join(f"[From {filename}]\n{chunk}" for chunk, filename in relevant_chunks)

    # Trim context to avoid token overflow
    MAX_CONTEXT_LENGTH = 2000
    if doc_context:
        trimmed_context = doc_context[:MAX_CONTEXT_LENGTH]
        conversation_histories[session_id].append({
            "role": "system",
            "content": f"Relevant documents:\n{trimmed_context.strip()}"
        })
        logging.info(f"Document context added for session {session_id}")
        persist()

    # Get LLM response
    try:
        response_text = react_with_llm(conversation_histories[session_id])
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Save assistant response to history
    conversation_histories[session_id].append({"role": "assistant", "content": response_text})
    persist()

    # Send response and set session ID cookie if it's a new session
    response = JSONResponse(content={"response": response_text})
    if "session_id" not in request.cookies:
        response.set_cookie(key="session_id", value=session_id)
    return response

# POST /clear/ - Clears the session's conversation history
@router.post("/clear/")
async def clear_history(session_id: Optional[str] = Cookie(default=None)):
    if session_id and session_id in conversation_histories:
        conversation_histories[session_id] = []
        persist()
        return {"message": "Conversation history cleared."}
    return {"message": "No session found to clear."}

