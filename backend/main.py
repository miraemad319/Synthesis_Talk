from fastapi import FastAPI, File, UploadFile, Request, Form, Cookie, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text
import os
import uuid
from docx import Document
from pydantic import BaseModel
import uuid
import re
from collections import defaultdict
from pydantic import BaseModel
from typing import Optional

# Custom libraries
from llm import react_with_llm
from duckduckgo_search import duckduckgo_search

class ChatRequest(BaseModel):
    message: str

def summarize_text(text: str) -> str:
    """
    Summarize the given text using the LLM.
    """
    prompt = f"Summarize the following document:\n\n{text[:3000]}"
    messages = [{"role": "user", "content": prompt}]
    return react_with_llm(messages)

# Session-based conversation + document storage
conversation_histories = {}
document_store = defaultdict(list)  # session_id -> list of (chunk_text, original_filename)

class Message(BaseModel):
    content: str

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is running"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file_path):
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        return f"Error extracting PDF text: {e}"

def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading TXT file: {e}"

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        return f"Error reading DOCX file: {e}"
    
def extract_search_query(message: str):
    # Simple regex to capture "search: some query" or "find: some query"
    pattern = r"(?:search|find)[:\-]\s*(.+)"
    match = re.search(pattern, message, re.I)
    if match:
        return match.group(1)
    return None

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), session_id: str = Cookie(None)):

    if session_id is None:
        session_id = str(uuid.uuid4())

    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_upload_{uuid.uuid4()}.{file_ext}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        if file_ext == "pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext == "txt":
            text = extract_text_from_txt(temp_path)
        elif file_ext == "docx":
            text = extract_text_from_docx(temp_path)
        else:
            return {"error": "Unsupported file type. Please upload PDF, TXT, or DOCX."}

        # Chunk text into 500-character pieces (basic retrieval unit)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        for chunk in chunks:
            document_store[session_id].append((chunk, file.filename))

        summary = summarize_text(text)
        return {
            "filename": file.filename,
            "summary": summary,
            "chunks": len(chunks)
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

import logging
# Set up basic logging
logging.basicConfig(level=logging.INFO)

@app.post("/chat/")
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    user_message = chat_request.message
    # Generate a new session ID if not present
    if session_id is None:
        session_id = str(uuid.uuid4())
        logging.info(f"New session started: {session_id}")

    # Parse incoming user message
    logging.info(f"User message for session {session_id}: {user_message}")

    # Initialize conversation history if not already present
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Append user message
    conversation_histories[session_id].append({"role": "user", "content": user_message})

    # Check if the message is a search query
    search_query = extract_search_query(user_message)
    if search_query:
        search_results = duckduckgo_search(search_query)
        context_message = f"Search results for '{search_query}':\n{search_results}"
        conversation_histories[session_id].append({"role": "system", "content": context_message})
        logging.info(f"Web search context added for session {session_id}")

    # Add relevant document chunks
    doc_context = ""
    for chunk, filename in document_store.get(session_id, []):
        for keyword in user_message.lower().split():
            if re.search(rf"\b{re.escape(keyword)}\b", chunk.lower()):
                doc_context += f"\n[From {filename}]\n{chunk}\n"
                break  # Avoid adding the same chunk multiple times

    # Optional: limit context length to avoid overloading the LLM
    MAX_CONTEXT_LENGTH = 2000
    if doc_context:
        trimmed_context = doc_context[:MAX_CONTEXT_LENGTH]
        conversation_histories[session_id].append({
            "role": "system",
            "content": f"Relevant documents:\n{trimmed_context.strip()}"
        })
        logging.info(f"Document context added for session {session_id}")

    # Call the LLM with the full context
    try:
        response_text = react_with_llm(conversation_histories[session_id])
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Append LLM response
    conversation_histories[session_id].append({"role": "assistant", "content": response_text})

    # Return response and set session cookie if needed
    response = JSONResponse(content={"response": response_text})
    if "session_id" not in request.cookies:
        response.set_cookie(key="session_id", value=session_id)
    return response

@app.post("/clear/")
async def clear_history(session_id: str = Cookie(default=None)):
    if session_id and session_id in conversation_histories:
        conversation_histories[session_id] = []
        return {"message": "Conversation history cleared."}
    return {"message": "No session found to clear."}

@app.get("/search/")
def search(query: str = Query(..., description="Search query")):
    result = duckduckgo_search(query)
    return {"query": query, "result": result}

