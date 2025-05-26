from fastapi import APIRouter, Cookie
from fastapi.responses import FileResponse
import os
from ..utils.session_store import conversation_histories
from datetime import datetime

router = APIRouter()

@router.get("/export/")
def export_conversation(session_id: str = Cookie(default=None), format: str = "txt"):
    if not session_id or session_id not in conversation_histories:
        return {"error": "No session found"}

    conversation = conversation_histories[session_id]
    export_text = ""
    for msg in conversation:
        export_text += f"{msg['role'].capitalize()}:\n{msg['content']}\n\n"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.{format}"
    filepath = os.path.join("exports", filename)

    os.makedirs("exports", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(export_text)

    return FileResponse(filepath, media_type="text/plain", filename=filename)
