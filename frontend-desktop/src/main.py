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
        self.page.window.width = 1366
        self.page.window.height = 768
        self.page.window.min_width = 1366
        self.page.window.min_height = 768
        self.page.window.max_width = 1366
        self.page.window.max_height = 768
        self.page.window.resizable = False
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # Tema personalizado
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
        )
        
        # Dark theme
        self.page.dark_theme = ft.Theme(
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
        
        # Configurar AppBar moderna con notificaciones y tema
        notification_badge = self.notification_manager.create_notification_badge()
        theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            tooltip="Cambiar tema",
            on_click=self.toggle_theme,
            icon_color=ft.Colors.WHITE
        )
        
        # Usuario info en AppBar
        user_info_appbar = ft.Container(
            content=ft.Row(
            [
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=32, color=ft.Colors.WHITE),
                ft.Column(
                    [
                        ft.Text(
                            self.current_user.get("username", "Usuario"),
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            self.current_user.get("rol", "").replace("_", " ").title(),
                            size=10,
                            color=ft.Colors.WHITE70
                        ),
                    ],
                    spacing=0,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            margin=ft.margin.only(right=10)
        )
        
        # Obtener nombre de la organización desde config del backend
        org_name = self.current_user.get("org_name", "Mi Organización")
        
        self.page.appbar = ft.AppBar(
            title=ft.Text(org_name, size=20, weight=ft.FontWeight.BOLD),
            center_title=False,
            bgcolor=ft.Colors.BLUE_800,
            leading=None,
            actions=[
                user_info_appbar,
                ft.Container(width=1, height=40, bgcolor=ft.Colors.WHITE24),
                theme_button,
                ft.Container(notification_badge, margin=ft.Margin(0, 0, 24, 0))
            ],
            toolbar_height=64
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
    
    def toggle_theme(self, e=None):
        """Cambiar entre tema claro y oscuro"""
        self.page.theme_mode = (
            ft.ThemeMode.DARK 
            if self.page.theme_mode == ft.ThemeMode.LIGHT 
            else ft.ThemeMode.LIGHT
        )
        
        # Actualizar icono del botón
        if self.page.appbar and len(self.page.appbar.actions) > 2:
            theme_button = self.page.appbar.actions[2]  # índice 2: user_info, separator, theme_button
            theme_button.icon = (
                ft.Icons.LIGHT_MODE 
                if self.page.theme_mode == ft.ThemeMode.DARK 
                else ft.Icons.DARK_MODE
            )
        
        self.page.update()
    
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