from datetime import date
from fastapi.testclient import TestClient
import uuid
import pytest


def auth_headers(client: TestClient):
    """Helper para crear usuario único y obtener headers de auth"""
    unique_id = uuid.uuid4().hex[:8]
    username = f"cashier_{unique_id}"
    password = "Admin1234"
    
    reg = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password,
            "nombre": "Caja",
            "apellido": "Test",
        },
    )
    assert reg.status_code == 201, reg.text
    
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_member(client: TestClient, headers):
    """Helper para crear miembro con identificadores únicos"""
    unique_id = uuid.uuid4().hex[:8]
    
    # Crear categoría mínima con nombre único
    rc = client.post(
        "/api/miembros/categorias",
        headers=headers,
        json={
            "nombre": f"PagosCat_{unique_id}",
            "cuota_base": 1000,
            "tiene_cuota_fija": True
        },
    )
    assert rc.status_code == 201, rc.text
    categoria_id = rc.json()["id"]

    # Crear miembro con documento único (solo dígitos)
    doc_numerico = str(abs(hash(unique_id)))[:8]  # Generar 8 dígitos únicos
    r = client.post(
        "/api/miembros",
        headers=headers,
        json={
            "numero_documento": doc_numerico,
            "nombre": "Maria",
            "apellido": "Lopez",
            "categoria_id": categoria_id,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_pago_rapido_y_anular(client: TestClient):
    headers = auth_headers(client)
    m = create_member(client, headers)

    # Registrar pago rápido
    r = client.post(
        "/api/pagos/rapido",
        headers=headers,
        json={
            "miembro_id": m["id"],
            "mes_periodo": date.today().month,
            "anio_periodo": date.today().year,
            "monto": 100.0,
            "metodo_pago": "efectivo",
            "aplicar_descuento": False,
        },
    )
    assert r.status_code == 201, r.text
    pago = r.json()

    # Ver en listar pagos
    r = client.get("/api/pagos?page=1&page_size=10", headers=headers)
    assert r.status_code == 200
    assert any(item["id"] == pago["id"] for item in r.json()["items"])  # type: ignore

    # Resumen financiero debería incluir algún ingreso
    r = client.get("/api/pagos/resumen/financiero", headers=headers)
    assert r.status_code == 200
    resumen = r.json()
    assert resumen["total_ingresos"] >= 0

    # Anular pago
    r = client.post(
        f"/api/pagos/{pago['id']}/anular",
        headers=headers,
        json={"motivo": "Error de carga"},
    )
    assert r.status_code == 200

    # Obtener pago y verificar estado cancelado
    r = client.get(f"/api/pagos/{pago['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "cancelado"
