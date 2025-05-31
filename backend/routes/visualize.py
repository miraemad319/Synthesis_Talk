# backend/routes/visualize.py

from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import JSONResponse
from collections import Counter, defaultdict
from typing import Optional, Dict, Any, List
import re
from datetime import datetime

from backend.utils.session_store import document_store, conversation_histories
from backend.llm import react_with_llm

router = APIRouter()

@router.get("/visualize/keywords")
async def visualize_keywords(
    session_id: str = Cookie(default=None),
    top_k: int = Query(default=10, description="Number of top keywords to return")
):
    """
    Extract and visualize the most frequent keywords from uploaded documents.
    Returns data suitable for word cloud or bar chart visualization.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    # Combine all document text
    all_text = " ".join(chunk for chunk, _ in docs).lower()
    
    # Extract keywords using simple regex (remove common stop words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract words (alphanumeric, minimum 3 characters)
    words = re.findall(r'\b[a-z]{3,}\b', all_text)
    filtered_words = [word for word in words if word not in stop_words]
    
    # Count frequency
    word_freq = Counter(filtered_words)
    top_words = word_freq.most_common(top_k)
    
    data = [{"name": word, "value": count} for word, count in top_words]
    
    return JSONResponse(content={
        "type": "keywords",
        "data": data,
        "total_words": len(filtered_words),
        "unique_words": len(word_freq)
    })

@router.get("/visualize/sources")
async def visualize_sources(session_id: str = Cookie(default=None)):
    """
    Visualize document sources and their contribution to the knowledge base.
    Returns data for pie chart or bar chart showing document distribution.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    # Count chunks per document
    source_counts = Counter()
    source_sizes = defaultdict(int)  # Track total character count per source
    
    for chunk, filename in docs:
        source_counts[filename] += 1
        source_sizes[filename] += len(chunk)

    # Prepare data with both chunk count and size information
    data = []
    for filename, chunk_count in source_counts.items():
        data.append({
            "name": filename,
            "chunks": chunk_count,
            "size": source_sizes[filename],
            "avg_chunk_size": source_sizes[filename] // chunk_count if chunk_count > 0 else 0
        })
    
    # Sort by chunk count descending
    data.sort(key=lambda x: x["chunks"], reverse=True)

    return JSONResponse(content={
        "type": "sources",
        "data": data,
        "total_sources": len(data),
        "total_chunks": sum(source_counts.values())
    })

