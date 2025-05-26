from fastapi import APIRouter, Cookie
from fastapi.responses import FileResponse
from collections import Counter
import os
import matplotlib.pyplot as plt
from ..utils.session_store import document_store

router = APIRouter()

@router.get("/visualize/")
def visualize_keywords(session_id: str = Cookie(default=None)):
    if not session_id or session_id not in document_store:
        return {"error": "No documents found"}

    # Combine all text chunks into one corpus
    text = " ".join(chunk for chunk, _ in document_store[session_id])
    words = [w.lower() for w in text.split() if len(w) > 4]
    common = Counter(words).most_common(5)

    labels, counts = zip(*common)

    # Plot bar chart
    plt.figure(figsize=(8, 5))
    plt.bar(labels, counts)
    plt.title("Most Common Keywords")
    plt.xlabel("Keywords")
    plt.ylabel("Frequency")
    filepath = f"exports/keywords_{session_id}.png"
    os.makedirs("exports", exist_ok=True)
    plt.savefig(filepath)
    plt.close()

    return FileResponse(filepath, media_type="image/png", filename="keywords.png")
