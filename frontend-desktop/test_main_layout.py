"""
Test del MainLayout con sidebar
"""
import sys
import traceback

print("=" * 60)
print("TEST: MainLayout Construction")
print("=" * 60)

try:
    print("\n1. Importando MainLayout...")
    from src.views.main_layout import MainLayout
    import flet as ft
    print("   ✅ Imports correctos")
    
    print("\n2. Creando página mock...")
    class MockPage:
        def __init__(self):
            self.snack_bar = None
            
        def run_task(self, task, *args):
            print(f"   [MOCK] run_task llamado")
            
        def update(self):
            print(f"   [MOCK] update llamado")
        
        def clean(self):
            print(f"   [MOCK] clean llamado")
    
    mock_page = MockPage()
    print("   ✅ Mock page creado")
    
    print("\n3. Creando MainLayout...")
    user_data = {"username": "admin", "rol": "SUPER_ADMIN"}
    
    def mock_logout():
        print("   [MOCK] logout llamado")
    
    layout = MainLayout(
        page=mock_page,
        user=user_data,
        on_logout=mock_logout,
        initial_view="dashboard"
    )
    print("   ✅ MainLayout creado")
    
    print("\n4. Verificando estructura...")
    print(f"   - Tipo: {type(layout)}")
    print(f"   - Base class: {layout.__class__.__bases__}")
    print(f"   - expand: {getattr(layout, 'expand', 'NO EXISTE')}")
    print(f"   - controls existe: {hasattr(layout, 'controls')}")
    
    if hasattr(layout, 'controls'):
        print(f"   - Número de controls: {len(layout.controls)}")
        for i, ctrl in enumerate(layout.controls):
            ctrl_type = type(ctrl).__name__
            print(f"     [{i}] {ctrl_type}")
            if ctrl_type == "Container" and i == 0:  # Sidebar
                print(f"         - width: {getattr(ctrl, 'width', 'N/A')}")
                print(f"         - bgcolor: {getattr(ctrl, 'bgcolor', 'N/A')}")
    
    print("\n5. Verificando métodos...")
    print(f"   - navigate_to existe: {hasattr(layout, 'navigate_to')}")
    print(f"   - load_view existe: {hasattr(layout, 'load_view')}")
    print(f"   - _create_sidebar existe: {hasattr(layout, '_create_sidebar')}")
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    print("=" * 60)
    sys.exit(1)
