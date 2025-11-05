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


def test_resumen_financiero_con_parametros(client: TestClient):
    headers = _auth_headers(client)
    socio = _crear_categoria_y_miembro(client, headers)

    # Mes/año controlado sin interferencia
    mes, anio = 5, 2030

    # Pago completo en 2030-05 (monto_final = 200 - 20 + 0 = 180)
    pago_payload = {
        "miembro_id": socio["id"],
        "tipo": "cuota",
        "concepto": "Cuota Test Mayo 2030",
        "monto": 200.0,
        "descuento": 20.0,
        "recargo": 0.0,
        "metodo_pago": "efectivo",
        "fecha_pago": date(anio, mes, 10).isoformat(),
        "fecha_periodo": date(anio, mes, 1).isoformat(),
    }
    rp = client.post("/api/pagos", headers=headers, json=pago_payload)
    assert rp.status_code == 201, rp.text
    monto_final_pago = rp.json()["monto_final"]

    # Movimiento ingreso manual en 2030-05
    rmi = client.post(
        "/api/pagos/movimientos",
        headers=headers,
        json={
            "tipo": "ingreso",
            "concepto": "Ingreso Test",
            "monto": 300.0,
            "fecha_movimiento": date(anio, mes, 12).isoformat(),
        },
    )
    assert rmi.status_code == 201, rmi.text

    # Movimiento egreso manual en 2030-05
    rme = client.post(
        "/api/pagos/movimientos",
        headers=headers,
        json={
            "tipo": "egreso",
            "concepto": "Egreso Test",
            "monto": 50.0,
            "fecha_movimiento": date(anio, mes, 15).isoformat(),
        },
    )
    assert rme.status_code == 201, rme.text

    # Resumen para mayo 2030
    rr = client.get(f"/api/pagos/resumen/financiero?mes={mes}&anio={anio}", headers=headers)
    assert rr.status_code == 200, rr.text
    resumen = rr.json()

    # total_ingresos = movimiento ingreso (300) + movimiento auto del pago (monto_final)
    esperado_ingresos = 300.0 + float(monto_final_pago)
    assert resumen["total_ingresos"] == pytest.approx(esperado_ingresos, rel=1e-3)
    assert resumen["total_egresos"] == pytest.approx(50.0, rel=1e-3)
    assert resumen["saldo"] == pytest.approx(esperado_ingresos - 50.0, rel=1e-3)
    assert resumen["cantidad_pagos"] >= 1  # Al menos el que creamos
    assert resumen["periodo"] == f"{anio}-{mes:02d}"


def test_listar_movimientos_por_fecha(client: TestClient):
    headers = _auth_headers(client)

    # Crear dos movimientos en distintos días del mismo mes 2030-07
    anio, mes = 2030, 7
    m1 = client.post(
        "/api/pagos/movimientos",
        headers=headers,
        json={
            "tipo": "ingreso",
            "concepto": "Filtro Fecha 1",
            "monto": 10.0,
            "fecha_movimiento": date(anio, mes, 5).isoformat(),
        },
    )
    assert m1.status_code == 201, m1.text

    m2 = client.post(
        "/api/pagos/movimientos",
        headers=headers,
        json={
            "tipo": "ingreso",
            "concepto": "Filtro Fecha 2",
            "monto": 20.0,
            "fecha_movimiento": date(anio, mes, 25).isoformat(),
        },
    )
    assert m2.status_code == 201, m2.text

    # Filtrar del 1 al 10: solo debe estar el primero
    r = client.get(
        f"/api/pagos/movimientos?fecha_inicio={date(anio, mes, 1).isoformat()}&fecha_fin={date(anio, mes, 10).isoformat()}",
        headers=headers,
    )
    assert r.status_code == 200
    res = r.json()
    assert any(x["concepto"] == "Filtro Fecha 1" for x in res)
    assert not any(x["concepto"] == "Filtro Fecha 2" for x in res)


def test_listar_pagos_por_fecha(client: TestClient):
    headers = _auth_headers(client)
    socio = _crear_categoria_y_miembro(client, headers)

    # Crear dos pagos en fechas distintas 2030-08 y 2030-09
    p1 = client.post(
        "/api/pagos",
        headers=headers,
        json={
            "miembro_id": socio["id"],
            "tipo": "cuota",
            "concepto": "Pago Ago 2030",
            "monto": 100.0,
            "metodo_pago": "efectivo",
            "fecha_pago": date(2030, 8, 10).isoformat(),
        },
    )
    assert p1.status_code == 201, p1.text

    p2 = client.post(
        "/api/pagos",
        headers=headers,
        json={
            "miembro_id": socio["id"],
            "tipo": "cuota",
            "concepto": "Pago Sep 2030",
            "monto": 120.0,
            "metodo_pago": "efectivo",
            "fecha_pago": date(2030, 9, 12).isoformat(),
        },
    )
    assert p2.status_code == 201, p2.text

    # Filtrar rango dentro de agosto 2030
    r = client.get(
        f"/api/pagos?fecha_inicio={date(2030, 8, 1).isoformat()}&fecha_fin={date(2030, 8, 31).isoformat()}",
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    conceptos = [item["concepto"] for item in body["items"]]
    assert "Pago Ago 2030" in conceptos
    assert "Pago Sep 2030" not in conceptos
