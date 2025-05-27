def test_chat_endpoint(client):
    response = client.post("/chat/", json={"message": "What is AI?"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert isinstance(response.json()["response"], str)

