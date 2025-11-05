"""
Tests de auditoría - Verificar registro de actividades
backend/tests/test_auditoria.py
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models.actividad import Actividad, TipoActividad, NivelSeveridad
from app.database import SessionLocal


def create_test_user(client: TestClient, role: str = "operador"):
    """Helper para crear usuario de prueba y retornar headers"""
    unique_id = uuid.uuid4().hex[:8]
    username = f"test_{role}_{unique_id}"
    password = "Test1234"
    
    r = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
            "confirm_password": password,
            "nombre": "Test",
            "apellido": "User",
        },
    )
    assert r.status_code == 201, r.text
    
    # Login para obtener token
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    
    return {
        "headers": {"Authorization": f"Bearer {r.json()['access_token']}"},
        "username": username,
        "user_id": r.json()["user"]["id"]
    }


def create_test_member(client: TestClient, headers: dict):
    """Helper para crear miembro de prueba"""
    unique_id = uuid.uuid4().hex[:8]
    
    # Crear categoría
    r = client.post(
        "/api/miembros/categorias",
        headers=headers,
        json={
            "nombre": f"TestCat_{unique_id}",
            "cuota_base": 1000,
            "tiene_cuota_fija": True,
        },
    )
    assert r.status_code == 201, r.text
    categoria_id = r.json()["id"]
    
    # Crear miembro
    doc = str(abs(hash(unique_id)))[:8]
    r = client.post(
        "/api/miembros",
        headers=headers,
        json={
            "numero_documento": doc,
            "nombre": "Juan",
            "apellido": "Test",
            "categoria_id": categoria_id,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_login_exitoso_crea_actividad(client: TestClient):
    """Verificar que login exitoso registra actividad LOGIN_EXITOSO"""
    user = create_test_user(client)
    
    db = SessionLocal()
    try:
        # Buscar actividad de login exitoso para este usuario
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.LOGIN_EXITOSO,
                Actividad.usuario_id == user["user_id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de login exitoso"
        assert actividad.severidad == NivelSeveridad.INFO
        assert user["username"] in actividad.descripcion
    finally:
        db.close()


def test_login_fallido_crea_actividad(client: TestClient):
    """Verificar que login fallido registra actividad LOGIN_FALLIDO"""
    unique_id = uuid.uuid4().hex[:8]
    fake_user = f"noexiste_{unique_id}"
    
    r = client.post("/api/auth/login", json={"username": fake_user, "password": "wrong"})
    assert r.status_code == 401
    
    db = SessionLocal()
    try:
        # Buscar actividad de login fallido
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.LOGIN_FALLIDO,
                Actividad.descripcion.ilike(f"%{fake_user}%")
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de login fallido"
        assert actividad.severidad == NivelSeveridad.WARNING
        assert fake_user in actividad.descripcion
    finally:
        db.close()


def test_crear_miembro_registra_actividad(client: TestClient):
    """Verificar que crear miembro registra actividad MIEMBRO_CREADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    db = SessionLocal()
    try:
        # Buscar actividad de creación de miembro
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.MIEMBRO_CREADO,
                Actividad.entidad_tipo == "miembro",
                Actividad.entidad_id == miembro["id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de creación de miembro"
        assert actividad.severidad == NivelSeveridad.INFO
        assert actividad.usuario_id == user["user_id"]
        assert miembro["numero_miembro"] in actividad.descripcion
    finally:
        db.close()


def test_eliminar_miembro_registra_actividad(client: TestClient):
    """Verificar que eliminar miembro registra actividad MIEMBRO_ELIMINADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Eliminar miembro (soft delete)
    r = client.delete(f"/api/miembros/{miembro['id']}", headers=user["headers"])
    assert r.status_code == 200, r.text
    
    db = SessionLocal()
    try:
        # Buscar actividad de eliminación
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.MIEMBRO_ELIMINADO,
                Actividad.entidad_tipo == "miembro",
                Actividad.entidad_id == miembro["id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de eliminación de miembro"
        assert actividad.usuario_id == user["user_id"]
        assert miembro["numero_miembro"] in actividad.descripcion
    finally:
        db.close()


def test_cambiar_estado_miembro_registra_actividad(client: TestClient):
    """Verificar que cambiar estado de miembro registra actividad MIEMBRO_EDITADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Cambiar estado a SUSPENDIDO
    r = client.post(
        f"/api/miembros/{miembro['id']}/cambiar-estado",
        headers=user["headers"],
        json={
            "miembro_id": miembro["id"],
            "nuevo_estado": "suspendido",
            "motivo": "Test de auditoría"
        }
    )
    assert r.status_code == 200, r.text
    
    db = SessionLocal()
    try:
        # Buscar actividad de cambio de estado
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.MIEMBRO_EDITADO,
                Actividad.entidad_tipo == "miembro",
                Actividad.entidad_id == miembro["id"]
            )
            .order_by(Actividad.fecha_hora.desc())
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de cambio de estado"
        assert actividad.usuario_id == user["user_id"]
        assert "suspendido" in actividad.descripcion.lower()
        assert actividad.datos_adicionales is not None
        assert actividad.datos_adicionales.get("estado_nuevo") == "suspendido"
        assert actividad.datos_adicionales.get("estado_anterior") == "activo"
    finally:
        db.close()


