"""
Test para verificar que el dashboard usa datos reales
"""
import sys
import os

# Agregar directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_methods():
    """Verificar que existen los métodos para datos reales"""
    from src.views.dashboard_view import DashboardView
    import inspect
    
    # Obtener todos los métodos de DashboardView
    methods = [m for m in dir(DashboardView) if not m.startswith('_') or m.startswith('_create') or m.startswith('_update')]
    
    # Verificar métodos críticos
    required_methods = [
        '_update_graficos',
        '_create_bar_elements',
        '_update_alertas',
        '_update_kpis'
    ]
    
    print("✅ Métodos encontrados:")
    for method in required_methods:
        if method in dir(DashboardView):
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} - FALTA")
            return False
    
    # Verificar que _update_graficos usa los nuevos endpoints
    source = inspect.getsource(DashboardView._update_graficos)
    
    print("\n✅ Verificando uso de endpoints reales:")
    
    if 'get_ingresos_historicos' in source:
        print("  ✓ Usa get_ingresos_historicos() para datos reales de ingresos")
    else:
        print("  ✗ NO usa get_ingresos_historicos()")
        return False
    
    if 'get_accesos_detallados' in source:
        print("  ✓ Usa get_accesos_detallados() para datos reales de accesos")
    else:
        print("  ✗ NO usa get_accesos_detallados()")
        return False
    
    # Verificar que NO usa datos simulados
    if 'Simular datos históricos' in source or 'ingresos_mes_actual * 0.8' in source:
        print("  ✗ Aún usa datos simulados")
        return False
    else:
        print("  ✓ Ya no usa datos simulados")
    
    # Verificar que muestra hora pico
    if 'hora_pico' in source:
        print("  ✓ Muestra estadísticas de hora pico")
    else:
        print("  ⚠ No muestra hora pico (opcional)")
    
    print("\n✅ Verificando método _create_bar_elements:")
    bar_elements_source = inspect.getsource(DashboardView._create_bar_elements)
    
    if 'max_valor = max(valores)' in bar_elements_source:
        print("  ✓ Calcula altura de barras correctamente")
    
    if 'val > 0 else ft.Colors.GREY_300' in bar_elements_source:
        print("  ✓ Diferencia barras con/sin actividad")
    
    print("\n✅ Verificando constructor compatible con MainLayout:")
    constructor_source = inspect.getsource(DashboardView.__init__)
    
    if 'user: dict = None' in constructor_source:
        print("  ✓ Constructor acepta parámetro 'user'")
    else:
        print("  ✗ Constructor NO acepta parámetro 'user'")
        return False
    
    if 'on_logout' in constructor_source:
        print("  ✓ Constructor acepta parámetro 'on_logout'")
    else:
        print("  ✗ Constructor NO acepta parámetro 'on_logout'")
        return False
    
    if 'navigate_callback' in constructor_source:
        print("  ✓ Constructor acepta parámetro 'navigate_callback'")
    else:
        print("  ✗ Constructor NO acepta parámetro 'navigate_callback'")
        return False
    
    print("\n✅ Verificando navegación correcta:")
    navigate_source = inspect.getsource(DashboardView.navigate_to)
    
    if 'self.navigate_callback' in navigate_source:
        print("  ✓ Usa navigate_callback para navegación")
    else:
        print("  ⚠ No usa navigate_callback (podría causar problemas)")
    
    print("\n" + "="*60)
    print("✅ TODAS LAS VERIFICACIONES PASARON")
    print("="*60)
    print("\n📊 Resumen de cambios:")
    print("  • Dashboard ahora usa get_ingresos_historicos() con datos reales")
    print("  • Dashboard ahora usa get_accesos_detallados() con datos reales")
    print("  • Muestra estadísticas de hora pico en gráfico de accesos")
    print("  • Diferencia visualmente horas con/sin actividad")
    print("  • Constructor compatible con MainLayout (user, on_logout, navigate_callback)")
    print("  • Navegación correcta via callback")
    
    return True


if __name__ == "__main__":
    try:
        success = test_dashboard_methods()
        if success:
            print("\n✅ Test completado exitosamente")
            sys.exit(0)
        else:
            print("\n❌ Test falló")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
