from fastapi import APIRouter, Cookie, Body, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import logging
from datetime import datetime

from backend.utils.session_store import conversation_histories, document_store, tool_usage_log, persist
from backend.llm import react_with_llm, tool_manager
from backend.utils.concept_linker import find_relevant_chunks

router = APIRouter()
logger = logging.getLogger(__name__)

class NoteInput(BaseModel):
    note: str
    category: str = "general"
    tags: List[str] = []

class ExplainInput(BaseModel):
    query: str
    detail_level: str = "medium"  # simple, medium, detailed
    format: str = "paragraph"     # paragraph, bullets, structured

class OrganizeInput(BaseModel):
    content_type: str = "notes"   # notes, documents, insights
    organization_method: str = "topic"  # topic, chronological, priority

class AnalysisRequest(BaseModel):
    analysis_type: str  # summary, comparison, trend, pattern
    focus_areas: List[str] = []
    output_format: str = "structured"

# Tool usage tracking
tool_usage_log: Dict[str, List[Dict]] = {}

def log_tool_usage(session_id: str, tool_name: str, input_data: Any, success: bool = True):
    """Log tool usage for analytics and debugging."""
    if session_id not in tool_usage_log:
        tool_usage_log[session_id] = []
    
    log_entry = {
        "tool": tool_name,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "input_summary": str(input_data)[:100] + "..." if len(str(input_data)) > 100 else str(input_data)
    }
    
    tool_usage_log[session_id].append(log_entry)
    
    # Keep only last 50 entries per session
    if len(tool_usage_log[session_id]) > 50:
        tool_usage_log[session_id] = tool_usage_log[session_id][-50:]

@router.post("/tools/note/")
def save_note(note_input: NoteInput, session_id: str = Cookie(default=None)):
    """
    Enhanced note-taking with categorization and tagging.
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session ID")

        # Create structured note
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_metadata = {
            "category": note_input.category,
            "tags": note_input.tags,
            "timestamp": timestamp
        }
        
        note_text = f"[NOTE - {note_input.category.upper()}] {note_input.note}"
        if note_input.tags:
            note_text += f" #{'#'.join(note_input.tags)}"
        
        conversation_histories.setdefault(session_id, []).append({
            "role": "user", 
            "content": note_text,
            "metadata": note_metadata
        })
        
        persist()
        log_tool_usage(session_id, "note_taker", note_input.dict())
        
        return {
            "message": "Note saved successfully",
            "note_id": len(conversation_histories[session_id]) - 1,
            "metadata": note_metadata
        }
        
    except Exception as e:
        log_tool_usage(session_id, "note_taker", note_input.dict(), success=False)
        logger.error(f"[TOOLS] Note saving failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save note: {str(e)}")

@router.post("/tools/explain/")
def explain_query(explain_input: ExplainInput, session_id: str = Cookie(default=None)):
    """
    Enhanced explanation tool with customizable detail levels and formats.
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session ID")

        # Customize explanation based on detail level
        detail_prompts = {
            "simple": "Please explain the following concept in very simple terms, as if explaining to a beginner:",
            "medium": "Please explain the following concept with moderate detail, including key points and examples:",
            "detailed": "Please provide a comprehensive explanation of the following concept, including background, details, examples, and implications:"
        }
        
        base_prompt = detail_prompts.get(explain_input.detail_level, detail_prompts["medium"])
        
        # Format specification
        format_instructions = {
            "paragraph": "Present your explanation in well-structured paragraphs.",
            "bullets": "Present your explanation using bullet points and sub-bullets for organization.",
            "structured": "Use a structured format with clear headings and sections."
        }
        
        format_instruction = format_instructions.get(explain_input.format, format_instructions["paragraph"])
        
        # Build the complete query
        query = f"{base_prompt}\n\n{explain_input.query}\n\n{format_instruction}"
        
        # Get relevant document context
        relevant_chunks = []
        if session_id in document_store:
            relevant_chunks = find_relevant_chunks(explain_input.query, document_store[session_id])
        
        # Add context if available
        if relevant_chunks:
            context = "\n".join(f"[From {fname}] {chunk}" for chunk, fname in relevant_chunks)
            query += f"\n\nRelevant context from your documents:\n{context[:1500]}"
        
        conversation_histories.setdefault(session_id, []).append({
            "role": "user",
            "content": query
        })

        response = react_with_llm(conversation_histories[session_id])

        conversation_histories[session_id].append({
            "role": "assistant",
            "content": response
        })

        persist()
        log_tool_usage(session_id, "explainer", explain_input.dict())
        
        return {
            "response": response,
            "detail_level": explain_input.detail_level,
            "format": explain_input.format,
            "context_used": len(relevant_chunks) > 0
        }
        
    except Exception as e:
        log_tool_usage(session_id, "explainer", explain_input.dict(), success=False)
        logger.error(f"[TOOLS] Explanation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")