def test_registrar_pago_crea_actividad(client: TestClient):
    """Verificar que registrar pago registra actividad PAGO_REGISTRADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Registrar pago
    r = client.post(
        "/api/pagos",
        headers=user["headers"],
        json={
            "miembro_id": miembro["id"],
            "tipo": "cuota",
            "concepto": "Pago test auditoría",
            "monto": 1500.0,
            "descuento": 0.0,
            "recargo": 0.0,
            "metodo_pago": "efectivo"
        }
    )
    assert r.status_code == 201, r.text
    pago = r.json()
    
    db = SessionLocal()
    try:
        # Buscar actividad de pago
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.PAGO_REGISTRADO,
                Actividad.entidad_tipo == "pago",
                Actividad.entidad_id == pago["id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de pago"
        assert actividad.usuario_id == user["user_id"]
        assert actividad.datos_adicionales is not None
        assert actividad.datos_adicionales.get("monto") == 1500.0
    finally:
        db.close()


def test_anular_pago_crea_actividad(client: TestClient):
    """Verificar que anular pago registra actividad PAGO_ANULADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Registrar pago
    r = client.post(
        "/api/pagos",
        headers=user["headers"],
        json={
            "miembro_id": miembro["id"],
            "tipo": "cuota",
            "concepto": "Pago a anular",
            "monto": 1000.0,
            "descuento": 0.0,
            "recargo": 0.0,
            "metodo_pago": "efectivo"
        }
    )
    assert r.status_code == 201, r.text
    pago = r.json()
    
    # Anular pago
    r = client.post(
        f"/api/pagos/{pago['id']}/anular",
        headers=user["headers"],
        json={"motivo": "Test de auditoría"}
    )
    assert r.status_code == 200, r.text
    
    db = SessionLocal()
    try:
        # Buscar actividad de anulación
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.PAGO_ANULADO,
                Actividad.entidad_tipo == "pago",
                Actividad.entidad_id == pago["id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de anulación"
        assert actividad.usuario_id == user["user_id"]
        assert actividad.datos_adicionales is not None
        assert "Test de auditoría" in str(actividad.datos_adicionales.get("motivo"))
    finally:
        db.close()


def test_acceso_manual_crea_actividad(client: TestClient):
    """Verificar que acceso manual registra actividad ACCESO_PERMITIDO o ACCESO_DENEGADO"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Registrar acceso manual
    r = client.post(
        "/api/accesos/manual",
        headers=user["headers"],
        json={
            "miembro_id": miembro["id"],
            "ubicacion": "Entrada principal",
            "observaciones": "Test de auditoría",
            "forzar_acceso": True
        }
    )
    assert r.status_code == 200, r.text
    acceso = r.json()
    
    db = SessionLocal()
    try:
        # Buscar actividad de acceso
        actividad = (
            db.query(Actividad)
            .filter(
                Actividad.tipo == TipoActividad.ACCESO_PERMITIDO,
                Actividad.entidad_tipo == "acceso",
                Actividad.entidad_id == acceso["id"]
            )
            .first()
        )
        
        assert actividad is not None, "No se registró actividad de acceso manual"
        assert miembro["numero_miembro"] in str(actividad.datos_adicionales.get("miembro"))
    finally:
        db.close()


def test_auditoria_no_rompe_operacion_principal(client: TestClient, monkeypatch):
    """Verificar que si falla la auditoría, la operación principal continúa"""
    user = create_test_user(client)
    miembro = create_test_member(client, user["headers"])
    
    # Forzar fallo en auditoría (mock)
    from app.services.audit_service import AuditService
    original_registrar = AuditService.registrar
    
    def _failing_registrar(*args, **kwargs):
        raise RuntimeError("Fallo simulado en auditoría")
    
    monkeypatch.setattr(AuditService, "registrar", _failing_registrar)
    
    # El pago debe registrarse exitosamente a pesar del fallo en auditoría
    # porque audit_service.py tiene try/except que no propaga el error
    r = client.post(
        "/api/pagos",
        headers=user["headers"],
        json={
            "miembro_id": miembro["id"],
            "tipo": "cuota",
            "concepto": "Pago con auditoría fallida",
            "monto": 1000.0,
            "descuento": 0.0,
            "recargo": 0.0,
            "metodo_pago": "efectivo"
        }
    )
    
    # La operación debe ser exitosa
    assert r.status_code == 201, r.text
    pago = r.json()
    assert pago["monto_final"] == 1000.0
    
    # Restaurar método original
    monkeypatch.setattr(AuditService, "registrar", original_registrar)
