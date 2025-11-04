"""
Test para verificar que DashboardView se construye correctamente
"""
import sys
import traceback

print("=" * 60)
print("TEST: DashboardView Construction")
print("=" * 60)

try:
    print("\n1. Importando DashboardView...")
    from src.views.dashboard_view import DashboardView
    import flet as ft
    print("   ✅ Imports correctos")
    
    print("\n2. Creando página mock...")
    # Crear una página mock
    class MockPage:
        def __init__(self):
            self.snack_bar = None
            
        def run_task(self, task):
            print(f"   [MOCK] run_task llamado con {task}")
            
        def update(self):
            print(f"   [MOCK] update llamado")
    
    mock_page = MockPage()
    print("   ✅ Mock page creado")
    
    print("\n3. Creando DashboardView...")
    user_data = {"username": "admin", "rol": "SUPER_ADMIN"}
    
    def mock_logout():
        print("   [MOCK] logout llamado")
    
    dashboard = DashboardView(
        page=mock_page,
        user=user_data,
        on_logout=mock_logout
    )
    print("   ✅ DashboardView creado")
    
    print("\n4. Verificando atributos...")
    print(f"   - Tipo: {type(dashboard)}")
    print(f"   - Base class: {dashboard.__class__.__bases__}")
    print(f"   - expand: {getattr(dashboard, 'expand', 'NO EXISTE')}")
    print(f"   - scroll: {getattr(dashboard, 'scroll', 'NO EXISTE')}")
    print(f"   - controls existe: {hasattr(dashboard, 'controls')}")
    print(f"   - controls es lista: {isinstance(getattr(dashboard, 'controls', None), list)}")
    
    if hasattr(dashboard, 'controls'):
        print(f"   - Número de controls: {len(dashboard.controls)}")
        for i, ctrl in enumerate(dashboard.controls):
            print(f"     [{i}] {type(ctrl).__name__}")
    
    print("\n5. Verificando métodos...")
    print(f"   - build_ui existe: {hasattr(dashboard, 'build_ui')}")
    print(f"   - load_dashboard_data existe: {hasattr(dashboard, 'load_dashboard_data')}")
    print(f"   - did_mount existe: {hasattr(dashboard, 'did_mount')}")
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    print("=" * 60)
    sys.exit(1)
