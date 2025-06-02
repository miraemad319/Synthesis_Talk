from collections import defaultdict
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime, timedelta
import threading
from backend.utils.persistence import load_sessions, save_sessions

# Load saved data (if available)
_conversations, _documents = load_sessions()

# Initialize in-memory stores with enhanced structure
conversation_histories = defaultdict(list, _conversations)
document_store = defaultdict(list, _documents)

# Enhanced session metadata storage
session_metadata = defaultdict(dict)
session_lock = threading.Lock()

# Auto-save mechanism
_last_save_time = datetime.now()
AUTOSAVE_INTERVAL = timedelta(minutes=5)

def get_session_metadata(session_id: str) -> Dict[str, Any]:
    """Get metadata for a specific session"""
    with session_lock:
        if session_id not in session_metadata:
            session_metadata[session_id] = {
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'message_count': 0,
                'document_count': 0,
                'topics': [],
                'reasoning_techniques_used': [],
                'tools_used': set()
            }
        return session_metadata[session_id]

def update_session_activity(session_id: str, activity_type: str = None, **kwargs):
    """Update session metadata with new activity"""
    with session_lock:
        metadata = get_session_metadata(session_id)
        metadata['last_activity'] = datetime.now().isoformat()
        
        if activity_type == 'message':
            metadata['message_count'] += 1
        elif activity_type == 'document':
            metadata['document_count'] += 1
        elif activity_type == 'tool_use':
            tool_name = kwargs.get('tool_name')
            if tool_name:
                if isinstance(metadata['tools_used'], set):
                    metadata['tools_used'].add(tool_name)
                else:
                    metadata['tools_used'] = set(metadata.get('tools_used', []))
                    metadata['tools_used'].add(tool_name)
        elif activity_type == 'reasoning':
            technique = kwargs.get('technique')
            if technique and technique not in metadata['reasoning_techniques_used']:
                metadata['reasoning_techniques_used'].append(technique)
        
        # Add topics if provided
        if 'topics' in kwargs:
            for topic in kwargs['topics']:
                if topic not in metadata['topics']:
                    metadata['topics'].append(topic)

def add_message_to_history(session_id: str, message: Dict[str, Any]):
    """Add a message to conversation history with metadata tracking"""
    with session_lock:
        enhanced_message = {
            'role': message.get('role', 'user'),
            'content': message.get('content', ''),
            'timestamp': datetime.now().isoformat(),
            'tools_used': message.get('tools_used', []),
            'reasoning_technique': message.get('reasoning_technique'),
            'context_sources': message.get('context_sources', [])
        }
        
        conversation_histories[session_id].append(enhanced_message)
        update_session_activity(session_id, 'message')
        
        # Auto-save check
        global _last_save_time
        if datetime.now() - _last_save_time > AUTOSAVE_INTERVAL:
            persist()
            _last_save_time = datetime.now()

