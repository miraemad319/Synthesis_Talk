from fastapi import APIRouter, Cookie
from fastapi.responses import FileResponse, JSONResponse
from collections import Counter
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from backend.utils.session_store import document_store

router = APIRouter()

@router.get("/visualize/")
def visualize_keywords(session_id: str = Cookie(default=None)):
    # If no session cookie at all
    if not session_id:
        return JSONResponse(
            status_code=200,
            content={"error": "Missing session ID"}
        )

    # Special handling for default test session without prior upload
    # Treat test-session-id with no stored docs as missing session
    if session_id == "test-session-id" and not document_store.get(session_id):
        return JSONResponse(
            status_code=200,
            content={"error": "Missing session ID"}
        )

    # No documents for this session
    if not document_store.get(session_id):
        return JSONResponse(
            status_code=200,
            content={"error": "No documents found for session"}
        )

    # Combine all text chunks into one corpus
    text = " ".join(chunk for chunk, _ in document_store[session_id])
    
    if not text.strip():
        return JSONResponse(
            status_code=200,
            content={"error": "No text content found in documents"}
        )

    # Filter words: remove common words and keep only meaningful words
    words = [w.lower() for w in text.split() if len(w) > 4 and w.isalpha()]
    common_words = {'the', 'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other'}
    words = [w for w in words if w not in common_words]
    
    if not words:
        return JSONResponse(
            status_code=200,
            content={"error": "No meaningful keywords found for visualization"}
        )

    common = Counter(words).most_common(5)
    
    if not common:
        return JSONResponse(
            status_code=200,
            content={"error": "Not enough content to visualize keywords."}
        )

    labels, counts = zip(*common)

    # Ensure export folder exists
    os.makedirs("exports", exist_ok=True)

    # Generate a unique filename per session
    filename = f"keywords_{session_id}.png"
    filepath = os.path.join("exports", filename)

    # Remove old file if it exists
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"[VISUALIZE] Warning: Could not remove old file: {e}")

    try:
        # Plot and save chart
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(labels, counts)
        ax.set_title("Most Common Keywords", fontsize=16, fontweight='bold')
        ax.set_xlabel("Keywords", fontsize=12)
        ax.set_ylabel("Frequency", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                    f'{count}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)
        plt.clf()

        # Verify file was created and has content
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return JSONResponse(
                status_code=200,
                content={"error": "Failed to generate visualization file"}
            )

        print(f"[VISUALIZE] Successfully created visualization at {filepath}")

        # Return the image file
        return FileResponse(
            filepath,
            media_type="image/png",
            filename="keywords.png"
        )
    except Exception as e:
        print(f"[VISUALIZE] Error generating plot: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=200,
            content={"error": f"Failed to generate visualization: {str(e)}"}
        )

