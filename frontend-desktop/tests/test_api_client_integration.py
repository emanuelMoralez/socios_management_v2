"""
Tests de integración para APIClient
frontend-desktop/tests/test_api_client_integration.py

Estos tests requieren que el backend esté corriendo en localhost:8000
Ejecutar: pytest tests/test_api_client_integration.py -v -s
"""

import pytest
import sys
from pathlib import Path
import asyncio

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.api_client import (
    APIClient,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APITimeoutError,
    APIException
)


# Fixture para cliente limpio
@pytest.fixture
def api_client():
    """Cliente API limpio para cada test"""
    client = APIClient()
    # Limpiar tokens de tests previos
    client.token = None
    client.refresh_token = None
    return client


# ==================== TESTS DE ESTRUCTURA ====================

def test_api_client_initialization(api_client):
    """Test de inicialización del cliente"""
    assert api_client.base_url is not None
    assert api_client.timeout > 0
    assert api_client.token is None
    assert api_client.refresh_token is None


def test_api_client_headers_without_token(api_client):
    """Test de headers sin token"""
    headers = api_client._get_headers()
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"
    assert "Authorization" not in headers


def test_api_client_headers_with_token(api_client):
    """Test de headers con token"""
    api_client.token = "test_token_123"
    headers = api_client._get_headers()
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer test_token_123"


def test_logout_clears_tokens(api_client):
    """Test de que logout limpia los tokens"""
    api_client.token = "test_token"
    api_client.refresh_token = "test_refresh"
    
    api_client.logout()
    
    assert api_client.token is None
    assert api_client.refresh_token is None


# ==================== TESTS CON BACKEND (REQUIERE SERVIDOR CORRIENDO) ====================

@pytest.mark.asyncio
async def test_login_invalid_credentials(api_client):
    """Test de login con credenciales inválidas"""
    try:
        await api_client.login("usuario_invalido", "password_invalida")
        pytest.fail("Debería lanzar excepción con credenciales inválidas")
    except (AuthenticationError, APIException) as e:
        # Esperado: credenciales inválidas
        assert True


@pytest.mark.asyncio
async def test_request_without_auth_should_fail(api_client):
    """Test de que peticiones sin auth fallan apropiadamente"""
    try:
        # Intentar obtener miembros sin token
        await api_client.get_miembros()
        pytest.fail("Debería requerir autenticación")
    except (AuthenticationError, APIException):
        # Esperado: necesita autenticación
        assert True


@pytest.mark.asyncio
async def test_get_categorias_without_auth_may_work(api_client):
    """Test de endpoints públicos (si existen)"""
    # Este test depende de si hay endpoints públicos
    # Ajustar según configuración del backend
    pass


# ==================== TESTS DE MÉTODOS ESPECÍFICOS ====================

def test_get_miembros_signature(api_client):
    """Verificar que get_miembros tiene la firma correcta"""
    import inspect
    sig = inspect.signature(api_client.get_miembros)
    params = list(sig.parameters.keys())
    
    assert 'page' in params
    assert 'page_size' in params
    assert 'q' in params
    assert 'estado' in params


def test_get_accesos_signature(api_client):
    """Verificar que get_accesos tiene TODOS los filtros (no duplicado)"""
    import inspect
    sig = inspect.signature(api_client.get_accesos)
    params = list(sig.parameters.keys())
    
    # Verificar que tiene los filtros completos
    assert 'page' in params
    assert 'page_size' in params
    assert 'miembro_id' in params
    assert 'fecha_inicio' in params
    assert 'fecha_fin' in params
    assert 'resultado' in params


def test_new_methods_exist(api_client):
    """Verificar que los métodos nuevos existen"""
    assert hasattr(api_client, 'get_dashboard')
    assert hasattr(api_client, 'cambiar_estado_miembro')
    assert hasattr(api_client, 'get_miembro_estado_financiero')
    assert hasattr(api_client, 'registrar_acceso_manual')
    assert hasattr(api_client, 'preview_morosos')
    assert hasattr(api_client, 'refresh_access_token')


def test_deprecated_methods_removed(api_client):
    """Verificar que los métodos obsoletos NO existen"""
    assert not hasattr(api_client, 'obtener_historial_accesos')
    assert not hasattr(api_client, 'obtener_resumen_accesos')
    assert not hasattr(api_client, 'obtener_estadisticas_accesos')


# ==================== TESTS DE DOCUMENTACIÓN ====================

def test_methods_have_docstrings(api_client):
    """Verificar que los métodos públicos tienen docstrings"""
    public_methods = [
        'login', 'logout', 'get_current_user',
        'get_miembros', 'create_miembro', 'update_miembro',
        'get_pagos', 'create_pago',
        'get_accesos', 'validar_acceso_qr',
        'get_dashboard', 'cambiar_estado_miembro'
    ]
    
    for method_name in public_methods:
        method = getattr(api_client, method_name)
        assert method.__doc__ is not None, f"{method_name} no tiene docstring"
        assert len(method.__doc__.strip()) > 10, f"{method_name} tiene docstring muy corto"


# ==================== TESTS DE TIMEOUTS ====================

def test_request_method_has_timeout_parameter(api_client):
    """Verificar que _request tiene parámetro timeout"""
    import inspect
    sig = inspect.signature(api_client._request)
    assert 'timeout' in sig.parameters


def test_request_method_has_retry_auth_parameter(api_client):
    """Verificar que _request tiene parámetro retry_auth para auto-refresh"""
    import inspect
    sig = inspect.signature(api_client._request)
    assert 'retry_auth' in sig.parameters


# ==================== RESUMEN ====================

def test_api_client_completeness():
    """Test general de completitud del API Client"""
    client = APIClient()
    
    # Verificar estructura básica
    assert hasattr(client, 'base_url')
    assert hasattr(client, 'timeout')
    assert hasattr(client, 'token')
    assert hasattr(client, 'refresh_token')
    
    # Verificar métodos core
    core_methods = [
        '_get_headers', '_request', 'login', 'logout',
        'refresh_access_token'  # NUEVO: Auto-refresh
    ]
    for method in core_methods:
        assert hasattr(client, method), f"Falta método core: {method}"
    
    # Verificar secciones de API
    sections = {
        'Auth': ['login', 'logout', 'get_current_user', 'refresh_access_token'],
        'Miembros': ['get_miembros', 'get_miembro', 'create_miembro', 'update_miembro', 'delete_miembro'],
        'Pagos': ['get_pagos', 'create_pago', 'get_resumen_financiero'],
        'Accesos': ['get_accesos', 'validar_acceso_qr', 'registrar_acceso_manual'],
        'Reportes': ['get_dashboard', 'get_reporte_socios', 'get_reporte_financiero'],
        'Notificaciones': ['preview_morosos', 'enviar_recordatorios_masivos']
    }
    
    for section, methods in sections.items():
        for method in methods:
            assert hasattr(client, method), f"Falta método de {section}: {method}"
    
    print(f"\n✅ API Client completo con {len([m for m in dir(client) if not m.startswith('_')])} métodos públicos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
