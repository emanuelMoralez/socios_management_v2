#!/usr/bin/env python3
"""
Script de debug para probar creación de socio
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.api_client import api_client


async def test_crear_socio():
    """Probar creación de socio con datos válidos"""
    
    print("=" * 60)
    print("TEST: CREAR SOCIO CON DATOS VÁLIDOS")
    print("=" * 60)
    
    # Login primero
    print("\n1. Haciendo login...")
    try:
        response = await api_client.login("admin", "Admin123")
        print(f"   ✅ Login exitoso")
        print(f"   Token: {api_client.token[:50]}...")
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return
    
    # Obtener categorías
    print("\n2. Obteniendo categorías...")
    try:
        categorias = await api_client.get_categorias()
        if categorias:
            print(f"   ✅ {len(categorias)} categorías disponibles")
            primera_cat = categorias[0]
            print(f"   Primera categoría: ID={primera_cat.get('id')}, Nombre={primera_cat.get('nombre')}")
            categoria_id = primera_cat.get('id')
        else:
            print("   ⚠️ No hay categorías. Crea una primero.")
            return
    except Exception as e:
        print(f"   ❌ Error obteniendo categorías: {e}")
        return
    
    # Crear socio con datos VÁLIDOS
    print("\n3. Creando socio con datos válidos...")
    import random
    doc_numero = str(random.randint(10000000, 99999999))
    data = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "numero_documento": doc_numero,
        "tipo_documento": "dni",
        "email": "juan.perez@example.com",  # Email VÁLIDO
        "telefono": "1234567890",
        "celular": "9876543210",
        "direccion": "Calle Falsa 123",
        "localidad": "Springfield",
        "provincia": "Buenos Aires",
        "cod_postal": "1234",
        "categoria_id": categoria_id,
        "modulo_tipo": "generico"
    }
    
    print(f"   Datos a enviar:")
    for key, value in data.items():
        print(f"     - {key}: {value}")
    
    try:
        resultado = await api_client.create_miembro(data)
        print(f"\n   ✅ SOCIO CREADO EXITOSAMENTE!")
        print(f"   ID: {resultado.get('id')}")
        print(f"   Número de socio: {resultado.get('numero_miembro')}")
        print(f"   Nombre completo: {resultado.get('nombre')} {resultado.get('apellido')}")
        
    except Exception as e:
        print(f"\n   ❌ ERROR AL CREAR SOCIO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        
        if hasattr(e, 'details'):
            print(f"   Detalles: {e.details}")
        
        import traceback
        print("\n   Traceback completo:")
        traceback.print_exc()
    
    # Verificar que se creó
    print("\n4. Verificando lista de socios...")
    try:
        response = await api_client.get_miembros(page=1, page_size=5)
        total = response.get("pagination", {}).get("total", 0)
        print(f"   ✅ Total de socios: {total}")
        
        items = response.get("items", [])
        if items:
            print(f"   Últimos 5 socios:")
            for socio in items[:5]:
                print(f"     - {socio.get('numero_miembro')}: {socio.get('nombre')} {socio.get('apellido')}")
    except Exception as e:
        print(f"   ❌ Error listando socios: {e}")
    
    print("\n" + "=" * 60)
    print("FIN DEL TEST")
    print("=" * 60)


async def test_crear_socio_email_invalido():
    """Probar creación con email inválido"""
    
    print("\n" + "=" * 60)
    print("TEST: CREAR SOCIO CON EMAIL INVÁLIDO")
    print("=" * 60)
    
    # Login primero
    print("\n1. Haciendo login...")
    try:
        await api_client.login("admin", "Admin123")
        print(f"   ✅ Login exitoso")
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return
    
    # Obtener categorías
    print("\n2. Obteniendo categorías...")
    try:
        categorias = await api_client.get_categorias()
        categoria_id = categorias[0].get('id') if categorias else None
        if not categoria_id:
            print("   ⚠️ No hay categorías")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Crear socio con EMAIL INVÁLIDO
    print("\n3. Creando socio con email inválido...")
    data = {
        "nombre": "Test",
        "apellido": "Usuario",
        "numero_documento": "87654321",
        "tipo_documento": "dni",
        "email": "test@",  # EMAIL INVÁLIDO
        "categoria_id": categoria_id,
        "modulo_tipo": "generico"
    }
    
    try:
        resultado = await api_client.create_miembro(data)
        print(f"   ❌ ERROR: Debería haber fallado pero se creó: {resultado}")
        
    except Exception as e:
        print(f"   ✅ CORRECTO: Se capturó la excepción")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        
        if hasattr(e, 'details'):
            print(f"   Detalles disponibles: Sí")
            details = e.details
            
            # Intentar extraer como lo hace error_handler
            if isinstance(details, dict):
                if "errors" in details and isinstance(details["errors"], list):
                    print(f"   Errores encontrados:")
                    for err in details["errors"]:
                        if isinstance(err, dict):
                            field = err.get("field", "campo")
                            message = err.get("message", "inválido")
                            print(f"     • {field}: {message}")
        else:
            print(f"   Detalles disponibles: No")
    
    print("\n" + "=" * 60)


async def main():
    print("\n🔍 DEBUG: CREACIÓN DE SOCIOS")
    
    # Test 1: Crear con datos válidos
    await test_crear_socio()
    
    # Test 2: Crear con email inválido
    respuesta = input("\n¿Probar con email inválido también? (s/n): ")
    if respuesta.lower() == 's':
        await test_crear_socio_email_invalido()
    
    print("\n✅ Tests completados")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
