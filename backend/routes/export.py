from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
import os
import json
import csv
from datetime import datetime
from typing import Optional, Dict, Any
import io

from backend.utils.session_store import conversation_histories, document_store

router = APIRouter()

class ExportFormatter:
    """Advanced export formatting with multiple output types"""
    
    @staticmethod
    def format_as_markdown(conversation: list, session_id: str, metadata: Dict[str, Any] = None) -> str:
        """Format conversation as structured markdown"""
        md_content = []
        
        # Header
        md_content.append(f"# SynthesisTalk Export - Session {session_id}")
        md_content.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if metadata:
            md_content.append(f"**Documents Processed:** {metadata.get('document_count', 0)}")
            md_content.append(f"**Total Messages:** {len(conversation)}")
        
        md_content.append("\n---\n")
        
        # Conversation
        md_content.append("## Conversation History")
        
        for i, msg in enumerate(conversation, 1):
            role = msg['role'].capitalize()
            content = msg['content']
            timestamp = ""
            
            if isinstance(msg.get('metadata'), dict) and 'timestamp' in msg['metadata']:
                timestamp = f" *({msg['metadata']['timestamp']})*"
            
            md_content.append(f"### {i}. {role}{timestamp}")
            md_content.append(f"{content}\n")
        
        return "\n".join(md_content)
    
    @staticmethod
    def format_as_json(conversation: list, session_id: str, metadata: Dict[str, Any] = None) -> str:
        """Format as structured JSON"""
        export_data = {
            "export_metadata": {
                "session_id": session_id,
                "export_timestamp": datetime.now().isoformat(),
                "format_version": "1.0",
                "total_messages": len(conversation)
            },
            "session_metadata": metadata or {},
            "conversation": conversation
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def format_as_csv(conversation: list, session_id: str) -> str:
        """Format conversation as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Message_ID', 'Role', 'Content', 'Timestamp', 'Message_Type'])
        
        # Data rows
        for i, msg in enumerate(conversation, 1):
            timestamp = ""
            msg_type = "regular"
            
            if isinstance(msg.get('metadata'), dict):
                timestamp = msg['metadata'].get('timestamp', '')
                msg_type = msg['metadata'].get('type', 'regular')
            
            writer.writerow([
                i,
                msg['role'],
                msg['content'].replace('\n', ' ').replace('\r', ''),  # Clean content for CSV
                timestamp,
                msg_type
            ])
        
        return output.getvalue()
    
    @staticmethod
    def create_research_summary(conversation: list, documents: list) -> str:
        """Create a structured research summary document"""
        summary_parts = []
        
        # Title and overview
        summary_parts.append("# Research Summary Report")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Document sources
        if documents:
            summary_parts.append("## Source Documents")
            doc_names = set()
            for _, filename in documents:
                if filename:
                    doc_names.add(filename)
            
            for doc_name in sorted(doc_names):
                summary_parts.append(f"- {doc_name}")
            summary_parts.append("")
        
        # Key interactions
        summary_parts.append("## Key Research Interactions")
        
        user_questions = []
        assistant_insights = []
        
        for msg in conversation:
            if msg['role'] == 'user' and len(msg['content']) > 20:
                user_questions.append(msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content'])
            elif msg['role'] == 'assistant' and len(msg['content']) > 50:
                assistant_insights.append(msg['content'][:300] + "..." if len(msg['content']) > 300 else msg['content'])
        
        if user_questions:
            summary_parts.append("### Research Questions Asked")
            for i, question in enumerate(user_questions[:10], 1):  # Limit to top 10
                summary_parts.append(f"{i}. {question}")
            summary_parts.append("")
        
        if assistant_insights:
            summary_parts.append("### Key Insights Generated")
            for i, insight in enumerate(assistant_insights[:10], 1):  # Limit to top 10
                summary_parts.append(f"{i}. {insight}")
            summary_parts.append("")
        
        # Statistics
        summary_parts.append("## Session Statistics")
        summary_parts.append(f"- Total messages: {len(conversation)}")
        summary_parts.append(f"- User messages: {len([m for m in conversation if m['role'] == 'user'])}")
        summary_parts.append(f"- Assistant responses: {len([m for m in conversation if m['role'] == 'assistant'])}")
        summary_parts.append(f"- Documents processed: {len(set(filename for _, filename in documents if filename))}")
        
        return "\n".join(summary_parts)

@router.get("/export/")
async def export_conversation(
    session_id: str = Cookie(default=None),
    format: str = Query(default="txt", description="Export format: txt, md, json, csv, summary"),
    include_metadata: bool = Query(default=True, description="Include session metadata")
):
    """Export conversation in various formats with enhanced structure"""
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    if session_id not in conversation_histories:
        raise HTTPException(status_code=404, detail="No conversation found for session")

    conversation = conversation_histories[session_id]
    if not conversation:
        raise HTTPException(status_code=404, detail="Empty conversation history")
    
    # Get document metadata if requested
    metadata = {}
    documents = []
    
    if include_metadata:
        documents = document_store.get(session_id, [])
        metadata = {
            "document_count": len(set(filename for _, filename in documents if filename)),
            "total_chunks": len(documents),
            "session_start": conversation[0].get('metadata', {}).get('timestamp', '') if conversation else '',
            "session_end": conversation[-1].get('metadata', {}).get('timestamp', '') if conversation else ''
        }
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    formatter = ExportFormatter()
    
    try:
        if format == "md" or format == "markdown":
            content = formatter.format_as_markdown(conversation, session_id, metadata)
            filename = f"conversation_{timestamp}.md"
            media_type = "text/markdown"
            
        elif format == "json":
            content = formatter.format_as_json(conversation, session_id, metadata)
            filename = f"conversation_{timestamp}.json"
            media_type = "application/json"
            
        elif format == "csv":
            content = formatter.format_as_csv(conversation, session_id)
            filename = f"conversation_{timestamp}.csv"
            media_type = "text/csv"
            
        elif format == "summary":
            content = formatter.create_research_summary(conversation, documents)
            filename = f"research_summary_{timestamp}.md"
            media_type = "text/markdown"
            
        else:  # Default to txt
            content = ""
            for msg in conversation:
                timestamp_str = ""
                if isinstance(msg.get('metadata'), dict) and 'timestamp' in msg['metadata']:
                    timestamp_str = f" [{msg['metadata']['timestamp']}]"
                
                content += f"{msg['role'].capitalize()}{timestamp_str}:\n{msg['content']}\n\n"
            
            filename = f"conversation_{timestamp}.txt"
            media_type = "text/plain"
        
        # Ensure exports directory exists
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        # Write file
        filepath = os.path.join(export_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return FileResponse(
            filepath,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/formats")
async def get_available_formats():
    """Get list of available export formats"""
    formats = {
        "txt": {
            "name": "Plain Text",
            "description": "Simple text format with conversation flow",
            "extension": ".txt"
        },
        "md": {
            "name": "Markdown",
            "description": "Structured markdown with headers and formatting",
            "extension": ".md"
        },
        "json": {
            "name": "JSON",
            "description": "Structured data format with full metadata",
            "extension": ".json"
        },
        "csv": {
            "name": "CSV",
            "description": "Spreadsheet format for data analysis",
            "extension": ".csv"
        },
        "summary": {
            "name": "Research Summary",
            "description": "Condensed research report with key findings",
            "extension": ".md"
        }
    }
    
    return JSONResponse(content={"formats": formats})

@router.get("/export/preview")
async def preview_export(
    session_id: str = Cookie(default=None),
    format: str = Query(default="txt"),
    lines: int = Query(default=20, description="Number of lines to preview")
):
    """Preview export content without downloading"""
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    if session_id not in conversation_histories:
        raise HTTPException(status_code=404, detail="No conversation found")
    
    conversation = conversation_histories[session_id][:5]  # Limit for preview
    documents = document_store.get(session_id, [])
    
    formatter = ExportFormatter()
    
    try:
        if format == "md":
            content = formatter.format_as_markdown(conversation, session_id)
        elif format == "json":
            content = formatter.format_as_json(conversation, session_id)
        elif format == "csv":
            content = formatter.format_as_csv(conversation, session_id)
        elif format == "summary":
            content = formatter.create_research_summary(conversation, documents)
        else:
            content = ""
            for msg in conversation:
                content += f"{msg['role'].capitalize()}:\n{msg['content']}\n\n"
        
        # Limit preview to specified number of lines
        preview_lines = content.split('\n')[:lines]
        preview_content = '\n'.join(preview_lines)
        
        if len(content.split('\n')) > lines:
            preview_content += f"\n\n... (truncated, full export has {len(content.split('\n'))} lines)"
        
        return JSONResponse(content={
            "preview": preview_content,
            "total_lines": len(content.split('\n')),
            "format": format,
            "truncated": len(content.split('\n')) > lines
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")
