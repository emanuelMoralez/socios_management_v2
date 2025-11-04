from fastapi.testclient import TestClient
import uuid


def test_register_login_me_refresh_change_password_flow(client: TestClient):
    # Generar username único para evitar colisiones
    unique_id = uuid.uuid4().hex[:8]
    username = f"tester_{unique_id}"
    
    # Register user
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "Admin1234",
        "confirm_password": "Admin1234",
        "nombre": "Tester",
        "apellido": "Flow",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text

    # Login
    r = client.post("/api/auth/login", json={"username": payload["username"], "password": payload["password"]})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data and "refresh_token" in data
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Me
    headers = {"Authorization": f"Bearer {access_token}"}
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["username"] == payload["username"]

    # Refresh
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200, r.text
    new_access = r.json()["access_token"]
    assert isinstance(new_access, str) and len(new_access) > 10

    # Change password
    headers = {"Authorization": f"Bearer {new_access}"}
    r = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": payload["password"],
            "new_password": "NewPass123",
            "confirm_password": "NewPass123",
        },
    )
    assert r.status_code == 200, r.text

    # Login with new password
    r = client.post("/api/auth/login", json={"username": payload["username"], "password": "NewPass123"})
    assert r.status_code == 200, r.text
