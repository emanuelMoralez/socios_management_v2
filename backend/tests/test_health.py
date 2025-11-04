import os
from fastapi.testclient import TestClient

# Ensure test env uses SQLite and development mode BEFORE importing app
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_root_ok():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body.get("message") == "Sistema de Gestión de Socios API"
    assert body.get("status") == "online"


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in {"healthy", "unhealthy"}
    # With SQLite in CI it should be connected
    assert body.get("database") == "connected"
