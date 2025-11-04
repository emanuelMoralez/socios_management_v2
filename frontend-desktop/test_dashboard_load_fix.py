"""
Test rápido para verificar que el dashboard se carga correctamente
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_load():
    """Verificar que el dashboard se carga correctamente desde MainLayout"""
    from src.views.main_layout import MainLayout
    import inspect
    
    print("✅ Verificando carga del Dashboard:")
    
    # Verificar método _load_view_async
    load_view_source = inspect.getsource(MainLayout._load_view_async)
    
    # Verificar que después de crear DashboardView se actualiza el contenedor
    if 'self.content_container.content = view' in load_view_source:
        print("  ✓ Actualiza content_container.content")
    else:
        print("  ✗ NO actualiza content_container.content")
        return False
    
    if 'self.content_container.update()' in load_view_source:
        print("  ✓ Llama a content_container.update()")
    else:
        print("  ✗ NO llama a content_container.update()")
        return False
    
    # Verificar que llama a load_dashboard_data() para el dashboard
    if 'view.load_dashboard_data()' in load_view_source:
        print("  ✓ Llama a view.load_dashboard_data() para dashboard")
    else:
        print("  ✗ NO llama a view.load_dashboard_data()")
        return False
    
    # Verificar que DashboardView ya no tiene did_mount()
    from src.views.dashboard_view import DashboardView
    
    if hasattr(DashboardView, 'did_mount'):
        print("  ⚠ DashboardView aún tiene método did_mount() (ya no se usa)")
    else:
        print("  ✓ DashboardView NO tiene did_mount() (correcto)")
    
    # Verificar que tiene load_dashboard_data()
    if hasattr(DashboardView, 'load_dashboard_data'):
        print("  ✓ DashboardView tiene método load_dashboard_data()")
    else:
        print("  ✗ DashboardView NO tiene load_dashboard_data()")
        return False
    
    print("\n" + "="*60)
    print("✅ TODAS LAS VERIFICACIONES PASARON")
    print("="*60)
    print("\n📊 Flujo de carga corregido:")
    print("  1. MainLayout._load_view_async('dashboard')")
    print("  2. Crea DashboardView(page, user, on_logout, navigate_callback)")
    print("  3. Actualiza content_container.content = view")
    print("  4. Llama a content_container.update()")
    print("  5. Llama a view.load_dashboard_data()")
    print("  6. load_dashboard_data() ejecuta _load_dashboard_data() async")
    print("  7. Se cargan los datos del backend y se actualizan los KPIs")
    
    print("\n✅ El dashboard ahora debería mostrarse correctamente")
    
    return True


if __name__ == "__main__":
    try:
        success = test_dashboard_load()
        if success:
            print("\n✅ Test completado exitosamente")
            print("\n🚀 Ahora puedes probar la aplicación:")
            print("   cd frontend-desktop")
            print("   PYTHONPATH=. python src/main.py")
            sys.exit(0)
        else:
            print("\n❌ Test falló")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
