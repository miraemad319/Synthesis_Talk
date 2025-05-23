from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pdfminer.high_level import extract_text
import os
import uuid
from docx import Document
from pydantic import BaseModel
from llm import chat_with_llm

conversation_history = []

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
        # Save the uploaded file temporarily
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text based on file type
        if file_ext == "pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext == "txt":
            text = extract_text_from_txt(temp_path)
        elif file_ext == "docx":
            text = extract_text_from_docx(temp_path)
        else:
            return {"error": "Unsupported file type. Please upload PDF, TXT, or DOCX."}

        return {"filename": file.filename, "content": text[:1000]}  # Return first 1000 chars

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat/")
async def chat(message: Message):
    conversation_history.append({"role": "user", "content": message.content})
    reply = chat_with_llm(conversation_history)
    conversation_history.append({"role": "assistant", "content": reply})
    return {"response": reply}
