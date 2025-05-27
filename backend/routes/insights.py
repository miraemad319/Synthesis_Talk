# routes/insights.py
from fastapi import APIRouter, Cookie
from backend.utils.session_store import document_store, conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()

@router.get("/insights/")
def generate_insights(session_id: str = Cookie(default=None)):
    """
    Analyze all uploaded documents and generate research insights based on patterns.
    """
    if not session_id:
        return {"error": "Missing session ID"}

    print(f"[INSIGHTS] Checking session: {session_id}")
    print(f"[INSIGHTS] Available sessions: {list(document_store.keys())}")
    print(f"[INSIGHTS] Session data: {document_store.get(session_id, 'NOT FOUND')}")

    if session_id not in document_store or not document_store[session_id]:
        return {"error": "No documents found for session"}

    # Combine all text chunks
    all_text = "\n".join(chunk for chunk, _ in document_store[session_id])

    if not all_text.strip():
        return {"error": "No content available for generating insights."}

    prompt = (
        "Analyze the following collection of text and extract useful insights, "
        "connections between ideas, or patterns that are worth noting. Be concise and informative.\n\n"
        f"{all_text[:3000]}"
    )

    # Initialize conversation history for this session if it doesn't exist
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Create a temporary conversation for the insights request
    temp_messages = [{"role": "user", "content": prompt}]

    try:
        response = react_with_llm(temp_messages)
        
        # Store the insights request and response in conversation history
        conversation_histories[session_id].append({"role": "user", "content": f"[INSIGHTS REQUEST] {prompt[:100]}..."})
        conversation_histories[session_id].append({"role": "assistant", "content": response})
        persist()

        return {"insights": response}
        
    except Exception as e:
        print(f"[INSIGHTS] Error generating insights: {e}")
        return {"error": f"Failed to generate insights: {str(e)}"}
