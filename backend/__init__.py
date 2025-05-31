# This file makes the backend directory a Python package
# and provides a centralized import point for the SynthesisTalk backend

# Version information
__version__ = "1.0.0"
__author__ = "SynthesisTalk Team"
__description__ = "Collaborative Research Assistant Backend"

# Import main components for easy access
try:
    from .main import app
    from .llm import LLMManager
except ImportError:
    # Handle cases where dependencies might not be installed yet
    app = None
    LLMManager = None

# Configuration constants
DEFAULT_CONFIG = {
    "MAX_FILE_SIZE": 50 * 1024 * 1024,  # 50MB
    "SUPPORTED_FILE_TYPES": [".pdf", ".txt", ".docx", ".json"],
    "MAX_CHUNK_SIZE": 1000,
    "DEFAULT_MODEL": "gemini-pro",
    "MAX_CONVERSATION_HISTORY": 50,
    "SEARCH_RESULTS_LIMIT": 10,
    "SESSION_TIMEOUT": 3600,  # 1 hour in seconds
}

# Export commonly used modules
__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "app",
    "LLMManager",
    "DEFAULT_CONFIG"
]