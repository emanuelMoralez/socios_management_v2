from fastapi.testclient import TestClient


def _headers(client: TestClient):
    r = client.post(
        "/api/auth/register",
        json={
            "username": "reporter",
            "email": "reporter@example.com",
            "password": "Admin1234",
            "confirm_password": "Admin1234",
            "nombre": "Report",
            "apellido": "User",
        },
    )
    assert r.status_code in (201, 400)
    r = client.post("/api/auth/login", json={"username": "reporter", "password": "Admin1234"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_ingresos_historicos_y_accesos_detallados(client: TestClient):
    headers = _headers(client)

    r = client.get("/api/reportes/ingresos-historicos?meses=3", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_meses"] == 3
    assert len(body["historico"]) == 3
    assert {"mes", "ingresos", "egresos", "balance"}.issubset(body["historico"][0].keys())

    r = client.get("/api/reportes/accesos-detallados", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "accesos_por_hora" in body and len(body["accesos_por_hora"]) == 24
    assert "estadisticas" in body
