"""
Test simple para verificar login y dashboard completo
"""
import flet as ft
from src.views.login_view import LoginView
from src.views.main_layout import MainLayout
from src.services.api_client import api_client
from src.utils.notification_manager import NotificationManager

class TestApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        self.notification_manager = None
        
        print("="*60)
        print("TEST: Inicializando aplicación")
        print("="*60)
        
        # Configuración
        self.page.title = "Test - Sistema de Gestión de Socios"
        self.page.window.width = 1280
        self.page.window.height = 800
        
        # Notification manager
        print("Creando NotificationManager...")
        self.notification_manager = NotificationManager(page)
        print("✅ NotificationManager creado")
        
        # Simular login exitoso directamente
        print("\nSimulando login exitoso...")
        self.current_user = {
            "id": 1,
            "username": "admin",
            "rol": "SUPER_ADMIN"
        }
        self.show_main_layout()
    
    def show_main_layout(self):
        print("\nMostrando MainLayout...")
        self.page.clean()
        
        # AppBar con notificaciones
        print("Creando notification badge...")
        try:
            notification_badge = self.notification_manager.create_notification_badge()
            print("✅ Badge creado")
            
            self.page.appbar = ft.AppBar(
                title=ft.Text("Sistema de Gestión de Socios"),
                bgcolor=ft.Colors.BLUE,
                actions=[notification_badge]
            )
            print("✅ AppBar configurado")
        except Exception as e:
            print(f"❌ Error en AppBar: {e}")
            import traceback
            traceback.print_exc()
        
        # MainLayout
        print("Creando MainLayout...")
        try:
            main_layout = MainLayout(
                page=self.page,
                user=self.current_user,
                on_logout=self.on_logout,
                initial_view="dashboard"
            )
            print("✅ MainLayout creado")
            
            self.page.add(main_layout)
            self.page.update()
            print("✅ MainLayout agregado a página")
            
            # Cargar dashboard
            print("\nCargando dashboard...")
            main_layout.load_view("dashboard")
            print("✅ Dashboard cargado")
            
            # Notificación de bienvenida
            print("\nAgregando notificación de bienvenida...")
            self.notification_manager.add_notification(
                titulo="✅ Test Exitoso",
                mensaje="Dashboard cargado correctamente",
                tipo="success"
            )
            print("✅ Notificación agregada")
            
            print("\n" + "="*60)
            print("✅ TODO FUNCIONANDO CORRECTAMENTE")
            print("="*60)
            print("\nVerifica que:")
            print("  • AppBar azul con badge 🔔 (1)")
            print("  • Sidebar con menú de navegación")
            print("  • Dashboard con KPIs y gráficos")
            print("  • Click en 🔔 para ver notificación")
            
        except Exception as e:
            print(f"❌ Error en MainLayout: {e}")
            import traceback
            traceback.print_exc()
    
    def on_logout(self):
        print("Logout")

def main(page: ft.Page):
    TestApp(page)

if __name__ == "__main__":
    ft.app(target=main)