@router.get("/visualize/conversation-flow")
async def visualize_conversation_flow(session_id: str = Cookie(default=None)):
    """
    Analyze conversation patterns and message types.
    Returns data showing the flow of conversation over time.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    if session_id not in conversation_histories:
        raise HTTPException(status_code=404, detail="No conversation found for session")
    
    conversation = conversation_histories[session_id]
    if not conversation:
        return JSONResponse(content={"type": "conversation_flow", "data": []})
    
    # Analyze conversation patterns
    data = []
    user_messages = 0
    assistant_messages = 0
    
    for i, message in enumerate(conversation):
        if message["role"] == "user":
            user_messages += 1
            message_type = "question" if "?" in message["content"] else "statement"
        else:
            assistant_messages += 1
            message_type = "response"
        
        data.append({
            "index": i + 1,
            "role": message["role"],
            "type": message_type,
            "length": len(message["content"]),
            "timestamp": message.get("timestamp", datetime.now().isoformat())
        })
    
    return JSONResponse(content={
        "type": "conversation_flow",
        "data": data,
        "stats": {
            "total_messages": len(conversation),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "avg_message_length": sum(len(msg["content"]) for msg in conversation) // len(conversation)
        }
    })

@router.get("/visualize/topic-analysis")
async def visualize_topic_analysis(session_id: str = Cookie(default=None)):
    """
    Use LLM to analyze and extract main topics from the research session.
    Returns structured topic data for visualization.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    conversation = conversation_histories.get(session_id, [])
    
    if not docs and not conversation:
        raise HTTPException(status_code=404, detail="No content found for session")

    # Combine document content and conversation for analysis
    content_parts = []
    
    if docs:
        doc_content = "\n".join(chunk for chunk, _ in docs[:5])  # Limit to first 5 chunks
        content_parts.append(f"Document Content:\n{doc_content[:1500]}")
    
    if conversation:
        recent_conversation = conversation[-10:]  # Last 10 messages
        conv_content = "\n".join(f"{msg['role']}: {msg['content']}" for msg in recent_conversation)
        content_parts.append(f"Recent Conversation:\n{conv_content[:1000]}")
    
    analysis_content = "\n\n".join(content_parts)
    
    prompt = f"""
    Analyze the following research content and identify the main topics and themes.
    Return a JSON response with this structure:
    {{
        "topics": [
            {{"name": "Topic Name", "relevance": 0.8, "keywords": ["keyword1", "keyword2"]}},
            {{"name": "Another Topic", "relevance": 0.6, "keywords": ["keyword3", "keyword4"]}}
        ],
        "summary": "Brief summary of the main research themes"
    }}
    
    Content to analyze:
    {analysis_content}
    
    Return only valid JSON.
    """

    try:
        response = react_with_llm([{"role": "user", "content": prompt}])
        
        # Try to parse JSON response
        import json
        analysis_result = json.loads(response)
        
        return JSONResponse(content={
            "type": "topic_analysis",
            "data": analysis_result.get("topics", []),
            "summary": analysis_result.get("summary", ""),
            "generated_at": datetime.now().isoformat()
        })
        
    except json.JSONDecodeError:
        # Fallback: extract simple topics from keywords
        docs_text = " ".join(chunk for chunk, _ in docs).lower()
        words = re.findall(r'\b[a-z]{4,}\b', docs_text)
        word_freq = Counter(words)
        top_words = word_freq.most_common(5)
        
        fallback_topics = [
            {"name": word.title(), "relevance": count/len(words), "keywords": [word]}
            for word, count in top_words
        ]
        
        return JSONResponse(content={
            "type": "topic_analysis",
            "data": fallback_topics,
            "summary": "Extracted from document frequency analysis",
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic analysis failed: {str(e)}")

@router.get("/visualize/research-timeline")
async def visualize_research_timeline(session_id: str = Cookie(default=None)):
    """
    Create a timeline view of the research session showing key events.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    conversation = conversation_histories.get(session_id, [])
    docs = document_store.get(session_id, [])
    
    timeline_events = []
    
    # Add document upload events
    doc_files = list(set(filename for _, filename in docs))
    for i, filename in enumerate(doc_files):
        timeline_events.append({
            "type": "document_upload",
            "title": f"Uploaded: {filename}",
            "timestamp": datetime.now().isoformat(),  # In real app, track actual upload time
            "details": f"Document containing {len([d for d in docs if d[1] == filename])} chunks"
        })
    
    # Add significant conversation events
    for i, message in enumerate(conversation):
        if message["role"] == "user" and len(message["content"]) > 100:
            timeline_events.append({
                "type": "major_question",
                "title": f"Research Question #{i//2 + 1}",
                "timestamp": message.get("timestamp", datetime.now().isoformat()),
                "details": message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"]
            })
    
    # Sort by timestamp
    timeline_events.sort(key=lambda x: x["timestamp"])
    
    return JSONResponse(content={
        "type": "research_timeline",
        "data": timeline_events,
        "session_start": timeline_events[0]["timestamp"] if timeline_events else datetime.now().isoformat(),
        "total_events": len(timeline_events)
    })

@router.get("/visualize/")
async def get_available_visualizations():
    """
    Return available visualization types and their descriptions.
    """
    visualizations = [
        {
            "endpoint": "/visualize/keywords",
            "name": "Keywords Analysis",
            "description": "Most frequent keywords from uploaded documents",
            "chart_types": ["wordcloud", "bar"]
        },
        {
            "endpoint": "/visualize/sources",
            "name": "Document Sources",
            "description": "Distribution of content across uploaded documents",
            "chart_types": ["pie", "bar"]
        },
        {
            "endpoint": "/visualize/conversation-flow",
            "name": "Conversation Flow",
            "description": "Pattern and flow of the research conversation",
            "chart_types": ["timeline", "line"]
        },
        {
            "endpoint": "/visualize/topic-analysis",
            "name": "Topic Analysis",
            "description": "AI-powered analysis of main research topics",
            "chart_types": ["network", "bubble"]
        },
        {
            "endpoint": "/visualize/research-timeline",
            "name": "Research Timeline",
            "description": "Chronological view of research session events",
            "chart_types": ["timeline"]
        }
    ]
    
    return JSONResponse(content={
        "available_visualizations": visualizations,
        "total_types": len(visualizations)
    })


