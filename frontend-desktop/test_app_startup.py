"""
Script de diagnóstico para detectar errores en el startup de la app
"""
import sys
import traceback

print("=== DIAGNÓSTICO DE STARTUP ===\n")

# Test 1: Imports básicos
print("1. Testing imports básicos...")
try:
    import flet as ft
    print("   ✅ flet importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando flet: {e}")
    sys.exit(1)

# Test 2: Import de LoginView
print("\n2. Testing LoginView...")
try:
    from src.views.login_view import LoginView
    print("   ✅ LoginView importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando LoginView:")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import de DashboardView
print("\n3. Testing DashboardView...")
try:
    from src.views.dashboard_view import DashboardView
    print("   ✅ DashboardView importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando DashboardView:")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import de api_client
print("\n4. Testing api_client...")
try:
    from src.services.api_client import api_client
    print("   ✅ api_client importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando api_client:")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Import de main
print("\n5. Testing main.py...")
try:
    from src.main import App, main
    print("   ✅ main.py importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando main.py:")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Crear instancia de LoginView
print("\n6. Testing creación de LoginView...")
try:
    def dummy_callback(data):
        pass
    login_view = LoginView(dummy_callback)
    print("   ✅ LoginView instanciado correctamente")
    print(f"   - Tipo: {type(login_view)}")
    print(f"   - Tiene content: {hasattr(login_view, 'content')}")
    print(f"   - Tiene expand: {hasattr(login_view, 'expand')}")
except Exception as e:
    print(f"   ❌ Error creando LoginView:")
    traceback.print_exc()
    sys.exit(1)

print("\n=== ✅ TODOS LOS TESTS PASARON ===")
print("\nAhora probando con ventana real...")

def test_main(page: ft.Page):
    """Test con ventana real"""
    try:
        page.title = "Test Startup"
        page.window.width = 800
        page.window.height = 600
        
        print("\n7. Creando App...")
        app = App(page)
        print("   ✅ App creada correctamente")
        
    except Exception as e:
        print(f"\n❌ ERROR EN APP:")
        traceback.print_exc()
        page.add(ft.Text(f"ERROR: {str(e)}", color=ft.Colors.RED))

print("\nLanzando ventana de prueba...")
ft.app(target=test_main)
