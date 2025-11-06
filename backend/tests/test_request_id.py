def test_validation_error_includes_request_id(client):
    # Enviamos payload inválido a /api/auth/login para detonar 422
    r = client.post("/api/auth/login", json={"username": 123, "password": 456})
    assert r.status_code == 422
    data = r.json()
    assert "request_id" in data
    assert data["request_id"]
