# backend/routes/upload.py

from fastapi import APIRouter, File, UploadFile, Cookie, Response, Query, HTTPException
from fastapi.responses import JSONResponse
import uuid
import os
import hashlib
from typing import Optional

from backend.utils.file_extraction import extract_text_from_pdf, extract_text_from_txt, extract_text_from_docx
from backend.utils.chunking import split_into_chunks
from backend.utils.session_store import document_store, persist, add_document_metadata
from backend.utils.summarizer import summarize_text

# Import the in‐memory contexts and current context
from backend.routes.context import _contexts, _current_context, add_source_to_context

router = APIRouter()


@router.post("/upload/")
async def upload_file(
    response: Response,
    file: UploadFile = File(...),
    session_id: Optional[str] = Cookie(default=None),
    format: str = Query(default="paragraph", enum=["paragraph", "bullets"])
):
    """
    Enhanced file upload with better error handling, metadata tracking, and context management.
    """

    # 1) Validate file size and type
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_ext = file.filename.split(".")[-1].lower()
    supported_types = ["pdf", "txt", "docx"]
    if file_ext not in supported_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Supported types: {', '.join(supported_types)}"
        )

    # 2) Create or reuse session
    is_new_session = False
    if session_id is None:
        session_id = str(uuid.uuid4())
        is_new_session = True

    print(f"[UPLOAD] Processing file '{file.filename}' for session: {session_id}")

    # 3) Save the uploaded file to a temp location
    temp_path = f"temp_upload_{uuid.uuid4()}.{file_ext}"
    file_content = None

    try:
        file_content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(file_content)

        # 4) Compute a hash to detect duplicates
        file_hash = hashlib.md5(file_content).hexdigest()

        # 5) *** LENGTH‐AWARE DUPLICATE CHECK ***
        existing_docs = document_store.get(session_id, [])
        for entry in existing_docs:
            # If entry is not a tuple/list, skip it
            if not isinstance(entry, (list, tuple)):
                continue

            if len(entry) == 3:
                chunk, filename, metadata = entry
            elif len(entry) == 2:
                # Older entries were just (chunk, filename), no metadata
                chunk, filename = entry
                metadata = {}
            else:
                # Unexpected shape—skip
                continue

            if metadata.get("file_hash") == file_hash:
                raise HTTPException(
                    status_code=409,
                    detail=f"File '{file.filename}' appears to be a duplicate of '{filename}'"
                )

        # 6) Extract the text from PDF / TXT / DOCX
        extractors = {
            "pdf": extract_text_from_pdf,
            "txt": extract_text_from_txt,
            "docx": extract_text_from_docx
        }
        text = extractors[file_ext](temp_path)

        if text.startswith("Error"):
            raise HTTPException(status_code=422, detail=f"File processing error: {text}")

        if not text.strip():
            raise HTTPException(status_code=422, detail="No readable content found in the file.")

        # 7) Chunk the text
        chunks = split_into_chunks(text)
        if not chunks:
            raise HTTPException(status_code=422, detail="Could not extract meaningful content chunks.")

        # 8) Build metadata for this document
        metadata = {
            "file_hash": file_hash,
            "file_size": len(file_content),
            "chunk_count": len(chunks),
            "upload_timestamp": uuid.uuid4().hex[:8]  # Just a short unique token
        }

        # 9) Store each chunk as a 3-tuple: (chunk_text, filename, metadata)
        document_store[session_id] = [
            (chunk, file.filename, metadata) for chunk in chunks
        ]

        # 10) Also save the metadata (2-tuple) via helper
        add_document_metadata(session_id, file.filename, metadata)

        print(f"[UPLOAD] Stored {len(chunks)} chunks for session {session_id}")
        persist()

        # 11) Generate a summary (if possible)
        summary = "Summary generation failed, but document was processed successfully."
        try:
            summary = summarize_text(text, format=format)
        except Exception as e:
            print(f"[UPLOAD] Summary generation failed: {e}")

        # 12) Add this file to the current context
        add_source_to_context(_current_context, file.filename)

        # 13) Build the JSON response
        result = {
            "filename": file.filename,
            "summary": summary,
            "chunks": len(chunks),
            "file_size": len(file_content),
            "session_id": session_id
        }

        json_response = JSONResponse(content=result)
        if is_new_session:
            json_response.set_cookie(key="session_id", value=session_id, httponly=True)

        return json_response

    except HTTPException:
        # Re‐raise any FastAPI HTTPException we explicitly threw above
        raise

    except Exception as e:
        print(f"[UPLOAD] Unexpected error processing '{file.filename}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing file: {str(e)}"
        )

    finally:
        # 14) Clean up the temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"[UPLOAD] Warning: Could not remove temp file {temp_path}: {e}")


@router.get("/upload/history")
async def get_upload_history(session_id: Optional[str] = Cookie(default=None)):
    """
    Get upload history for the current session.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    docs = document_store.get(session_id, [])
    if not docs:
        return {"files": []}

    files_info = {}
    # *** LENGTH‐AWARE HISTORY LOOP ***
    for entry in docs:
        if not isinstance(entry, (list, tuple)):
            continue

        if len(entry) == 3:
            chunk, filename, metadata = entry
        elif len(entry) == 2:
            chunk, filename = entry
            metadata = {}
        else:
            continue

        if filename not in files_info:
            files_info[filename] = {
                "filename": filename,
                "chunks": metadata.get("chunk_count", 0),
                "file_size": metadata.get("file_size", 0),
                "upload_time": metadata.get("upload_timestamp", "unknown")
            }

    return {"files": list(files_info.values())}


@router.delete("/upload/{filename}")
async def remove_document(
    filename: str,
    session_id: Optional[str] = Cookie(default=None)
):
    """
    Remove a specific document from the session.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found")

    remaining_entries = []
    found = False

    # *** LENGTH‐AWARE DELETION LOOP ***
    for entry in docs:
        if not isinstance(entry, (list, tuple)):
            # If it isn’t a tuple/list, skip it entirely
            continue

        if len(entry) == 3:
            chunk, fname, metadata = entry
        elif len(entry) == 2:
            chunk, fname = entry
            metadata = {}
        else:
            continue

        if fname == filename:
            found = True
            # Skip adding this entry to remaining_entries
            continue
        # Otherwise, keep it
        remaining_entries.append((chunk, fname, metadata))

    if not found:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in session")

    document_store[session_id] = remaining_entries
    persist()

    return {"message": f"Successfully removed '{filename}' from session"}
