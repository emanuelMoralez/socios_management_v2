from datetime import date
from fastapi.testclient import TestClient
import uuid
import pytest

from app.models.pago import Pago


def auth_headers(client: TestClient):
    """Crea un usuario simple y retorna headers Bearer."""
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
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_member(client: TestClient, headers):
    """Crea una categoría mínima y un miembro asociado."""
    unique_id = uuid.uuid4().hex[:8]

    rc = client.post(
        "/api/miembros/categorias",
        headers=headers,
        json={
            "nombre": f"PagosCat_{unique_id}",
            "cuota_base": 1000,
            "tiene_cuota_fija": True,
        },
    )
    assert rc.status_code == 201, rc.text
    categoria_id = rc.json()["id"]

    doc_numerico = str(abs(hash(unique_id)))[:8]
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


def test_registrar_pago_completo_happy_path(client: TestClient):
    headers = auth_headers(client)
    m = create_member(client, headers)

    # Conteo inicial de movimientos
    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    movs_before = len(r.json())

    payload = {
        "miembro_id": m["id"],
        "tipo": "inscripcion",
        "concepto": "Pago de inscripción",
        "descripcion": "Alta de socio",
        "monto": 150.0,
        "descuento": 0.0,
        "recargo": 0.0,
        "metodo_pago": "efectivo",
        "fecha_pago": date.today().isoformat(),
    }

    r = client.post("/api/pagos", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    pago = r.json()

    # Miembro debe reflejar el saldo actualizado
    r = client.get(f"/api/miembros/{m['id']}", headers=headers)
    assert r.status_code == 200
    miembro = r.json()
    assert pytest.approx(miembro["saldo_cuenta"], rel=1e-6) == 150.0

    # Movimiento de caja creado
    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    movs_after = r.json()
    assert len(movs_after) == movs_before + 1
    assert any(mv.get("pago_id") == pago["id"] for mv in movs_after)


def test_registrar_pago_rollback_on_exception(client: TestClient, monkeypatch):
    """Simula una excepción tras flush (al generar comprobante) y valida rollback total."""
    headers = auth_headers(client)
    m = create_member(client, headers)

    # Estado inicial
    r = client.get(f"/api/miembros/{m['id']}", headers=headers)
    assert r.status_code == 200
    saldo_inicial = r.json()["saldo_cuenta"]

    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    movs_inicial = len(r.json())

    # Forzar excepción al generar número de comprobante, después del flush
    def _raise_on_comprobante(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(Pago, "generar_numero_comprobante", _raise_on_comprobante, raising=True)

    payload = {
        "miembro_id": m["id"],
        "tipo": "otro",
        "concepto": "Pago que debe fallar",
        "monto": 200.0,
        "descuento": 0.0,
        "recargo": 0.0,
        "metodo_pago": "efectivo",
        "fecha_pago": date.today().isoformat(),
    }

    r = client.post("/api/pagos", headers=headers, json=payload)
    # Debe fallar con 500 (handler general)
    assert r.status_code == 500, r.text

    # Validar que NO hubo efectos parciales:
    # - saldo del miembro sin cambios
    r = client.get(f"/api/miembros/{m['id']}", headers=headers)
    assert r.status_code == 200
    assert pytest.approx(r.json()["saldo_cuenta"], rel=1e-6) == saldo_inicial

    # - no se creó movimiento de caja
    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == movs_inicial

    # - no aparece en listar pagos
    r = client.get(f"/api/pagos?miembro_id={m['id']}", headers=headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(item["concepto"] != "Pago que debe fallar" for item in items)


def test_registrar_pago_rapido_rollback_on_exception(client: TestClient, monkeypatch):
    """Simula excepción en pago rápido y valida rollback sin efectos parciales."""
    headers = auth_headers(client)
    m = create_member(client, headers)

    # Estado inicial
    r = client.get(f"/api/miembros/{m['id']}", headers=headers)
    assert r.status_code == 200
    saldo_inicial = r.json()["saldo_cuenta"]

    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    movs_inicial = len(r.json())

    # Forzar excepción justo después del flush, al generar comprobante
    def _raise_on_comprobante(self):
        raise RuntimeError("boom-rapido")

    monkeypatch.setattr(Pago, "generar_numero_comprobante", _raise_on_comprobante, raising=True)

    payload = {
        "miembro_id": m["id"],
        "monto": 120.0,
        "metodo_pago": "efectivo",
        "mes_periodo": date.today().month,
        "anio_periodo": date.today().year,
        "aplicar_descuento": False,
    }

    r = client.post("/api/pagos/rapido", headers=headers, json=payload)
    assert r.status_code == 500, r.text

    # Validar sin efectos parciales
    r = client.get(f"/api/miembros/{m['id']}", headers=headers)
    assert r.status_code == 200
    assert pytest.approx(r.json()["saldo_cuenta"], rel=1e-6) == saldo_inicial

    r = client.get("/api/pagos/movimientos", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == movs_inicial

    r = client.get(f"/api/pagos?miembro_id={m['id']}", headers=headers)
    assert r.status_code == 200
    items = r.json()["items"]
    # El concepto comienza con "Cuota", verificamos que no haya registros del periodo actual con ese monto
    assert all(it["monto_final"] != 120.0 for it in items)
