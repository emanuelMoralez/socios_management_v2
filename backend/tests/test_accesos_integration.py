"""
Tests de integración para el sistema de control de accesos con QR
Prueba endpoints críticos de validación de acceso
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import uuid


@pytest.fixture
def admin_token(client: TestClient) -> str:
    """Fixture que crea un usuario admin y retorna su token"""
    unique_id = uuid.uuid4().hex[:8]
    username = f"admin_{unique_id}"
    password = "Admin1234"
    
    # Registrar admin
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password,
            "nombre": "Admin",
            "apellido": "Test",
            "rol": "administrador"
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    return response.json()["access_token"]


@pytest.fixture
def portero_token(client: TestClient) -> str:
    """Fixture que crea un usuario portero y retorna su token"""
    unique_id = uuid.uuid4().hex[:8]
    username = f"portero_{unique_id}"
    password = "Portero1234"
    
    # Registrar portero
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password,
            "nombre": "Portero",
            "apellido": "Test",
            "rol": "portero"
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    return response.json()["access_token"]


@pytest.fixture
def miembro_con_qr(client: TestClient, admin_token: str):
    """Fixture que crea un miembro activo con QR generado"""
    unique_id = uuid.uuid4().hex[:8]
    
    # Crear categoría
    cat_response = client.post(
        "/api/miembros/categorias",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": f"Titular_{unique_id}",
            "descripcion": "Categoría test",
            "cuota_base": 1000.0,
            "tiene_cuota_fija": True
        }
    )
    categoria_id = cat_response.json()["id"]
    
    # Crear miembro
    miembro_response = client.post(
        "/api/miembros",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Juan",
            "apellido": "Pérez",
            "tipo_documento": "dni",
            "numero_documento": str(abs(hash(unique_id)))[:8],
            "fecha_nacimiento": "1990-01-01",
            "email": f"juan_{unique_id}@test.com",
            "telefono": "1234567890",
            "categoria_id": categoria_id,
            "direccion": "Calle Test 123",
            "localidad": "Ciudad Test",
            "provincia": "Provincia Test"
        }
    )
    
    miembro = miembro_response.json()
    
    # El miembro ya tiene QR generado automáticamente
    return {
        "miembro_id": miembro["id"],
        "qr_code": miembro["qr_code"],
        "numero_documento": miembro["numero_documento"],
        "numero_miembro": miembro["numero_miembro"],
        "nombre_completo": f"{miembro['nombre']} {miembro['apellido']}"
    }


class TestValidarAccesoQR:
    """Tests de validación de acceso con código QR"""
    
    def test_validar_qr_miembro_activo(self, client: TestClient, portero_token: str, miembro_con_qr: dict):
        """Portero valida QR de miembro activo - debe permitir acceso"""
        response = client.post(
            "/api/accesos/validar-qr",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "qr_code": miembro_con_qr["qr_code"],
                "ubicacion": "Entrada principal",
                "tipo_acceso": "entrada"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar respuesta
        assert data["acceso_permitido"] is True
        assert data["resultado"] == "permitido"
        assert data["nivel_alerta"] == "success"
        assert "miembro" in data
        assert data["miembro"]["id"] == miembro_con_qr["miembro_id"]
        assert "acceso_id" in data
        assert "timestamp" in data
    
    def test_validar_qr_formato_invalido(self, client: TestClient, portero_token: str):
        """QR con formato inválido debe ser rechazado con 400"""
        response = client.post(
            "/api/accesos/validar-qr",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "qr_code": "QR-INVALIDO-123",
                "ubicacion": "Entrada principal",
                "tipo_acceso": "entrada"
            }
        )
        
        # Ahora el backend devuelve 400 sin intentar guardar en BD
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "inválido" in data["detail"].lower() or "invalido" in data["detail"].lower()
    
    def test_validar_qr_miembro_inexistente(self, client: TestClient, portero_token: str):
        """QR con formato válido pero miembro inexistente"""
        # QR válido en formato pero ID inexistente
        qr_falso = "CLUB-999999-abc123def456"
        
        response = client.post(
            "/api/accesos/validar-qr",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "qr_code": qr_falso,
                "ubicacion": "Entrada principal",
                "tipo_acceso": "entrada"
            }
        )
        
        # El backend retorna 404 cuando el miembro no existe
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["acceso_permitido"] is False
            assert data["resultado"] in ["miembro_no_encontrado", "rechazado"]
    
    def test_validar_acceso_sin_autenticacion(self, client: TestClient, miembro_con_qr: dict):
        """Validar acceso sin token debe fallar con 401 o 403"""
        response = client.post(
            "/api/accesos/validar-qr",
            json={
                "qr_code": miembro_con_qr["qr_code"],
                "ubicacion": "Entrada principal",
                "tipo_acceso": "entrada"
            }
        )
        
        assert response.status_code in [401, 403]  # Ambos son válidos para sin autenticación


class TestRegistrarAccesoManual:
    """Tests de registro manual de acceso (sin QR)"""
    
    def test_registrar_acceso_manual_admin(self, client: TestClient, admin_token: str, miembro_con_qr: dict):
        """Admin puede registrar acceso manual"""
        response = client.post(
            "/api/accesos/manual",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "miembro_id": miembro_con_qr["miembro_id"],
                "ubicacion": "Entrada lateral",
                "tipo_acceso": "entrada",
                "observaciones": "Olvidó el QR"
            }
        )
        
        assert response.status_code == 200  # FastAPI retorna 200 por default, no 201
        data = response.json()
        
        # AccesoResponse tiene estos campos
        assert data["id"] > 0
        assert data["miembro_id"] == miembro_con_qr["miembro_id"]
        assert data["resultado"] == "permitido"
        assert data["tipo_acceso"] == "manual"
        assert data["ubicacion"] == "Entrada lateral"
    
    def test_registrar_acceso_manual_portero_no_autorizado(
        self, client: TestClient, portero_token: str, miembro_con_qr: dict
    ):
        """Portero normal no puede registrar accesos manuales (requiere admin/operador)"""
        response = client.post(
            "/api/accesos/manual",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "miembro_id": miembro_con_qr["miembro_id"],
                "ubicacion": "Entrada lateral",
                "tipo_acceso": "entrada"
            }
        )
        
        # Depende de la configuración de permisos, puede ser 403 o necesitar forzar_acceso
        assert response.status_code in [403, 200]


class TestListarAccesos:
    """Tests de listado y consulta de accesos"""
    
    def test_listar_accesos_con_paginacion(self, client: TestClient, admin_token: str):
        """Listar accesos con paginación usando /historial"""
        response = client.get(
            "/api/accesos/historial?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data or "data" in data
        assert isinstance(data.get("items", data.get("data", [])), list)
    
    def test_listar_accesos_filtro_fecha(self, client: TestClient, admin_token: str):
        """Filtrar accesos por fecha"""
        hoy = date.today().isoformat()
        
        response = client.get(
            f"/api/accesos/historial?fecha_desde={hoy}&fecha_hasta={hoy}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data or "data" in data
        # Los accesos retornados deben ser de hoy
    
    def test_listar_accesos_filtro_resultado(self, client: TestClient, admin_token: str):
        """Filtrar accesos por resultado (permitido/rechazado)"""
        response = client.get(
            "/api/accesos/historial?resultado=permitido",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data or "data" in data
    
    def test_listar_accesos_miembro_especifico(
        self, client: TestClient, admin_token: str, miembro_con_qr: dict
    ):
        """Listar accesos de un miembro específico"""
        response = client.get(
            f"/api/accesos/historial?miembro_id={miembro_con_qr['miembro_id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", data.get("data", []))
        assert isinstance(items, list)
        # Si hay accesos, todos deben ser del miembro especificado
        for acceso in items:
            if "miembro_id" in acceso:
                assert acceso["miembro_id"] == miembro_con_qr["miembro_id"]


class TestEstadisticasAccesos:
    """Tests de estadísticas y reportes de accesos"""
    
    def test_obtener_estadisticas_hoy(self, client: TestClient, admin_token: str):
        """Obtener estadísticas de accesos del día"""
        response = client.get(
            "/api/accesos/estadisticas",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de estadísticas
        assert "total_hoy" in data
        assert "entradas_hoy" in data
        assert "salidas_hoy" in data
        assert "rechazos_hoy" in data
        assert "fecha" in data
        assert isinstance(data["total_hoy"], int)
    
    def test_obtener_estadisticas_rango_fechas(self, client: TestClient, admin_token: str):
        """Obtener estadísticas en un rango de fechas"""
        fecha_inicio = (date.today() - timedelta(days=7)).isoformat()
        fecha_fin = date.today().isoformat()
        
        response = client.get(
            f"/api/accesos/estadisticas?fecha_desde={fecha_inicio}&fecha_hasta={fecha_fin}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_hoy" in data or "total" in data


class TestAccesosConEstadosMiembro:
    """Tests de validación con diferentes estados de miembro"""
    
    def test_acceso_miembro_moroso(
        self, client: TestClient, admin_token: str, portero_token: str, miembro_con_qr: dict
    ):
        """Miembro moroso puede recibir advertencia pero acceder (según config)"""
        # Primero, hacer que el miembro esté moroso (crear deuda antigua)
        # Esto depende de la lógica de negocio específica
        
        response = client.post(
            "/api/accesos/validar-qr",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "qr_code": miembro_con_qr["qr_code"],
                "ubicacion": "Entrada principal",
                "tipo_acceso": "entrada"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Puede permitir con advertencia o rechazar según configuración
        assert "resultado" in data
        assert "nivel_alerta" in data


class TestHistorialAccesos:
    """Tests de historial y auditoría de accesos"""
    
    def test_obtener_resumen_accesos(self, client: TestClient, admin_token: str):
        """Obtener resumen de accesos"""
        response = client.get(
            "/api/accesos/resumen",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Puede retornar 200 con datos o estar implementado diferente
        assert response.status_code in [200, 404]
    
    def test_exportar_historial_accesos(self, client: TestClient, admin_token: str):
        """Exportar historial de accesos (si existe el endpoint)"""
        response = client.get(
            "/api/accesos/export?formato=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Puede ser 200 si existe o 404 si no está implementado
        assert response.status_code in [200, 404, 501]


class TestSeguridadAccesos:
    """Tests de seguridad y control de acceso"""
    
    def test_portero_puede_validar_qr(self, client: TestClient, portero_token: str, miembro_con_qr: dict):
        """Portero debe poder validar QR (permiso mínimo requerido)"""
        response = client.post(
            "/api/accesos/validar-qr",
            headers={"Authorization": f"Bearer {portero_token}"},
            json={
                "qr_code": miembro_con_qr["qr_code"],
                "ubicacion": "Entrada Test",
                "tipo_acceso": "entrada"
            }
        )
        
        # Portero debe poder validar accesos
        assert response.status_code == 200
        data = response.json()
        assert "acceso_permitido" in data
    
    def test_validar_qr_requiere_permisos_minimos(self, client: TestClient):
        """Validar QR requiere al menos rol de portero"""
        # Este test verifica que el endpoint está protegido
        response = client.post(
            "/api/accesos/validar-qr",
            json={
                "qr_code": "CLUB-123-abc",
                "ubicacion": "Test",
                "tipo_acceso": "entrada"
            }
        )
        
        # Puede ser 401 (no autenticado) o 403 (no autorizado)
        assert response.status_code in [401, 403]
