"""
Vista de Login
frontend-desktop/src/views/login_view.py
"""
import flet as ft
from src.services.api_client import api_client


class LoginView(ft.Container):
    """Pantalla de login"""
    
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.page = None  # Se establecerá cuando se agregue a la página
        
        # Campos de formulario
        self.username_field = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON,
            hint_text="Ingresa tu usuario",
            autofocus=True,
        )
        
        self.password_field = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            hint_text="Ingresa tu contraseña",
        )
        
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=14,
            visible=False
        )
        
        self.login_button = ft.ElevatedButton(
            "Iniciar Sesión",
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
            )
        )
        
        self.loading_indicator = ft.ProgressRing(visible=False)
        
        # Contenedor del formulario
        self.content = ft.Container(
            content=ft.Column(
                [
                    # Logo/Icono
                    ft.Icon(
                        ft.Icons.SPORTS_SOCCER,
                        size=100,
                        color=ft.Colors.BLUE
                    ),
                    
                    # Título
                    ft.Text(
                        "Sistema de Gestión",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900
                    ),
                    ft.Text(
                        "Clubes y Cooperativas",
                        size=18,
                        color=ft.Colors.GREY_700
                    ),
                    
                    ft.Divider(height=30, color="transparent"),
                    
                    # Formulario
                    ft.Container(
                        content=ft.Column(
                            [
                                self.username_field,
                                self.password_field,
                                self.error_text,
                                ft.Row(
                                    [
                                        self.login_button,
                                        self.loading_indicator
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            spacing=20,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                        ),
                        width=400,
                        padding=30,
                        border_radius=10,
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=ft.Colors.BLUE_GREY_100,
                        )
                    ),
                    
                    ft.Divider(height=20, color="transparent"),
                    
                    # Usuarios de prueba
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Usuarios de prueba:",
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Text(
                                    "admin / Admin123!",
                                    size=11,
                                    color=ft.Colors.GREY_600
                                ),
                                ft.Text(
                                    "operador1 / Operador123!",
                                    size=11,
                                    color=ft.Colors.GREY_600
                                ),
                            ],
                            spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=10,
                        border_radius=5,
                        bgcolor=ft.Colors.GREY_100
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            alignment=ft.alignment.center,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.Colors.BLUE_50, ft.Colors.BLUE_100]
            )
        )
        
        self.expand = True
    
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        self.page = self.page or self.content.page
        # Conectar eventos después de montar
        self.username_field.on_submit = lambda _: self.page.run_task(self.handle_login)
        self.password_field.on_submit = lambda _: self.page.run_task(self.handle_login)
        self.login_button.on_click = lambda _: self.page.run_task(self.handle_login)
        self.update()
    
    def show_error(self, message: str):
        """Mostrar mensaje de error"""
        self.error_text.value = message
        self.error_text.visible = True
        if self.page:
            self.update()
    
    def hide_error(self):
        """Ocultar mensaje de error"""
        self.error_text.visible = False
        if self.page:
            self.update()
    
    def set_loading(self, loading: bool):
        """Mostrar/ocultar loading"""
        self.loading_indicator.visible = loading
        self.login_button.disabled = loading
        self.username_field.disabled = loading
        self.password_field.disabled = loading
        if self.page:
            self.update()
    
    async def handle_login(self):
        """Manejar intento de login"""
        username = self.username_field.value
        password = self.password_field.value
        
        # Validar campos
        if not username or not password:
            self.show_error("Por favor completa todos los campos")
            return
        
        self.hide_error()
        self.set_loading(True)
        
        try:
            # Llamar a la API
            response = await api_client.login(username, password)
            
            # Login exitoso
            user_data = response.get("user", {})
            user_data["access_token"] = response.get("access_token")
            
            # Callback de éxito
            self.on_login_success(user_data)
            
        except Exception as e:
            error_message = str(e)
            if "401" in error_message or "Unauthorized" in error_message:
                self.show_error("Usuario o contraseña incorrectos")
            elif "Connection" in error_message:
                self.show_error("Error de conexión con el servidor")
            else:
                self.show_error(f"Error: {error_message}")
        
        finally:
            self.set_loading(False)