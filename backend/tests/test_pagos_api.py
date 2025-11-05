from datetime import date, timedelta
from fastapi.testclient import TestClient
import uuid
import pytest


def _auth_headers(client: TestClient):
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
            "apellido": "Pagos",
        },
    )
    assert reg.status_code == 201, reg.text

    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _crear_categoria_y_miembro(client: TestClient, headers):
    unique_id = uuid.uuid4().hex[:8]
    # categoría
    rc = client.post(
        "/api/miembros/categorias",
        headers=headers,
        json={
            "nombre": f"CatPagos_{unique_id}",
            "cuota_base": 1000,
            "tiene_cuota_fija": True,
        },
    )
    assert rc.status_code == 201, rc.text
    categoria_id = rc.json()["id"]

    # miembro
    dni = str(abs(hash(unique_id)))[:8]
    rm = client.post(
        "/api/miembros",
        headers=headers,
        json={
            "numero_documento": dni,
            "nombre": "Ana",
            "apellido": "Gomez",
            "categoria_id": categoria_id,
        },
    )
    assert rm.status_code == 201, rm.text
    return rm.json()


def test_registrar_pago_completo_y_listar(client: TestClient):
    headers = _auth_headers(client)
    socio = _crear_categoria_y_miembro(client, headers)

    payload = {
        "miembro_id": socio["id"],
        "tipo": "cuota",
        "concepto": "Cuota Mensual",
        "descripcion": "Pago manual",
        "monto": 150.0,
        "descuento": 10.0,
        "recargo": 5.0,
        "metodo_pago": "efectivo",
        "fecha_pago": date.today().isoformat(),
        "fecha_periodo": date.today().replace(day=1).isoformat(),
        "observaciones": "Caja",
    }

    r = client.post("/api/pagos", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    pago = r.json()
    assert pago["monto_final"] == pytest.approx(145.0, rel=1e-2)

    # listar con filtros
    r = client.get(
        f"/api/pagos?miembro_id={socio['id']}&metodo_pago=efectivo&estado=aprobado",
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["pagination"]["total"] >= 1

    # obtener detalle
    r = client.get(f"/api/pagos/{pago['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == pago["id"]


def test_registrar_pago_valida_miembro_inexistente(client: TestClient):
    headers = _auth_headers(client)
    payload = {
        "miembro_id": 999999,
        "tipo": "cuota",
        "concepto": "Cuota",
        "monto": 100.0,
        "metodo_pago": "efectivo",
        "fecha_pago": date.today().isoformat(),
    }
    r = client.post("/api/pagos", headers=headers, json=payload)
    assert r.status_code == 404


def test_movimientos_manual_y_listado(client: TestClient):
    headers = _auth_headers(client)

    # Crear movimiento manual (ingreso)
    mov = {
        "tipo": "ingreso",
        "concepto": "Venta Merch",
        "descripcion": "remeras",
        "monto": 300.0,
        "categoria_contable": "Ventas",
        "fecha_movimiento": date.today().isoformat(),
    }
    r = client.post("/api/pagos/movimientos", headers=headers, json=mov)
    assert r.status_code == 201, r.text

    # Listar por tipo
    r = client.get("/api/pagos/movimientos?tipo=ingreso", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_anular_pago_doble_marca_error(client: TestClient):
    headers = _auth_headers(client)
    socio = _crear_categoria_y_miembro(client, headers)

    # Pago rápido
    r = client.post(
        "/api/pagos/rapido",
        headers=headers,
        json={
            "miembro_id": socio["id"],
            "mes_periodo": date.today().month,
            "anio_periodo": date.today().year,
            "monto": 100.0,
            "metodo_pago": "efectivo",
            "aplicar_descuento": False,
        },
    )
    assert r.status_code == 201
    pago_id = r.json()["id"]

    # Primera anulación OK
    r = client.post(f"/api/pagos/{pago_id}/anular", headers=headers, json={"motivo": "Error" * 4})
    assert r.status_code == 200

    # Segunda anulación debe fallar
    r = client.post(f"/api/pagos/{pago_id}/anular", headers=headers, json={"motivo": "Reintento" * 3})
    assert r.status_code == 400
