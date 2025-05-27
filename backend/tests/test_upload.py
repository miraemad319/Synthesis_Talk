import io

def test_upload_txt_file(client):
    """Test uploading a text file and getting a proper response"""
    client.cookies.set("session_id", "test-session-id")

    file_content = b"This is a test document for summarization. It contains multiple sentences for testing purposes."

    response = client.post(
        "/upload/?format=paragraph",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    )

    assert response.status_code == 200
    data = response.json()
    
    # Check that we don't have an error response
    assert "error" not in data, f"Upload failed with error: {data.get('error', 'Unknown error')}"
    
    # Check expected fields are present
    assert "filename" in data
    assert "summary" in data  
    assert "chunks" in data
    
    # Verify content
    assert data["filename"] == "test.txt"
    assert isinstance(data["summary"], str)
    assert isinstance(data["chunks"], int)
    assert data["chunks"] > 0

def test_upload_unsupported_file(client):
    """Test uploading an unsupported file type"""
    client.cookies.set("session_id", "test-session-id")

    file_content = b"Some binary content"

    response = client.post(
        "/upload/?format=paragraph",
        files={"file": ("test.xyz", io.BytesIO(file_content), "application/octet-stream")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "Unsupported file type" in data["error"]
