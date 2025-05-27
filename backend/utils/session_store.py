from collections import defaultdict
from backend.utils.persistence import load_sessions, save_sessions

# Load saved data (if available)
_conversations, _documents = load_sessions()

# Initialize in-memory stores
conversation_histories = _conversations
document_store = defaultdict(list, _documents)

def persist():
    """
    Manually call this to persist current state to disk.
    """
    save_sessions(conversation_histories, document_store)

