# backend/routes/context.py

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Cookie
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.utils.session_store import document_store, conversation_histories, persist

router = APIRouter()

# Pydantic models for request/response
class SwitchContextRequest(BaseModel):
    context_id: str

class CreateContextRequest(BaseModel):
    topic: str
    description: Optional[str] = ""

class UpdateContextRequest(BaseModel):
    context_id: str
    topic: Optional[str] = None
    description: Optional[str] = None

class ContextResponse(BaseModel):
    id: str
    topic: str
    description: str
    sources: List[str]
    created_at: str
    last_active: str
    message_count: int
    document_count: int

# Enhanced in-memory storage with metadata
_contexts = [
    {
        "id": "default",
        "topic": "Getting Started",
        "description": "Initial research context for new sessions",
        "sources": [],
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "message_count": 0,
        "document_count": 0
    }
]
_current_context: Optional[str] = "default"

def _update_context_activity(context_id: str):
    """Update the last_active timestamp for a context"""
    for ctx in _contexts:
        if ctx["id"] == context_id:
            ctx["last_active"] = datetime.now().isoformat()
            break

def _get_context_stats(context_id: str) -> Dict[str, int]:
    """Get statistics for a context (message count, document count)"""
    message_count = len(conversation_histories.get(context_id, []))
    document_count = len(set(filename for _, filename in document_store.get(context_id, [])))
    return {"message_count": message_count, "document_count": document_count}

def add_source_to_context(context_id: str, source_filename: str):
    """
    Add a source document to a specific context.
    Updates the context's sources list and activity timestamp.
    """
    for ctx in _contexts:
        if ctx["id"] == context_id:
            if source_filename not in ctx["sources"]:
                ctx["sources"].append(source_filename)
            ctx["document_count"] = len(ctx["sources"])
            _update_context_activity(context_id)
            break

@router.get("/context/", response_model=Dict[str, Any])
async def get_contexts():
    """
    Return all available contexts with enhanced metadata and statistics.
    Response includes current context and detailed information about each context.
    """
    # Update context statistics
    for ctx in _contexts:
        stats = _get_context_stats(ctx["id"])
        ctx.update(stats)
        
        # Update sources list from document store
        docs = document_store.get(ctx["id"], [])
        ctx["sources"] = list(set(filename for _, filename in docs))
    
    return {
        "contexts": _contexts,
        "current": _current_context,
        "total_contexts": len(_contexts),
        "active_sessions": len([ctx for ctx in _contexts if ctx["message_count"] > 0])
    }

@router.post("/context/switch", response_model=Dict[str, str])
async def switch_context(request: SwitchContextRequest):
    """
    Switch to a different research context.
    Updates the active context and tracks activity.
    """
    global _current_context

    # Verify the requested ID exists
    context_ids = {ctx["id"] for ctx in _contexts}
    if request.context_id not in context_ids:
        raise HTTPException(status_code=400, detail="Invalid context_id")

    _current_context = request.context_id
    _update_context_activity(request.context_id)
    
    return {
        "current": _current_context,
        "message": f"Switched to context: {request.context_id}"
    }

@router.post("/context/create", response_model=ContextResponse)
async def create_context(request: CreateContextRequest):
    """
    Create a new research context with specified topic and description.
    Each context maintains separate conversation history and document store.
    """
    new_context_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    
    new_context = {
        "id": new_context_id,
        "topic": request.topic,
        "description": request.description,
        "sources": [],
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "message_count": 0,
        "document_count": 0
    }
    
    _contexts.append(new_context)
    
    # Initialize empty stores for the new context
    conversation_histories[new_context_id] = []
    document_store[new_context_id] = []
    
    persist()  # Save to disk
    
    return ContextResponse(**new_context)

@router.put("/context/{context_id}", response_model=ContextResponse)
async def update_context(context_id: str, request: UpdateContextRequest):
    """
    Update an existing context's metadata (topic, description).
    """
    context = None
    for ctx in _contexts:
        if ctx["id"] == context_id:
            context = ctx
            break
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Update fields if provided
    if request.topic is not None:
        context["topic"] = request.topic
    if request.description is not None:
        context["description"] = request.description
    
    _update_context_activity(context_id)
    persist()
    
    # Update statistics
    stats = _get_context_stats(context_id)
    context.update(stats)
    
    return ContextResponse(**context)

