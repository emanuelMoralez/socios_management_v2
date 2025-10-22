"""
Sistema de Gestión de Socios - Frontend Desktop
frontend-desktop/src/main.py
"""
import flet as ft
from src.views.login_view import LoginView
from src.views.dashboard_view import DashboardView
from src.services.api_client import api_client


class App:
    """Aplicación principal"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        
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
        self.show_dashboard()
    
    def show_dashboard(self):
        """Mostrar dashboard principal"""
        self.page.clean()
        dashboard = DashboardView(
            page=self.page,
            user=self.current_user,
            on_logout=self.on_logout
        )
        self.page.add(dashboard)
        self.page.update()
    
    def on_logout(self):
        """Callback cuando usuario cierra sesión"""
        api_client.logout()
        self.current_user = None
        self.show_login()


def main(page: ft.Page):
    """Función principal de Flet"""
    App(page)


if __name__ == "__main__":
    ft.app(target=main)