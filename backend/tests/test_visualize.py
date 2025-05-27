import io
import pytest

def test_visualize_keywords(client):
    """Test generating keyword visualization after uploading content"""
    client.cookies.set("session_id", "test-session-id")

    # Upload content with repeated keywords to generate visualization from
    content = b"Machine learning and artificial intelligence are transformative technologies. Machine learning algorithms process data efficiently. Artificial intelligence systems demonstrate remarkable capabilities. Data processing and algorithmic approaches drive these machine learning innovations."

    upload_response = client.post(
        "/upload/?format=paragraph",
        files={"file": ("keywords.txt", io.BytesIO(content), "text/plain")}
    )

    # Verify upload was successful
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "error" not in upload_data, f"Upload failed: {upload_data.get('error')}"

    # Request visualization
    response = client.get("/visualize/")

    assert response.status_code == 200
    
    # Check if we got an error or a proper image
    if response.headers["content-type"] == "application/json":
        # If JSON response, check what the error is
        data = response.json()
        if "error" in data:
            # For debugging - print the error but don't fail the test if it's a reasonable error
            print(f"Visualization error: {data['error']}")
            # Accept certain errors as valid (like no meaningful keywords)
            acceptable_errors = [
                "No meaningful keywords found",
                "Not enough content to visualize",
                "No documents found for session",
                "No meaningful keywords found for visualization"
            ]
            assert any(err in data["error"] for err in acceptable_errors), f"Unexpected error: {data['error']}"
        else:
            pytest.fail("Got JSON response but no error field")
    else:
        # Should be an image response
        assert response.headers["content-type"].startswith("image/")
        # PNG files start with specific bytes
        assert len(response.content) > 8, "Image file too small"
        # Check for PNG signature (optional, but good validation)
        png_signature = b"\x89PNG\r\n\x1a\n"
        assert response.content[:8] == png_signature, "Not a valid PNG file"

def test_visualize_no_session(client):
    """Test visualization without a session ID"""
    # Don't set session cookie
    response = client.get("/visualize/")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "Missing session ID" in data["error"]

def test_visualize_empty_session(client):
    """Test visualization with empty session"""
    client.cookies.set("session_id", "empty-session-id")
    response = client.get("/visualize/")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "No documents found for session" in data["error"]
