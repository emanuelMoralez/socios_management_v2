from fastapi.testclient import TestClient
from datetime import date, timedelta
import uuid

from app.database import SessionLocal


def _auth_headers(client: TestClient):
    """Crear usuario operador y devolver headers con Bearer token."""
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


def _crear_categoria(client: TestClient, headers):
    unique_id = uuid.uuid4().hex[:8]
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
    return r.json()["id"]


def _crear_miembro(client: TestClient, headers, categoria_id: int, con_email=True):
    unique_id = uuid.uuid4().hex[:8]
    doc_numerico = str(abs(hash(unique_id)))[:8]
    payload = {
        "numero_documento": doc_numerico,
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": (f"juan_{unique_id}@example.com" if con_email else None),
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
    return r.json()


def _forzar_deuda(miembro_id: int, monto: float = 150.0, dias_mora: int = 10):
    """Ajustar saldo y vencimiento directamente en la DB para simular deuda."""
    db = SessionLocal()
    try:
        from app.models.miembro import Miembro, EstadoMiembro
        m = db.query(Miembro).filter(Miembro.id == miembro_id).first()
        assert m is not None
        m.saldo_cuenta = -abs(monto)
        m.estado = EstadoMiembro.MOROSO
        m.proximo_vencimiento = date.today() - timedelta(days=dias_mora)
        db.commit()
    finally:
        db.close()


def test_preview_morosos(client: TestClient):
    headers = _auth_headers(client)
    cat_id = _crear_categoria(client, headers)
    socio = _crear_miembro(client, headers, cat_id, con_email=True)
    _forzar_deuda(socio["id"], monto=200, dias_mora=12)

    r = client.get("/api/notificaciones/preview-morosos?solo_morosos=true&dias_mora_minimo=5", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_destinatarios"] >= 1
    assert body["filtros"]["solo_morosos"] is True


def test_recordatorio_individual_exito_con_mock(client: TestClient, monkeypatch):
    headers = _auth_headers(client)
    cat_id = _crear_categoria(client, headers)
    socio = _crear_miembro(client, headers, cat_id, con_email=True)
    _forzar_deuda(socio["id"], monto=120, dias_mora=20)

    # Mockear el servicio para evitar SMTP real
    async def _fake_send(**kwargs):
        return {"success": True, "email": "fake@example.com"}

    from app.services import notification_service
    monkeypatch.setattr(notification_service.NotificationService, "enviar_recordatorio_individual", _fake_send)

    r = client.post(f"/api/notificaciones/recordatorio?miembro_id={socio['id']}", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["message"].startswith("Recordatorio enviado")


def test_recordatorio_individual_sin_deuda(client: TestClient):
    headers = _auth_headers(client)
    cat_id = _crear_categoria(client, headers)
    socio = _crear_miembro(client, headers, cat_id, con_email=True)
    # Sin deuda

    r = client.post(f"/api/notificaciones/recordatorio?miembro_id={socio['id']}", headers=headers)
    assert r.status_code == 400


def test_test_email_config_sin_config(client: TestClient, monkeypatch):
    # Forzar configuración SMTP incompleta
    from app.config import settings
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    headers = _auth_headers(client)
    r = client.get("/api/notificaciones/test-email", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
