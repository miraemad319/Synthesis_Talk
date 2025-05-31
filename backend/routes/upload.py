# backend/routes/upload.py

from fastapi import APIRouter, File, UploadFile, Cookie, Response, Query, HTTPException
import uuid
import os

from backend.utils.file_extraction import extract_text_from_pdf, extract_text_from_txt, extract_text_from_docx
from backend.utils.chunking import split_into_chunks
from backend.utils.session_store import document_store, persist
from backend.utils.summarizer import summarize_text

# Import the in‐memory contexts and current context
from backend.routes.context import _contexts, _current_context

router = APIRouter()

@router.post("/upload/")
async def upload_file(
    response: Response,                   # so we can set cookies in the response
    file: UploadFile = File(...),         # The uploaded file
    session_id: str = Cookie(default=None),   # Read session_id from cookie (if any)
    format: str = Query(default="paragraph", enum=["paragraph", "bullets"])
):
    # 1) If no session_id was sent, create a new one
    is_new_session = False
    if session_id is None:
        session_id = str(uuid.uuid4())
        is_new_session = True

    print(f"[UPLOAD] Using session_id: {session_id}")

    # 2) Save the file temporarily to disk
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_upload_{uuid.uuid4()}.{file_ext}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # 3) Extract the text
        if file_ext == "pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext == "txt":
            text = extract_text_from_txt(temp_path)
        elif file_ext == "docx":
            text = extract_text_from_docx(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, TXT, or DOCX.")

        if text.startswith("Error"):
            raise HTTPException(status_code=400, detail=text)

        # 4) Chunk the text
        chunks = split_into_chunks(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="No content could be extracted from the file.")

        # 5) Store those chunks under this session_id
        document_store[session_id] = [(chunk, file.filename) for chunk in chunks]
        print(f"[UPLOAD] Storing {len(chunks)} chunks for session {session_id}")
        persist()

        # 6) Generate a summary
        try:
            summary = summarize_text(text, format=format)
        except Exception as e:
            print(f"[UPLOAD] Summary generation failed: {e}")
            summary = "Summary generation failed, but document was processed successfully."

        # 7) Append this filename into the CURRENT CONTEXT’s sources list
        #    We imported _contexts and _current_context from context.py
        for ctx in _contexts:
            if ctx["id"] == _current_context:
                ctx["sources"].append(file.filename)
                break

        # 8) Build the JSON response
        result = {
            "filename": file.filename,
            "summary": summary,
            "chunks": len(chunks)
        }

        # 9) If this is a brand‐new session, set the cookie so subsequent calls reuse it
        if is_new_session:
            response.set_cookie(key="session_id", value=session_id)

        return result

    except HTTPException:
        # Re‐raise FastAPI errors (400, etc.) so the client sees them
        raise

    except Exception as e:
        print(f"[UPLOAD] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {e}")

    finally:
        # 10) Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)