@router.post("/tools/organize/")
def organize_content(organize_input: OrganizeInput, session_id: str = Cookie(default=None)):
    """
    Organize and structure existing content (notes, documents, insights).
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session ID")

        # Get session content
        conversation_history = conversation_histories.get(session_id, [])
        documents = document_store.get(session_id, [])
        
        if not conversation_history and not documents:
            return {"message": "No content found to organize", "organized_content": {}}

        # Extract content based on type
        content_to_organize = []
        
        if organize_input.content_type == "notes":
            # Extract notes from conversation
            for msg in conversation_history:
                if msg["role"] == "user" and msg["content"].startswith("[NOTE"):
                    content_to_organize.append(msg["content"])
        
        elif organize_input.content_type == "documents":
            # Include document summaries
            for chunk, filename in documents:
                content_to_organize.append(f"[From {filename}] {chunk[:200]}...")
        
        elif organize_input.content_type == "insights":
            # Extract assistant insights and responses
            for msg in conversation_history:
                if msg["role"] == "assistant" and len(msg["content"]) > 100:
                    content_to_organize.append(msg["content"][:300] + "...")

        if not content_to_organize:
            return {"message": f"No {organize_input.content_type} found to organize", "organized_content": {}}

        # Create organization prompt
        organization_prompt = f"""
        Please organize the following {organize_input.content_type} using the {organize_input.organization_method} method.
        
        Content to organize:
        {chr(10).join(content_to_organize[:10])}  # Limit to first 10 items
        
        Organization method: {organize_input.organization_method}
        
        Please provide a well-structured organization with clear categories, headings, and logical groupings.
        Return the result as a JSON object with organized categories.
        """
        
        organization_history = [{"role": "user", "content": organization_prompt}]
        organization_result = react_with_llm(organization_history)
        
        # Try to parse as JSON, fallback to text
        try:
            organized_data = json.loads(organization_result)
        except json.JSONDecodeError:
            organized_data = {"organized_text": organization_result}
        
        # Log the organization
        conversation_histories[session_id].append({
            "role": "system",
            "content": f"[ORGANIZATION] Content organized by {organize_input.organization_method}: {len(content_to_organize)} items processed"
        })
        
        persist()
        log_tool_usage(session_id, "organizer", organize_input.dict())
        
        return {
            "message": f"Successfully organized {len(content_to_organize)} items",
            "method": organize_input.organization_method,
            "organized_content": organized_data
        }
        
    except Exception as e:
        log_tool_usage(session_id, "organizer", organize_input.dict(), success=False)
        logger.error(f"[TOOLS] Content organization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Organization failed: {str(e)}")

@router.post("/tools/analyze/")
def perform_analysis(analysis_request: AnalysisRequest, session_id: str = Cookie(default=None)):
    """
    Perform various types of analysis on session content.
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session ID")

        # Get all available content
        conversation_history = conversation_histories.get(session_id, [])
        documents = document_store.get(session_id, [])
        
        # Prepare content for analysis
        all_content = []
        
        # Include conversation content
        for msg in conversation_history:
            if msg["role"] in ["user", "assistant"] and len(msg["content"]) > 50:
                all_content.append(msg["content"])
        
        # Include document content
        for chunk, filename in documents:
            all_content.append(f"[Document: {filename}] {chunk}")
        
        if not all_content:
            return {"message": "No content available for analysis", "analysis": {}}

        # Create analysis prompt based on type
        analysis_prompts = {
            "summary": "Provide a comprehensive summary of all the content, highlighting key themes and insights.",
            "comparison": "Compare and contrast the different ideas, sources, and perspectives present in the content.",
            "trend": "Identify trends, patterns, and developments over time in the content.",
            "pattern": "Analyze patterns, relationships, and connections between different pieces of information."
        }
        
        base_prompt = analysis_prompts.get(analysis_request.analysis_type, analysis_prompts["summary"])
        
        analysis_prompt = f"""
        {base_prompt}
        
        Focus areas: {', '.join(analysis_request.focus_areas) if analysis_request.focus_areas else 'General analysis'}
        Output format: {analysis_request.output_format}
        
        Content to analyze:
        {chr(10).join(all_content[:15])}  # Limit content length
        
        Please provide a thorough {analysis_request.analysis_type} analysis.
        """
        
        analysis_history = [{"role": "user", "content": analysis_prompt}]
        analysis_result = react_with_llm(analysis_history)
        
        # Store analysis in conversation
        conversation_histories[session_id].append({
            "role": "assistant",
            "content": f"[ANALYSIS - {analysis_request.analysis_type.upper()}]\n{analysis_result}"
        })
        
        persist()
        log_tool_usage(session_id, "analyzer", analysis_request.dict())
        
        return {
            "analysis_type": analysis_request.analysis_type,
            "focus_areas": analysis_request.focus_areas,
            "analysis": analysis_result,
            "content_pieces_analyzed": len(all_content)
        }
        
    except Exception as e:
        log_tool_usage(session_id, "analyzer", analysis_request.dict(), success=False)
        logger.error(f"[TOOLS] Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/tools/available/")
