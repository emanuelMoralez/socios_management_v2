#!/usr/bin/env python3
"""
Script de test rápido para validar error handling en la UI
frontend-desktop/test_error_handling.py

Este script prueba las nuevas excepciones sin necesidad de levantar
la aplicación completa.
"""
import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.api_client import (
    APIClient,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    APITimeoutError,
    APIException
)


async def test_exceptions():
    """Probar que las excepciones se lanzan correctamente"""
    
    print("=" * 60)
    print("TEST DE EXCEPCIONES DEL API CLIENT")
    print("=" * 60)
    
    client = APIClient()
    
    # Test 1: Validar que el cliente se inicializa
    print("\n✅ Test 1: Cliente inicializado correctamente")
    print(f"   Base URL: {client.base_url}")
    
    # Test 2: Probar ValidationError (email inválido)
    print("\n🧪 Test 2: ValidationError - Email inválido")
    print("   Intentando crear socio con email inválido...")
    
    try:
        # Este debería fallar con ValidationError si el backend valida
        await client.create_miembro({
            "nombre": "Test",
            "apellido": "Usuario",
            "numero_documento": "12345678",
            "tipo_documento": "dni",
            "email": "email_invalido_sin_arroba",  # Email sin @
            "categoria_id": 1,
            "modulo_tipo": "generico"
        })
        print("   ❌ FALLÓ: No se lanzó excepción")
        
    except ValidationError as e:
        print(f"   ✅ CORRECTO: Se capturó ValidationError")
        print(f"   Mensaje: {str(e)}")
        if hasattr(e, 'details'):
            print(f"   Detalles: {e.details}")
            
    except AuthenticationError:
        print("   ⚠️ AuthenticationError: Necesitas hacer login primero")
        print("   (Esto es normal si no estás autenticado)")
        
    except Exception as e:
        print(f"   ⚠️ Otra excepción: {type(e).__name__}: {e}")
    
    # Test 3: NotFoundError
    print("\n🧪 Test 3: NotFoundError - Recurso inexistente")
    print("   Intentando obtener socio con ID 999999...")
    
    try:
        await client.get_miembro(999999)
        print("   ❌ FALLÓ: No se lanzó excepción")
        
    except NotFoundError as e:
        print(f"   ✅ CORRECTO: Se capturó NotFoundError")
        print(f"   Mensaje: {str(e)}")
        
    except AuthenticationError:
        print("   ⚠️ AuthenticationError: Necesitas hacer login primero")
        
    except Exception as e:
        print(f"   ⚠️ Otra excepción: {type(e).__name__}: {e}")
    
    # Test 4: Verificar métodos nuevos existen
    print("\n🧪 Test 4: Verificar métodos nuevos")
    nuevos_metodos = [
        "get_dashboard",
        "cambiar_estado_miembro",
        "get_miembro_estado_financiero",
        "registrar_acceso_manual",
        "preview_morosos",
        "exportar_accesos_excel"
    ]
    
    for metodo in nuevos_metodos:
        existe = hasattr(client, metodo)
        symbol = "✅" if existe else "❌"
        print(f"   {symbol} {metodo}: {'existe' if existe else 'NO EXISTE'}")
    
    # Test 5: Verificar que métodos obsoletos NO existen
    print("\n🧪 Test 5: Verificar que métodos obsoletos fueron eliminados")
    obsoletos = [
        "obtener_historial_accesos",
        "obtener_resumen_accesos",
        "obtener_estadisticas_accesos"
    ]
    
    for metodo in obsoletos:
        existe = hasattr(client, metodo)
        symbol = "❌" if existe else "✅"
        status = "TODAVÍA EXISTE (MAL)" if existe else "eliminado correctamente"
        print(f"   {symbol} {metodo}: {status}")
    
    # Test 6: Verificar refresh_access_token
    print("\n🧪 Test 6: Verificar método refresh_access_token")
    tiene_refresh = hasattr(client, 'refresh_access_token')
    if tiene_refresh:
        print("   ✅ refresh_access_token existe")
        # Verificar firma
        import inspect
        sig = inspect.signature(client.refresh_access_token)
        print(f"   Firma: {sig}")
    else:
        print("   ❌ refresh_access_token NO EXISTE")
    
    # Test 7: Verificar _request tiene retry_auth
    print("\n🧪 Test 7: Verificar que _request tiene parámetro retry_auth")
    import inspect
    sig = inspect.signature(client._request)
    params = list(sig.parameters.keys())
    tiene_retry = 'retry_auth' in params
    symbol = "✅" if tiene_retry else "❌"
    print(f"   {symbol} Parámetro retry_auth: {'existe' if tiene_retry else 'NO EXISTE'}")
    print(f"   Parámetros de _request: {params}")
    
    print("\n" + "=" * 60)
    print("FIN DE TESTS")
    print("=" * 60)


