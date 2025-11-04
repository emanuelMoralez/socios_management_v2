from fastapi.testclient import TestClient
from datetime import date
import uuid


def _auth_headers(client: TestClient):
    """Helper para crear usuario único y obtener headers de auth"""
    unique_id = uuid.uuid4().hex[:8]
    username = f"op_{unique_id}"
    password = "Admin1234"
    
    reg = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password,
            "nombre": "Operador",
            "apellido": "Pruebas",
        },
    )
    assert reg.status_code == 201, reg.text
    
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_categoria_y_miembro_crud(client: TestClient):
    headers = _auth_headers(client)
    unique_id = uuid.uuid4().hex[:8]

    # Crear categoría con nombre único
    r = client.post(
        "/api/miembros/categorias",
        headers=headers,
        json={
            "nombre": f"Titular_{unique_id}",
            "descripcion": "Cat de prueba",
            "cuota_base": 1000,
            "tiene_cuota_fija": True,
            "modulo_tipo": "generico",
        },
    )
    assert r.status_code == 201, r.text
    categoria_id = r.json()["id"]

    # Crear miembro con documento único (solo dígitos)
    doc_numerico = str(abs(hash(unique_id)))[:8]  # Generar 8 dígitos únicos
    payload = {
        "numero_documento": doc_numerico,
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": f"juan_{unique_id}@example.com",
        "telefono": "12345",
        "direccion": "Calle 123",
        "localidad": "Ciudad",
        "provincia": "Prov",
        "codigo_postal": "1000",
        "categoria_id": categoria_id,
        "fecha_alta": date.today().isoformat(),
        "modulo_tipo": "generico",
    }
    r = client.post("/api/miembros", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    miembro = r.json()

    # Obtener miembro
    r = client.get(f"/api/miembros/{miembro['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["numero_miembro"].startswith("M-")

    # Listar miembros (paginado)
    r = client.get("/api/miembros?page=1&page_size=10", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["pagination"]["page"] == 1
    assert any(item["id"] == miembro["id"] for item in body["items"])  # type: ignore

    # Estado financiero
    r = client.get(f"/api/miembros/{miembro['id']}/estado-financiero", headers=headers)
    assert r.status_code == 200
    est = r.json()
    assert est["miembro_id"] == miembro["id"]

    # Eliminar (soft delete)
    r = client.delete(f"/api/miembros/{miembro['id']}", headers=headers)
    assert r.status_code == 200

    # Ver que no aparezca en listar (solo_activos=True default)
    r = client.get("/api/miembros?page=1&page_size=10", headers=headers)
    assert r.status_code == 200
    assert all(item["id"] != miembro["id"] for item in r.json()["items"])  # type: ignore
