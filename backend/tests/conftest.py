"""
Fixtures de Pytest para tests del backend
backend/tests/conftest.py
"""
import os
import shutil
import tempfile
import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient


# Configurar entorno de pruebas ANTES de importar la app
os.environ.setdefault("ENVIRONMENT", "development")
# Usamos una base SQLite temporal por ejecución
_TEST_DB = os.path.join(tempfile.gettempdir(), f"gestion_socios_test_{int(time.time())}.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
	"""Cliente de pruebas FastAPI con SQLite temporal.

	Crea el app y su ciclo de vida; en ENV=development, las tablas se crean
	automáticamente en startup (ver app.main:lifespan).
	"""
	from app.main import app  # import tardío para respetar variables de entorno

	with TestClient(app) as c:
		yield c


@pytest.fixture
def make_user(client):
	"""Helper para registrar usuarios vía API.

	Retorna un dict con (username, password, json).
	"""
	def _maker(username: str = None, password: str = None):
		import uuid
		username = username or f"user_{uuid.uuid4().hex[:8]}"
		password = password or "Admin1234"
		payload = {
			"username": username,
			"email": f"{username}@example.com",
			"password": password,
			"confirm_password": password,
			"nombre": "Test",
			"apellido": "User",
		}
		r = client.post("/api/auth/register", json=payload)
		assert r.status_code == 201, r.text
		return {"username": username, "password": password, "json": r.json()}

	return _maker


@pytest.fixture
def auth_tokens(client, make_user):
	"""Crea un usuario y retorna sus tokens tras login."""
	u = make_user()
	r = client.post("/api/auth/login", json={"username": u["username"], "password": u["password"]})
	assert r.status_code == 200, r.text
	data = r.json()
	return data