def get_conversation_history(session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get conversation history for a session with optional limit"""
    with session_lock:
        history = conversation_histories.get(session_id, [])
        if limit:
            return history[-limit:]
        return history

def add_document_to_store(session_id: str, filename: str, content: str, chunks: List[str] = None):
    """Add document to store with enhanced metadata"""
    with session_lock:
        document_entry = {
            'filename': filename,
            'content': content,
            'chunks': chunks or [],
            'upload_time': datetime.now().isoformat(),
            'processed': bool(chunks)
        }
        
        document_store[session_id].append(document_entry)
        update_session_activity(session_id, 'document')

def get_documents_for_session(session_id: str) -> List[Dict[str, Any]]:
    """Get all documents for a session"""
    with session_lock:
        return document_store.get(session_id, [])

def get_document_chunks_for_session(session_id: str) -> List[tuple[str, str]]:
    """Get all document chunks for a session as (chunk_text, filename) tuples"""
    with session_lock:
        chunks = []
        for doc in document_store.get(session_id, []):
            filename = doc['filename']
            for chunk in doc.get('chunks', []):
                chunks.append((chunk, filename))
        return chunks

def clear_session(session_id: str):
    """Clear all data for a specific session"""
    with session_lock:
        if session_id in conversation_histories:
            del conversation_histories[session_id]
        if session_id in document_store:
            del document_store[session_id]
        if session_id in session_metadata:
            del session_metadata[session_id]
        persist()

def get_all_sessions() -> List[Dict[str, Any]]:
    """Get metadata for all active sessions"""
    with session_lock:
        sessions = []
        all_session_ids = set(conversation_histories.keys()) | set(document_store.keys()) | set(session_metadata.keys())
        
        for session_id in all_session_ids:
            metadata = get_session_metadata(session_id)
            # Convert set to list for JSON serialization
            if isinstance(metadata.get('tools_used'), set):
                metadata['tools_used'] = list(metadata['tools_used'])
            
            sessions.append({
                'session_id': session_id,
                'metadata': metadata,
                'has_conversation': session_id in conversation_histories,
                'has_documents': session_id in document_store
            })
        
        return sessions

def get_session_context_summary(session_id: str) -> Dict[str, Any]:
    """Get a comprehensive summary of session context"""
    with session_lock:
        metadata = get_session_metadata(session_id)
        history = conversation_histories.get(session_id, [])
        documents = document_store.get(session_id, [])
        
        # Convert set to list for JSON serialization
        tools_used = metadata.get('tools_used', set())
        if isinstance(tools_used, set):
            tools_used = list(tools_used)
        
        return {
            'session_id': session_id,
            'metadata': {
                **metadata,
                'tools_used': tools_used
            },
            'conversation_length': len(history),
            'document_count': len(documents),
            'document_names': [doc['filename'] for doc in documents],
            'recent_activity': history[-3:] if history else [],
            'total_chunks': sum(len(doc.get('chunks', [])) for doc in documents)
        }

def persist():
    """
    Manually call this to persist current state to disk with enhanced metadata.
    """
    with session_lock:
        # Convert sets to lists for JSON serialization
        serializable_metadata = {}
        for session_id, metadata in session_metadata.items():
            serializable_metadata[session_id] = {
                **metadata,
                'tools_used': list(metadata.get('tools_used', set())) if isinstance(metadata.get('tools_used'), set) else metadata.get('tools_used', [])
            }
        
        # Save with enhanced structure
        enhanced_data = {
            'conversations': dict(conversation_histories),
            'documents': dict(document_store),
            'session_metadata': serializable_metadata,
            'last_save': datetime.now().isoformat()
        }
        
        try:
            with open('session_data.json', 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error persisting session data: {e}")

def load_enhanced_sessions():
    """Load enhanced session data if available"""
    global session_metadata
    
    if os.path.exists('session_data.json'):
        try:
            with open('session_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load metadata if available
            if 'session_metadata' in data:
                for session_id, metadata in data['session_metadata'].items():
                    # Convert tools_used back to set
                    if 'tools_used' in metadata and isinstance(metadata['tools_used'], list):
                        metadata['tools_used'] = set(metadata['tools_used'])
                    session_metadata[session_id] = metadata
                    
        except Exception as e:
            print(f"Warning: Could not load enhanced session data: {e}")

# Load enhanced data on import
load_enhanced_sessions()

def cleanup_old_sessions(days_old: int = 30):
    """Clean up sessions older than specified days"""
    with session_lock:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        sessions_to_remove = []
        
        for session_id, metadata in session_metadata.items():
            try:
                last_activity = datetime.fromisoformat(metadata.get('last_activity', metadata.get('created_at', '')))
                if last_activity < cutoff_date:
                    sessions_to_remove.append(session_id)
            except (ValueError, TypeError):
                # If we can't parse the date, keep the session
                continue
        
        for session_id in sessions_to_remove:
            clear_session(session_id)
        
        return len(sessions_to_remove)

def add_document_metadata(session_id: str, filename: str, metadata: Dict[str, Any]):
    """Add document metadata to session tracking"""
    with session_lock:
        session_meta = get_session_metadata(session_id)
        
        # Initialize document_metadata if it doesn't exist
        if 'document_metadata' not in session_meta:
            session_meta['document_metadata'] = {}
        
        # Store the document metadata
        session_meta['document_metadata'][filename] = {
            **metadata,
            'added_at': datetime.now().isoformat()
        }
        
        # Update session activity
        update_session_activity(session_id, 'document')