async def test_login_and_refresh():
    """Test de login y refresh (requiere backend corriendo)"""
    
    print("\n" + "=" * 60)
    print("TEST DE LOGIN Y AUTO-REFRESH")
    print("=" * 60)
    print("⚠️ Este test requiere backend corriendo en http://localhost:8000")
    
    respuesta = input("\n¿Está el backend corriendo? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Test cancelado. Levanta el backend y vuelve a intentar.")
        return
    
    client = APIClient()
    
    # Test 1: Login
    print("\n🧪 Test 1: Login con admin/Admin123")
    try:
        response = await client.login("admin", "Admin123")
        print("   ✅ Login exitoso")
        print(f"   Token: {client.token[:50]}..." if client.token else "   ❌ No hay token")
        print(f"   Refresh token: {client.refresh_token[:50]}..." if client.refresh_token else "   ❌ No hay refresh")
        
    except AuthenticationError as e:
        print(f"   ❌ Credenciales inválidas: {e}")
        print("   Verifica usuario/password o crea admin con: python backend/scripts/create_admin.py")
        return
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return
    
    # Test 2: Hacer una petición normal
    print("\n🧪 Test 2: Obtener lista de socios (con token válido)")
    try:
        response = await client.get_miembros(page=1, page_size=5)
        total = response.get("pagination", {}).get("total", 0)
        print(f"   ✅ Petición exitosa: {total} socios en total")
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
    
    # Test 3: Simular token expirado y probar refresh
    print("\n🧪 Test 3: Simular token expirado y probar auto-refresh")
    print("   Guardando token original...")
    token_original = client.token
    
    # Simular token expirado (token inválido)
    print("   Invalidando token actual...")
    client.token = "token_invalido_para_test"
    
    print("   Intentando petición (debería auto-renovar)...")
    try:
        response = await client.get_miembros(page=1, page_size=5)
        print("   ✅ Auto-refresh funcionó! Petición exitosa después de renovar token")
        print(f"   Token renovado: {client.token[:50]}...")
        
    except AuthenticationError as e:
        print(f"   ❌ No pudo renovar token: {e}")
        print("   Verifica que refresh_access_token() esté implementado correctamente")
        
    except Exception as e:
        print(f"   ⚠️ Error inesperado: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("FIN DE TESTS DE LOGIN/REFRESH")
    print("=" * 60)


async def main():
    """Ejecutar todos los tests"""
    
    print("\n🚀 INICIANDO TESTS DE API CLIENT V2.0")
    print("=" * 60)
    
    # Tests básicos (no requieren backend)
    await test_exceptions()
    
    # Tests de integración (requieren backend)
    print("\n")
    respuesta = input("¿Quieres ejecutar tests de login/refresh? (requiere backend) (s/n): ")
    if respuesta.lower() == 's':
        await test_login_and_refresh()
    
    print("\n✅ Todos los tests completados")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrumpidos por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