def get_available_tools():
    """
    Get information about all available research tools.
    """
    return {
        "tools": tool_manager.get_available_tools(),
        "categories": {
            "note_management": ["note_taker"],
            "analysis": ["explainer", "analyzer"],
            "organization": ["organizer"],
            "research": ["document_analyzer", "web_searcher", "concept_linker"]
        }
    }

@router.get("/tools/recommendations/")
def get_tool_recommendations(
    query: str,
    session_id: str = Cookie(default=None)
):
    """
    Get tool recommendations based on the current query and session context.
    """
    try:
        # Get session context
        context = ""
        if session_id and session_id in conversation_histories:
            recent_messages = conversation_histories[session_id][-5:]  # Last 5 messages
            context = "\n".join(msg["content"] for msg in recent_messages)
        
        recommendations = tool_manager.get_tool_recommendations(query, context)
        
        return {
            "query": query,
            "recommended_tools": recommendations,
            "context_considered": bool(context)
        }
        
    except Exception as e:
        logger.error(f"[TOOLS] Tool recommendation failed: {e}")
        return {"recommended_tools": [], "error": str(e)}

@router.get("/tools/usage/")
def get_tool_usage_stats(session_id: str = Cookie(default=None)):
    """
    Get tool usage statistics for the current session.
    """
    if not session_id or session_id not in tool_usage_log:
        return {"usage_stats": {}}
    
    usage_data = tool_usage_log[session_id]
    
    # Calculate statistics
    tool_counts = {}
    success_rates = {}
    
    for entry in usage_data:
        tool = entry["tool"]
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        if tool not in success_rates:
            success_rates[tool] = {"successful": 0, "failed": 0}
        
        if entry["success"]:
            success_rates[tool]["successful"] += 1
        else:
            success_rates[tool]["failed"] += 1
    
    return {
        "total_tool_uses": len(usage_data),
        "tool_usage_counts": tool_counts,
        "success_rates": success_rates,
        "recent_usage": usage_data[-10:]  # Last 10 uses
    }
