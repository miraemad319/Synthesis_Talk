from fastapi import FastAPI, File, UploadFile, Request, Cookie, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text
from docx import Document
from collections import defaultdict
from pydantic import BaseModel
from typing import Optional
import os
import uuid
import re
import logging
import nltk
from nltk.tokenize import sent_tokenize

# Download punkt tokenizer once
nltk.download('punkt')

# Custom libraries
from llm import react_with_llm
from duckduckgo_search import duckduckgo_search

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(level=logging.INFO)

# Memory stores
conversation_histories = {}
document_store = defaultdict(list)

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    content: str

# Health check
@app.get("/")
def read_root():
    return {"message": "API is running"}

# Extraction helpers
def extract_text_from_pdf(file_path):
    try:
        return extract_text(file_path)
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
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        return f"Error reading DOCX file: {e}"

def extract_search_query(message: str):
    pattern = r"(?:search|find)[:\-]\s*(.+)"
    match = re.search(pattern, message, re.I)
    return match.group(1) if match else None

def split_into_chunks(text, max_tokens=500):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sent in sentences:
        if len(current_chunk) + len(sent) < max_tokens:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def summarize_text(text: str) -> str:
    prompt = f"Summarize the following document:\n\n{text[:3000]}"
    messages = [{"role": "user", "content": prompt}]
    return react_with_llm(messages)

# Upload endpoint
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

        chunks = split_into_chunks(text)
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

# Other endpoints (chat, clear, search) can follow here unchanged.
