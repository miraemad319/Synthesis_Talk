from fastapi import APIRouter, Request, Body, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
import re

from ..utils.session_store import conversation_histories, document_store
from ..utils.helpers import extract_search_query
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

    # Check if the message contains a web search trigger
    search_query = extract_search_query(user_message)
    if search_query:
        search_results = duckduckgo_search(search_query)
        context_message = f"Search results for '{search_query}':\n{search_results}"
        conversation_histories[session_id].append({"role": "system", "content": context_message})
        logging.info(f"Web search context added for session {session_id}")

    # Inject document chunks based on keyword overlap
    doc_context = ""
    for chunk, filename in document_store.get(session_id, []):
        for keyword in user_message.lower().split():
            if re.search(rf"\b{re.escape(keyword)}\b", chunk.lower()):
                doc_context += f"\n[From {filename}]\n{chunk}\n"
                break  # Avoid duplicates

    # Trim context to avoid token overflow
    MAX_CONTEXT_LENGTH = 2000
    if doc_context:
        trimmed_context = doc_context[:MAX_CONTEXT_LENGTH]
        conversation_histories[session_id].append({
            "role": "system",
            "content": f"Relevant documents:\n{trimmed_context.strip()}"
        })
        logging.info(f"Document context added for session {session_id}")

    # Get LLM response
    try:
        response_text = react_with_llm(conversation_histories[session_id])
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Save assistant response to history
    conversation_histories[session_id].append({"role": "assistant", "content": response_text})

    # Send response and set session ID cookie if it's a new session
    response = JSON
