from fastapi import FastAPI, File, UploadFile, Request, Form, Cookie, Query
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

# Custom libraries
from llm import react_with_llm
from duckduckgo_search import duckduckgo_search

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

@app.post("/chat/")
async def chat(request: Request, session_id: str = Cookie(None)):
    import uuid

    if session_id is None:
        session_id = str(uuid.uuid4())

    data = await request.json()
    user_message = data.get("message", "")

    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    conversation_histories[session_id].append({"role": "user", "content": user_message})

    # If query seems like a search, trigger web search
    search_query = extract_search_query(user_message)
    if search_query:
        search_results = duckduckgo_search(search_query)
        context_message = f"Search results for '{search_query}':\n{search_results}"
        conversation_histories[session_id].append({"role": "system", "content": context_message})

    # Add relevant document chunks to the conversation
    doc_context = ""
    for chunk, filename in document_store.get(session_id, []):
        if any(keyword in chunk.lower() for keyword in user_message.lower().split()):
            doc_context += f"\n[From {filename}]\n{chunk}\n"

    if doc_context:
        conversation_histories[session_id].append({"role": "system", "content": f"Relevant documents:\n{doc_context.strip()}"})

    try:
        response_text = react_with_llm(conversation_histories[session_id])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    conversation_histories[session_id].append({"role": "assistant", "content": response_text})

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

