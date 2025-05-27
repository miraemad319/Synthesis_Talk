import pytest
from fastapi.testclient import TestClient
import sys
import os
import nltk

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Download NLTK data before importing main app
try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)  # New NLTK format
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")

from main import app

@pytest.fixture
def client():
    """Create a test client with a pre-set session ID"""
    test_client = TestClient(app)
    # Set session cookie that will be used by all test requests
    test_client.cookies.set("session_id", "test-session-id")
    return test_client

@pytest.fixture(autouse=True)
def clean_test_data():
    """Clean up test data before and after each test"""
    # Clean up before test
    from backend.utils.session_store import conversation_histories, document_store
    
    # Clear test session data
    test_session_id = "test-session-id"
    if test_session_id in conversation_histories:
        del conversation_histories[test_session_id]
    if test_session_id in document_store:
        del document_store[test_session_id]
    
    yield  # Run the test
    
    # Clean up after test (optional, but good practice)
    if test_session_id in conversation_histories:
        del conversation_histories[test_session_id]
    if test_session_id in document_store:
        del document_store[test_session_id]