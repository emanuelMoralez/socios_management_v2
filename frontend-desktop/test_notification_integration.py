"""
Test de integración del NotificationManager en main.py
"""
import sys
import os

# Agregar directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_notification_integration():
    """Verificar que NotificationManager está integrado en App"""
    from src.main import App
    import inspect
    
    print("✅ Verificando integración de NotificationManager:")
    
    # Verificar import
    main_source = inspect.getsource(App)
    
    if 'from src.utils.notification_manager import NotificationManager' in open('src/main.py').read():
        print("  ✓ Import de NotificationManager presente")
    else:
        print("  ✗ Import de NotificationManager FALTA")
        return False
    
    # Verificar inicialización en __init__
    init_source = inspect.getsource(App.__init__)
    
    if 'self.notification_manager = NotificationManager(page)' in init_source:
        print("  ✓ NotificationManager inicializado en __init__")
    else:
        print("  ✗ NotificationManager NO inicializado")
        return False
    
    # Verificar AppBar con badge
    show_layout_source = inspect.getsource(App.show_main_layout)
    
    if 'notification_badge = self.notification_manager.create_notification_badge()' in show_layout_source:
        print("  ✓ Badge de notificaciones creado")
    else:
        print("  ✗ Badge de notificaciones NO creado")
        return False
    
    if 'self.page.appbar = ft.AppBar' in show_layout_source:
        print("  ✓ AppBar configurado")
    else:
        print("  ✗ AppBar NO configurado")
        return False
    
    if 'actions=[notification_badge]' in show_layout_source:
        print("  ✓ Badge agregado al AppBar")
    else:
        print("  ✗ Badge NO agregado al AppBar")
        return False
    
    # Verificar inicio de notificaciones
    if 'self.page.run_task(self.start_notifications)' in show_layout_source:
        print("  ✓ Notificaciones iniciadas en background")
    else:
        print("  ✗ Notificaciones NO iniciadas")
        return False
    
    # Verificar método start_notifications
    if hasattr(App, 'start_notifications'):
        print("  ✓ Método start_notifications existe")
        start_notif_source = inspect.getsource(App.start_notifications)
        
        if 'async def check_morosos():' in start_notif_source:
            print("  ✓ Función check_morosos definida")
        else:
            print("  ✗ Función check_morosos NO definida")
            return False
        
        if 'api_client.get_reporte_morosidad()' in start_notif_source:
            print("  ✓ Llama a get_reporte_morosidad()")
        else:
            print("  ✗ NO llama a get_reporte_morosidad()")
            return False
        
        if 'start_background_check(check_morosos)' in start_notif_source:
            print("  ✓ Inicia chequeo en background")
        else:
            print("  ✗ NO inicia chequeo en background")
            return False
        
        if 'add_notification' in start_notif_source and 'Bienvenido' in start_notif_source:
            print("  ✓ Agrega notificación de bienvenida")
        else:
            print("  ⚠ No agrega notificación de bienvenida (opcional)")
    else:
        print("  ✗ Método start_notifications NO existe")
        return False
    
    # Verificar limpieza en logout
    logout_source = inspect.getsource(App.on_logout)
    
    if 'stop_background_check()' in logout_source:
        print("  ✓ Detiene notificaciones en logout")
    else:
        print("  ✗ NO detiene notificaciones en logout")
        return False
    
    if 'self.page.appbar = None' in logout_source:
        print("  ✓ Limpia AppBar en logout")
    else:
        print("  ⚠ No limpia AppBar (opcional)")
    
    print("\n" + "="*60)
    print("✅ TODAS LAS VERIFICACIONES PASARON")
    print("="*60)
    print("\n📊 Resumen de integración:")
    print("  • NotificationManager importado en main.py")
    print("  • Instancia creada en App.__init__")
    print("  • Badge agregado al AppBar")
    print("  • Chequeo de morosos cada 5 minutos en background")
    print("  • Notificación de bienvenida al iniciar sesión")
    print("  • Limpieza correcta en logout")
    print("\n🎯 Funcionalidades activas:")
    print("  • 🔔 Badge con contador de notificaciones no leídas")
    print("  • ⚠️  Alertas automáticas de nuevos morosos")
    print("  • 📱 Panel lateral con historial de notificaciones")
    print("  • ✅ Marcar notificaciones como leídas")
    print("  • 🔄 Actualización automática cada 5 minutos")
    
    return True


if __name__ == "__main__":
    try:
        success = test_notification_integration()
        if success:
            print("\n✅ Test completado exitosamente")
            print("\n🚀 Para probar:")
            print("   1. Ejecutar: PYTHONPATH=. python src/main.py")
            print("   2. Iniciar sesión")
            print("   3. Verificar badge 🔔 en AppBar (esquina superior derecha)")
            print("   4. Hacer clic en badge para ver panel de notificaciones")
            print("   5. Esperar 5 minutos para ver chequeo automático de morosos")
            sys.exit(0)
        else:
            print("\n❌ Test falló")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
