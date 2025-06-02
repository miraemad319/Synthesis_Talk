# IMMEDIATE FIX 1: backend/routes/chat.py
# Replace your current chat.py with this simplified version that actually works

from fastapi import APIRouter, Request, HTTPException, Body, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import logging
import time

# Import the upload system's storage to bridge the gap temporarily
try:
    from backend.routes.upload import simple_document_store
except ImportError:
    simple_document_store = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    use_reasoning: Optional[bool] = True

# Simple conversation storage that syncs with upload
chat_conversations = {}

def get_session_documents(session_id: str) -> list:
    """Get documents for session from upload system"""
    return simple_document_store.get(session_id, [])

def simple_ai_response(user_message: str, session_id: str) -> str:
    """Fixed AI response with proper document awareness"""
    message_lower = user_message.lower()
    
    # Get documents from upload system
    docs = get_session_documents(session_id)
    doc_count = len(docs)
    
    logger.info(f"[CHAT] Session {session_id} has {doc_count} documents")
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey']):
        if doc_count > 0:
            doc_names = [doc.get('filename', 'Unknown') for doc in docs]
            return f"Hello! I'm SynthesisTalk, your AI research assistant. I can see you have {doc_count} document(s) uploaded: {', '.join(doc_names)}. How can I help you analyze your research today?"
        else:
            return "Hello! I'm SynthesisTalk, your AI research assistant. You haven't uploaded any documents yet. Upload some files to get started with analysis!"
    
    elif any(word in message_lower for word in ['document', 'file', 'upload', 'what do i have']):
        if doc_count > 0:
            doc_info = []
            for doc in docs:
                filename = doc.get('filename', 'Unknown')
                chunks = doc.get('chunk_count', len(doc.get('chunks', [])))
                doc_info.append(f"📄 {filename} ({chunks} chunks)")
            
            return f"You have {doc_count} document(s) uploaded:\n\n" + "\n".join(doc_info) + f"\n\nI can analyze these documents, extract key themes, answer questions about their content, or help you understand the relationships between different concepts."
        else:
            return "You haven't uploaded any documents yet. Try uploading a PDF, DOCX, or TXT file using the upload area above to get started with document analysis."
    
    elif any(word in message_lower for word in ['analyze', 'analysis', 'summarize', 'summary']):
        if doc_count > 0:
            # Provide basic analysis based on available documents
            total_chunks = sum(len(doc.get('chunks', [])) for doc in docs)
            doc_names = [doc.get('filename', 'Unknown') for doc in docs]
            
            return f"I can analyze your {doc_count} uploaded document(s): {', '.join(doc_names)}.\n\nThese documents contain {total_chunks} chunks of text that I can analyze. Here's what I can help with:\n\n• Extract key themes and concepts\n• Summarize main points\n• Find connections between ideas\n• Answer specific questions about the content\n• Generate insights and recommendations\n\nWhat specific type of analysis would you like me to perform?"
        else:
            return "I'd be happy to help with analysis! Please upload some documents first using the upload area above, then I can analyze their content, extract themes, and answer questions about your research."
    
    elif any(word in message_lower for word in ['help', 'what can you do']):
        doc_status = f"You currently have {doc_count} document(s) uploaded." if doc_count > 0 else "No documents uploaded yet."
        return f"I'm SynthesisTalk, your AI research assistant! {doc_status}\n\nHere's what I can help you with:\n\n📄 **Document Analysis**: Upload PDFs, DOCX, or TXT files for analysis\n🔍 **Research Insights**: Extract themes, patterns, and key concepts\n📊 **Visualizations**: Create charts and graphs from your data\n🔗 **Connections**: Find relationships between different ideas\n📝 **Summaries**: Generate structured summaries and reports\n🧠 **Q&A**: Answer questions about your uploaded content\n\nWhat would you like to explore?"
    
    # If we have documents, provide context-aware responses
    if doc_count > 0:
        # Basic content search through documents
        relevant_content = []
        search_terms = user_message.lower().split()
        
        for doc in docs:
            chunks = doc.get('chunks', [])
            filename = doc.get('filename', 'Unknown')
            
            for chunk in chunks[:3]:  # Check first 3 chunks per document
                chunk_lower = chunk.lower()
                if any(term in chunk_lower for term in search_terms if len(term) > 3):
                    relevant_content.append(f"From {filename}: {chunk[:200]}...")
        
        if relevant_content:
            response = f"Based on your {doc_count} uploaded document(s), here's what I found related to '{user_message}':\n\n"
            response += "\n\n".join(relevant_content[:2])  # Show top 2 matches
            response += f"\n\nI can provide more detailed analysis or answer specific questions about this content."
            return response
        else:
            return f"I searched through your {doc_count} uploaded document(s) but didn't find specific content matching '{user_message}'. Try asking about:\n\n• General themes or topics in the documents\n• Specific concepts you're researching\n• Summaries or overviews\n• Key findings or insights\n\nWhat would you like to know about your research materials?"
    else:
        return f"I understand you're asking about: '{user_message}'\n\nI'd be happy to help! However, I don't see any uploaded documents yet. To provide the most relevant and detailed response, try uploading some research documents first using the upload area above.\n\nOnce you upload documents, I can:\n• Answer questions based on your specific content\n• Provide targeted analysis and insights\n• Extract relevant information from your documents"

@router.post("/chat/")
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    """Fixed chat endpoint with proper document integration"""
    start_time = time.time()
    user_message = chat_request.message
    
    logger.info(f"[CHAT] Starting chat for session: {session_id}")
    logger.info(f"[CHAT] User message: {user_message}")

    # Create new session if needed
    is_new_session = False
    if session_id is None:
        session_id = str(uuid.uuid4())
        is_new_session = True
        logger.info(f"[CHAT] Created new session: {session_id}")

    # Initialize conversation history
    if session_id not in chat_conversations:
        chat_conversations[session_id] = []

    # Add user message to history
    user_entry = {
        "role": "user", 
        "content": user_message,
        "timestamp": time.time()
    }
    chat_conversations[session_id].append(user_entry)

    try:
        # Generate AI response with document awareness
        logger.info("[CHAT] Generating AI response with document awareness...")
        assistant_reply = simple_ai_response(user_message, session_id)
        processing_time = time.time() - start_time
        
        logger.info(f"[CHAT] Response generated in {processing_time:.2f}s")

        # Save assistant's reply
        assistant_entry = {
            "role": "assistant", 
            "content": assistant_reply,
            "timestamp": time.time(),
            "processing_time": processing_time
        }
        chat_conversations[session_id].append(assistant_entry)

        # FIXED: Return proper string response, not object
        response_data = {
            "reply": assistant_reply,  # This should be a string
            "reasoning_steps": [],
            "used_reasoning": False,
            "session_id": session_id,
            "processing_time": f"{processing_time:.2f}s",
            "success": True
        }

        json_response = JSONResponse(content=response_data)
        if is_new_session:
            json_response.set_cookie(key="session_id", value=session_id, httponly=True)
        
        logger.info(f"[CHAT] Chat completed successfully in {processing_time:.2f}s")
        return json_response

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"[CHAT] Error after {processing_time:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = Cookie(default=None)):
    """Get conversation history for the current session."""
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")
    
    history = chat_conversations.get(session_id, [])
    return {"history": history, "session_id": session_id}