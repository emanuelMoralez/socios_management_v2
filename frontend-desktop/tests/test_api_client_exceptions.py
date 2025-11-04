"""
Tests básicos para las nuevas excepciones del APIClient
frontend-desktop/tests/test_api_client_exceptions.py

Ejecutar: pytest tests/test_api_client_exceptions.py
"""

import pytest
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.api_client import (
    APIException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APITimeoutError
)


def test_exception_inheritance():
    """Verificar que todas las excepciones heredan correctamente"""
    # Todas deben heredar de APIException
    assert issubclass(AuthenticationError, APIException)
    assert issubclass(ValidationError, APIException)
    assert issubclass(NotFoundError, APIException)
    assert issubclass(APITimeoutError, APIException)
    
    # APIException debe heredar de Exception
    assert issubclass(APIException, Exception)


def test_authentication_error():
    """Test de AuthenticationError"""
    error = AuthenticationError("Token expirado")
    assert str(error) == "Token expirado"
    assert isinstance(error, APIException)
    assert isinstance(error, Exception)


def test_validation_error():
    """Test de ValidationError"""
    error = ValidationError("Email inválido")
    assert str(error) == "Email inválido"
    assert isinstance(error, APIException)


def test_not_found_error():
    """Test de NotFoundError"""
    error = NotFoundError("Miembro no encontrado")
    assert str(error) == "Miembro no encontrado"
    assert isinstance(error, APIException)


def test_api_timeout_error():
    """Test de APITimeoutError"""
    error = APITimeoutError("Timeout después de 30s")
    assert str(error) == "Timeout después de 30s"
    assert isinstance(error, APIException)


def test_exception_catching():
    """Verificar que se pueden capturar específicamente"""
    
    # Lanzar y capturar AuthenticationError
    try:
        raise AuthenticationError("Test")
    except AuthenticationError as e:
        assert str(e) == "Test"
    except APIException:
        pytest.fail("Debería capturar AuthenticationError específicamente")
    
    # Capturar como APIException genérica
    try:
        raise ValidationError("Test")
    except APIException as e:
        assert isinstance(e, ValidationError)
    
    # Verificar que se puede distinguir entre tipos
    try:
        raise NotFoundError("404")
    except AuthenticationError:
        pytest.fail("No debería capturar como AuthenticationError")
    except NotFoundError as e:
        assert str(e) == "404"


def test_exception_hierarchy():
    """Verificar que el orden de captura funciona correctamente"""
    
    def raise_specific_error():
        raise ValidationError("Datos inválidos")
    
    # Captura específica primero
    try:
        raise_specific_error()
    except ValidationError as e:
        assert str(e) == "Datos inválidos"
    except APIException:
        pytest.fail("Debería capturar ValidationError antes que APIException")
    
    # Captura genérica funciona
    try:
        raise_specific_error()
    except APIException as e:
        assert isinstance(e, ValidationError)


def test_multiple_exceptions():
    """Test de manejo de múltiples excepciones"""
    
    def simular_error(tipo: str):
        if tipo == "auth":
            raise AuthenticationError("401")
        elif tipo == "validation":
            raise ValidationError("422")
        elif tipo == "not_found":
            raise NotFoundError("404")
        elif tipo == "timeout":
            raise APITimeoutError("Timeout")
        else:
            raise APIException("Error genérico")
    
    # Test cada tipo
    with pytest.raises(AuthenticationError):
        simular_error("auth")
    
    with pytest.raises(ValidationError):
        simular_error("validation")
    
    with pytest.raises(NotFoundError):
        simular_error("not_found")
    
    with pytest.raises(APITimeoutError):
        simular_error("timeout")
    
    with pytest.raises(APIException):
        simular_error("otro")


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
