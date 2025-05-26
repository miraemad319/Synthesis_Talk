from collections import defaultdict

# In-memory session storage for conversation history and uploaded documents

# Tracks the message history per session (used to maintain LLM context)
conversation_histories = {}

# Stores uploaded document chunks per session
# Format: session_id -> list of (chunk_text, filename)
document_store = defaultdict(list)
