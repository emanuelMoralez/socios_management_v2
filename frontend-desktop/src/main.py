"""
Sistema de Gestión de Socios - Frontend Desktop
frontend-desktop/src/main.py
"""
import flet as ft
from src.views.login_view import LoginView
from src.views.main_layout import MainLayout
from src.services.api_client import api_client
from src.utils.notification_manager import NotificationManager


class App:
    """Aplicación principal"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        self.notification_manager = None
        
        # Configuración de la página
        self.page.title = "Sistema de Gestión de Socios"
        self.page.window.width = 1280
        self.page.window.height = 800
        self.page.window.min_width = 1024
        self.page.window.min_height = 768
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # Tema personalizado
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
        )
        
        # Inicializar gestor de notificaciones
        self.notification_manager = NotificationManager(page)
        
        # Iniciar con login
        self.show_login()
    
    def show_login(self):
        """Mostrar pantalla de login"""
        self.page.clean()
        login_view = LoginView(self.on_login_success)
        self.page.add(login_view)
        self.page.update()
    
    def on_login_success(self, user_data: dict):
        """Callback cuando login es exitoso"""
        self.current_user = user_data
        self.show_main_layout()
    
    def show_main_layout(self):
        """Mostrar layout principal con sidebar"""
        self.page.clean()
        
        # Configurar AppBar con notificaciones
        notification_badge = self.notification_manager.create_notification_badge()
        self.page.appbar = ft.AppBar(
            title=ft.Text("Sistema de Gestión de Socios"),
            center_title=False,
            bgcolor=ft.Colors.BLUE,
            actions=[notification_badge]
        )
        
        main_layout = MainLayout(
            page=self.page,
            user=self.current_user,
            on_logout=self.on_logout,
            initial_view="dashboard"
        )
        self.page.add(main_layout)
        self.page.update()
        
        # Cargar vista inicial
        main_layout.load_view("dashboard")
        
        # Iniciar sistema de notificaciones en background
        self.page.run_task(self.start_notifications)
    
    def on_logout(self):
        """Callback cuando usuario cierra sesión"""
        # Detener notificaciones
        if self.notification_manager:
            self.notification_manager.stop_background_check()
        
        api_client.logout()
        self.current_user = None
        
        # Limpiar AppBar
        self.page.appbar = None
        
        self.show_login()
    
    async def start_notifications(self):
        """Iniciar sistema de notificaciones"""
        try:
            # Función para chequear morosos
            async def check_morosos():
                try:
                    data = await api_client.get_reporte_morosidad()
                    morosos = data.get("morosos", [])
                    return len(morosos)
                except Exception as e:
                    print(f"Error al obtener reporte de morosidad: {e}")
                    return 0
            
            # Agregar notificación de bienvenida
            self.notification_manager.add_notification(
                titulo="✅ Bienvenido",
                mensaje=f"Sesión iniciada como {self.current_user.get('username', 'usuario')}",
                tipo="success"
            )
            
            # Iniciar chequeo en background de morosos (cada 5 minutos)
            await self.notification_manager.start_background_check(check_morosos)
            
        except Exception as e:
            print(f"Error al iniciar notificaciones: {e}")


def main(page: ft.Page):
    """Función principal de Flet"""
    App(page)


if __name__ == "__main__":
    ft.app(target=main)