@router.delete("/context/{context_id}")
async def delete_context(context_id: str):
    """
    Delete a research context and all associated data.
    Cannot delete the default context or currently active context.
    """
    global _current_context
    
    if context_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default context")
    
    if context_id == _current_context:
        raise HTTPException(status_code=400, detail="Cannot delete currently active context")
    
    # Find and remove the context
    context_found = False
    for i, ctx in enumerate(_contexts):
        if ctx["id"] == context_id:
            _contexts.pop(i)
            context_found = True
            break
    
    if not context_found:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Clean up associated data
    if context_id in conversation_histories:
        del conversation_histories[context_id]
    if context_id in document_store:
        del document_store[context_id]
    
    persist()
    
    return {"message": f"Context {context_id} deleted successfully"}

@router.get("/context/{context_id}/summary")
async def get_context_summary(context_id: str):
    """
    Get a detailed summary of a specific research context.
    Includes conversation overview, document analysis, and activity metrics.
    """
    context = None
    for ctx in _contexts:
        if ctx["id"] == context_id:
            context = ctx.copy()
            break
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Get conversation summary
    conversation = conversation_histories.get(context_id, [])
    recent_messages = conversation[-5:] if conversation else []
    
    # Get document summary
    docs = document_store.get(context_id, [])
    doc_sources = list(set(filename for _, filename in docs))
    total_content_length = sum(len(chunk) for chunk, _ in docs)
    
    # Calculate activity metrics
    if conversation:
        user_messages = len([msg for msg in conversation if msg["role"] == "user"])
        assistant_messages = len([msg for msg in conversation if msg["role"] == "assistant"])
        avg_message_length = sum(len(msg["content"]) for msg in conversation) // len(conversation)
    else:
        user_messages = assistant_messages = avg_message_length = 0
    
    summary = {
        "context": context,
        "conversation_summary": {
            "total_messages": len(conversation),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "avg_message_length": avg_message_length,
            "recent_messages": [
                {
                    "role": msg["role"],
                    "preview": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                    "timestamp": msg.get("timestamp", "")
                }
                for msg in recent_messages
            ]
        },
        "document_summary": {
            "total_documents": len(doc_sources),
            "document_sources": doc_sources,
            "total_chunks": len(docs),
            "total_content_length": total_content_length,
            "avg_chunk_size": total_content_length // len(docs) if docs else 0
        },
        "activity_metrics": {
            "created_at": context["created_at"],
            "last_active": context["last_active"],
            "is_active": context_id == _current_context,
            "research_intensity": len(conversation) + len(docs)  # Simple activity score
        }
    }
    
    return summary

@router.post("/context/{context_id}/archive")
async def archive_context(context_id: str):
    """
    Archive a context (mark as inactive but preserve data).
    Archived contexts are not shown in the main context list but can be restored.
    """
    context = None
    for ctx in _contexts:
        if ctx["id"] == context_id:
            context = ctx
            break
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    if context_id == "default":
        raise HTTPException(status_code=400, detail="Cannot archive default context")
    
    context["archived"] = True
    context["archived_at"] = datetime.now().isoformat()
    
    persist()
    
    return {"message": f"Context {context_id} archived successfully"}

@router.get("/context/current")
async def get_current_context():
    """
    Get detailed information about the currently active context.
    """
    if not _current_context:
        raise HTTPException(status_code=400, detail="No active context")
    
    for ctx in _contexts:
        if ctx["id"] == _current_context:
            stats = _get_context_stats(_current_context)
            ctx.update(stats)
            
            # Add real-time source information
            docs = document_store.get(_current_context, [])
            ctx["sources"] = list(set(filename for _, filename in docs))
            
            return {
                "current_context": ctx,
                "is_active": True,
                "last_updated": datetime.now().isoformat()
            }
    
    raise HTTPException(status_code=404, detail="Current context not found")
