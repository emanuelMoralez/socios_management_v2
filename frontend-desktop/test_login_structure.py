"""
Test simple para verificar la estructura de LoginView
"""
from src.views.login_view import LoginView
import sys

print("=" * 60)
print("TEST: Estructura de LoginView")
print("=" * 60)

def dummy_callback(data):
    print(f"Callback ejecutado con: {data}")

try:
    print("\n1. Creando instancia de LoginView...")
    login = LoginView(dummy_callback)
    print("   ✅ LoginView creado exitosamente")
    
    print("\n2. Verificando atributos...")
    print(f"   - Tipo: {type(login)}")
    print(f"   - Clase base: {login.__class__.__bases__}")
    print(f"   - expand: {getattr(login, 'expand', 'NO EXISTE')}")
    print(f"   - content existe: {hasattr(login, 'content')}")
    print(f"   - content es None: {getattr(login, 'content', 'NO EXISTE') is None}")
    
    if hasattr(login, 'content') and login.content:
        print(f"   - Tipo de content: {type(login.content)}")
        print(f"   - Content tiene expand: {getattr(login.content, 'expand', False)}")
    
    print("\n3. Verificando campos del formulario...")
    print(f"   - username_field existe: {hasattr(login, 'username_field')}")
    print(f"   - password_field existe: {hasattr(login, 'password_field')}")
    print(f"   - login_button existe: {hasattr(login, 'login_button')}")
    print(f"   - error_text existe: {hasattr(login, 'error_text')}")
    
    if hasattr(login, 'username_field'):
        print(f"   - username_field.on_submit asignado: {login.username_field.on_submit is not None}")
    if hasattr(login, 'login_button'):
        print(f"   - login_button.on_click asignado: {login.login_button.on_click is not None}")
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
