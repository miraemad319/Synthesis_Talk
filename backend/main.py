from fastapi import FastAPI, File, UploadFile, Request, Form, Cookie, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text
import os
import uuid
from docx import Document
from pydantic import BaseModel
import uuid

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
async def chat(message: Message, session_id: str = Cookie(default=None)):
    # Generate a new session_id if one doesn't exist
    if session_id is None:
        session_id = str(uuid.uuid4())
        conversation_histories[session_id] = []
    elif session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Add user message
    conversation_histories[session_id].append({"role": "user", "content": message.content})

    # Generate assistant reply
    response = chat_with_llm(conversation_histories[session_id])

    # Add assistant reply to history
    conversation_histories[session_id].append({"role": "assistant", "content": response})

    # Return response with session_id set as cookie
    return JSONResponse(content={"response": response}, headers={"Set-Cookie": f"session_id={session_id}; Path=/; HttpOnly"})

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

