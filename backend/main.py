import os
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# === TEXT EXTRACTION FUNCTIONS ===

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# === FASTAPI SETUP ===

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "SynthesisTalk backend is running."}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_upload.{file_ext}"

    # Save uploaded file
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    if file_ext == "pdf":
        text = extract_text_from_pdf(temp_path)
    elif file_ext == "txt":
        text = extract_text_from_txt(temp_path)
    else:
        os.remove(temp_path)
        return {"error": "Unsupported file type"}

    os.remove(temp_path)

    return {"filename": file.filename, "content": text[:1000]}

