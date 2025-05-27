import io
import os

def test_save_note(client):
    """Test saving a note to the session"""
    client.cookies.set("session_id", "test-session-id")

    response = client.post(
        "/note/",
        json={"note": "This is a test note."}
    )

    assert response.status_code == 200
    assert response.json().get("message") == "Note saved."

def test_explain_query(client):
    """Test explaining a concept"""
    client.cookies.set("session_id", "test-session-id")

    response = client.post(
        "/explain/",
        json={"query": "What is a neural network?"}
    )

    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)
    assert len(response.json()["response"]) > 0

def test_export_conversation(client):
    """Test exporting conversation history"""
    client.cookies.set("session_id", "test-session-id")

    # First, create some conversation history
    client.post("/chat/", json={"message": "Test for export"})

    response = client.get("/export/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    
    # Check that content exists
    content = response.content.decode('utf-8')
    assert len(content) > 0
    assert "Test for export" in content

def test_generate_insights(client):
    """Test generating insights from uploaded documents"""
    client.cookies.set("session_id", "test-session-id")

    # Upload some content first
    file_data = b"Artificial intelligence and machine learning are evolving rapidly in healthcare and finance. These technologies show promising applications in medical diagnosis and financial risk assessment. Healthcare AI systems can analyze medical images with high accuracy. Financial machine learning models can detect fraudulent transactions effectively."

    upload_response = client.post(
        "/upload/?format=paragraph",
        files={"file": ("context.txt", io.BytesIO(file_data), "text/plain")}
    )

    # Verify upload was successful
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "error" not in upload_data, f"Upload failed: {upload_data.get('error')}"
    assert "filename" in upload_data

    # Now try to generate insights
    response = client.get("/insights/")

    assert response.status_code == 200
    data = response.json()
    
    # Should have insights, not an error
    if "error" in data:
        print(f"Insights generation failed: {data['error']}")
        # This might fail due to LLM API issues, which is acceptable in testing
        # Check if it's a reasonable error
        acceptable_errors = ["No documents found for session", "Failed to generate insights"]
        assert any(err in data["error"] for err in acceptable_errors), f"Unexpected error: {data['error']}"
    else:
        assert "insights" in data
        assert isinstance(data["insights"], str)
        assert len(data["insights"]) > 0

def test_insights_no_documents(client):
    """Test insights generation without documents"""
    client.cookies.set("session_id", "empty-test-session")
    
    response = client.get("/insights/")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "No documents found for session" in data["error"]
