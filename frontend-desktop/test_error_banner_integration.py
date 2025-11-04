"""
Test de integración del ErrorBanner en socios_view.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TEST: Validación de integración ErrorBanner")
print("=" * 60)

# 1. Test import de ErrorBanner
print("\n1. Verificando imports...")
try:
    from src.components.error_banner import ErrorBanner, SuccessBanner
    print("   ✅ ErrorBanner y SuccessBanner importados correctamente")
except ImportError as e:
    print(f"   ❌ Error al importar ErrorBanner: {e}")
    sys.exit(1)

# 2. Test import de handle_api_error_with_banner
print("\n2. Verificando error_handler...")
try:
    from src.utils.error_handler import handle_api_error_with_banner
    print("   ✅ handle_api_error_with_banner importado correctamente")
except ImportError as e:
    print(f"   ❌ Error al importar handle_api_error_with_banner: {e}")
    sys.exit(1)

# 3. Test import de socios_view
print("\n3. Verificando socios_view.py...")
try:
    # Importar flet primero (dummy page si no está disponible)
    import flet as ft
    from src.views.socios_view import SociosView
    print("   ✅ SociosView importado correctamente")
    print("   ✅ Imports en socios_view.py validados")
except ImportError as e:
    print(f"   ❌ Error al importar SociosView: {e}")
    sys.exit(1)

# 4. Test creación de instancias
print("\n4. Verificando creación de instancias...")
try:
    error_banner = ErrorBanner()
    success_banner = SuccessBanner()
    print("   ✅ ErrorBanner instanciado correctamente")
    print("   ✅ SuccessBanner instanciado correctamente")
except Exception as e:
    print(f"   ❌ Error al crear instancias: {e}")
    sys.exit(1)

# 5. Test métodos del ErrorBanner
print("\n5. Verificando métodos de ErrorBanner...")
try:
    # Verificar que los métodos existen
    assert hasattr(error_banner, 'show_error'), "Falta método show_error"
    assert hasattr(error_banner, 'show_errors'), "Falta método show_errors"
    assert hasattr(error_banner, 'show_validation_errors'), "Falta método show_validation_errors"
    assert hasattr(error_banner, 'hide'), "Falta método hide"
    assert hasattr(success_banner, 'show'), "Falta método show en SuccessBanner"
    assert hasattr(success_banner, 'hide'), "Falta método hide en SuccessBanner"
    print("   ✅ Todos los métodos necesarios están presentes")
except AssertionError as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# 6. Test de uso de handle_api_error_with_banner
print("\n6. Verificando handle_api_error_with_banner...")
try:
    from src.services.api_client import ValidationError
    
    # Simular error de validación
    test_error = ValidationError(
        message="Errores de validación",
        details={
            "email": ["Email inválido"],
            "telefono": ["Formato incorrecto"]
        }
    )
    
    # Llamar al handler (sin page, solo para verificar que no explota)
    result = handle_api_error_with_banner(test_error, error_banner, "test")
    assert result == True, "handle_api_error_with_banner debe retornar True"
    print("   ✅ handle_api_error_with_banner funciona correctamente")
    
except Exception as e:
    print(f"   ❌ Error en handle_api_error_with_banner: {e}")
    sys.exit(1)

# 7. Verificar que show_nuevo_socio_dialog está modificado
print("\n7. Verificando modificaciones en show_nuevo_socio_dialog...")
try:
    import inspect
    source = inspect.getsource(SociosView.show_nuevo_socio_dialog)
    
    checks = [
        ("error_banner = ErrorBanner()", "Creación de error_banner"),
        ("success_banner = SuccessBanner()", "Creación de success_banner"),
        ("handle_api_error_with_banner", "Uso de handle_api_error_with_banner"),
        ("error_banner.hide()", "Limpieza de banners"),
        ("error_banner.show_error", "Mostrar errores en banner")
    ]
    
    all_ok = True
    for check_str, description in checks:
        if check_str in source:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ Falta: {description}")
            all_ok = False
    
    if not all_ok:
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error al verificar código fuente: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODOS LOS TESTS PASARON")
print("=" * 60)
print("\nEl ErrorBanner está correctamente integrado en socios_view.py")
print("\nPróximos pasos:")
print("  1. Ejecutar la app: python -m src.main")
print("  2. Ir a vista de Socios")
print("  3. Click en 'Nuevo Socio'")
print("  4. Ingresar email inválido (ej: 'invalid')")
print("  5. Verificar que aparece banner naranja con errores en el modal")
print("  6. Verificar que el modal NO se cierra")
print("  7. Corregir el email y guardar")
print("  8. Verificar que se cierra el modal y aparece mensaje de éxito")
