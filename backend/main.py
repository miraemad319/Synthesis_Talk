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

# Custom libraries
from llm import chat_with_llm
from duckduckgo_search import duckduckgo_search

def summarize_text(text: str) -> str:
    """
    Summarize the given text using the LLM.
    """
    prompt = f"Summarize the following document:\n\n{text[:3000]}"
    messages = [{"role": "user", "content": prompt}]
    return chat_with_llm(messages)

conversation_histories = {}

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
async def upload_file(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1].lower()
    unique_id = uuid.uuid4()
    temp_path = f"temp_upload_{unique_id}.{file_ext}"

    try:
        # Save uploaded file
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text
        if file_ext == "pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext == "txt":
            text = extract_text_from_txt(temp_path)
        elif file_ext == "docx":
            text = extract_text_from_docx(temp_path)
        else:
            return {"error": "Unsupported file type. Please upload PDF, TXT, or DOCX."}

        # Summarize text
        summary = summarize_text(text)

        return {
            "filename": file.filename,
            "content": text[:1000],  # Optional: first 1000 chars
            "summary": summary
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat/")
async def chat(request: Request, session_id: str = Cookie(None)):
    if session_id is None:
        # Generate a new session ID if none exists
        import uuid
        session_id = str(uuid.uuid4())

    data = await request.json()
    user_message = data.get("message", "")

    # Initialize conversation history if not present
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Append user message to history
    conversation_histories[session_id].append({"role": "user", "content": user_message})

    # Check if user wants to do a web search
    search_query = extract_search_query(user_message)
    if search_query:
        # Call the DuckDuckGo search tool
        search_results = duckduckgo_search(search_query)

        # Add search results to conversation as system message for context
        context_message = (
            f"Search results for '{search_query}':\n{search_results}"
        )
        conversation_histories[session_id].append({"role": "system", "content": context_message})

    # Call the LLM with enriched conversation history
    try:
        response_text = chat_with_llm(conversation_histories[session_id])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Append LLM response to history
    conversation_histories[session_id].append({"role": "assistant", "content": response_text})

    # Return response and set session_id cookie if new
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

