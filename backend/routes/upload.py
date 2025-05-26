from fastapi import APIRouter, File, UploadFile, Cookie
import uuid
import os

# Import utility functions for file reading, chunking, session storage, and summarization
from ..utils.file_extraction import extract_text_from_pdf, extract_text_from_txt, extract_text_from_docx
from ..utils.chunking import split_into_chunks
from ..utils.session_store import document_store, persist
from ..utils.summarizer import summarize_text

# Create a router to group upload-related endpoints
router = APIRouter()

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),            # The uploaded file (PDF, DOCX, TXT)
    session_id: str = Cookie(default=None)   # Track user sessions via cookie
):
    # Create a new session ID if not already provided
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Extract file extension (e.g., pdf, txt, docx)
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_upload_{uuid.uuid4()}.{file_ext}"

    try:
        # Save uploaded file temporarily to disk
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text depending on file type
        if file_ext == "pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext == "txt":
            text = extract_text_from_txt(temp_path)
        elif file_ext == "docx":
            text = extract_text_from_docx(temp_path)
        else:
            return {"error": "Unsupported file type. Please upload PDF, TXT, or DOCX."}

        # Break text into smaller chunks (used later for context-aware LLM responses)
        chunks = split_into_chunks(text)

        # Store each chunk associated with the session ID and original filename
        for chunk in chunks:
            document_store[session_id].append((chunk, file.filename))

        # Save document state after upload
        persist()

        # Generate a summary of the full document using LLM
        summary = summarize_text(text)

        # Return file info, number of chunks, and summary
        return {
            "filename": file.filename,
            "summary": summary,
            "chunks": len(chunks)
        }

    except Exception as e:
        # Catch and return any unexpected errors
        return {"error": str(e)}

    finally:
        # Clean up by removing the temporary uploaded file
        if os.path.exists(temp_path):
            os.remove(temp_path)

