#!/usr/bin/env python3
"""
Test para debuggear ValidationError
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.api_client import ValidationError, APIException

# Test 1: Crear ValidationError con kwargs
print("=" * 60)
print("TEST 1: Crear ValidationError con keyword arguments")
print("=" * 60)

try:
    error = ValidationError(
        message="Datos inválidos al crear socio",
        status_code=422,
        details={
            "errors": [
                {
                    "field": "email",
                    "message": "value is not a valid email address"
                }
            ]
        }
    )
    print(f"✅ ValidationError creado correctamente")
    print(f"   Tipo: {type(error)}")
    print(f"   Mensaje: {error.message}")
    print(f"   Status: {error.status_code}")
    print(f"   Tiene details: {hasattr(error, 'details')}")
    print(f"   Details: {error.details}")
    print(f"   isinstance(error, ValidationError): {isinstance(error, ValidationError)}")
    print(f"   isinstance(error, APIException): {isinstance(error, APIException)}")
    print(f"   isinstance(error, Exception): {isinstance(error, Exception)}")
    
except Exception as e:
    print(f"❌ Error al crear ValidationError:")
    print(f"   Tipo: {type(e)}")
    print(f"   Mensaje: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Lanzar y capturar
print("\n" + "=" * 60)
print("TEST 2: Lanzar y capturar ValidationError")
print("=" * 60)

try:
    raise ValidationError(
        message="Test error",
        status_code=422,
        details={"test": "data"}
    )
except ValidationError as e:
    print(f"✅ ValidationError capturado correctamente en except ValidationError")
    print(f"   Mensaje: {e.message}")
    print(f"   Detalles: {e.details}")
except APIException as e:
    print(f"⚠️ Capturado como APIException en lugar de ValidationError")
    print(f"   Mensaje: {e.message}")
except Exception as e:
    print(f"❌ Capturado como Exception genérico")
    print(f"   Tipo: {type(e)}")
    print(f"   Mensaje: {e}")

# Test 3: Simular lo que pasa en _request
print("\n" + "=" * 60)
print("TEST 3: Simular flujo de _request")
print("=" * 60)

def simular_request():
    """Simular el flujo del método _request"""
    try:
        # Simular respuesta 422
        print("1. Simulando respuesta 422...")
        error_detail = {
            "errors": [
                {
                    "field": "email",
                    "message": "invalid email"
                }
            ]
        }
        
        print("2. Creando ValidationError...")
        raise ValidationError(
            message="Datos inválidos",
            status_code=422,
            details=error_detail
        )
        
    except ValidationError:
        print("3. ✅ ValidationError capturado y re-lanzado")
        raise
    except Exception as e:
        print(f"3. ❌ Capturado como Exception: {type(e).__name__}: {e}")
        raise

try:
    simular_request()
except ValidationError as e:
    print(f"4. ✅ ValidationError llegó al caller")
    print(f"   Mensaje: {e.message}")
    print(f"   Detalles: {e.details}")
except Exception as e:
    print(f"4. ❌ Llegó como Exception: {type(e).__name__}")
    print(f"   Mensaje: {e}")

print("\n" + "=" * 60)
print("FIN DE TESTS")
print("=" * 60)
