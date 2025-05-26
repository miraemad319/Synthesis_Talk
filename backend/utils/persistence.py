import json
import os

DATA_FILE = "session_data.json"

def save_sessions(conversations, documents):
    """
    Save session data (conversations + documents) to disk.
    """
    data = {
        "conversations": conversations,
        "documents": {k: v for k, v in documents.items()}
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_sessions():
    """
    Load session data from disk (if it exists).
    Returns: (conversation_histories, document_store)
    """
    if not os.path.exists(DATA_FILE):
        return {}, {}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        conversations = data.get("conversations", {})
        documents = data.get("documents", {})
        return conversations, documents
