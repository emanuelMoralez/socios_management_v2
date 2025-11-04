"""
Vista Dashboard Principal - ACTUALIZADO
frontend-desktop/src/views/dashboard_view.py
"""
import flet as ft
from src.views.socios_view import SociosView
from src.views.cuotas_view import CuotasView
from src.views.accesos_qr_view import AccesosQRView
from src.views.accesos_view import AccesosView
from src.views.reportes_view import ReportesView
from src.views.usuarios_view import UsuariosView
from src.views.categorias_view import CategoriasView


class DashboardView(ft.Container):
    """Dashboard principal con navegación"""
    
    def __init__(self, page: ft.Page, user: dict, on_logout):
        super().__init__()
        self.page = page
        self.user = user
        self.on_logout = on_logout
        
        # Vista actual
        self.current_view = "socios"
        
        # Contenedor de contenido
        self.content_container = ft.Container(
            expand=True,
            padding=20
        )
        
        # Crear interfaz
        self.build_ui()
    
    def build_ui(self):
        """Construir la interfaz"""
        
        # Verificar si el usuario es admin
        is_admin = self.user.get("rol") in ["super_admin", "administrador"]
        
        # NavigationRail (menú lateral)
        destinations = [
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Socios"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PAYMENT_OUTLINED,
                selected_icon=ft.Icons.PAYMENT,
                label="Cuotas"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.QR_CODE_SCANNER_OUTLINED,
                selected_icon=ft.Icons.QR_CODE_SCANNER,
                label="Escáner QR"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DOOR_FRONT_DOOR_OUTLINED,
                selected_icon=ft.Icons.DOOR_FRONT_DOOR,
                label="Historial"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BAR_CHART_OUTLINED,
                selected_icon=ft.Icons.BAR_CHART,
                label="Reportes"
            ),
        ]
        
        # Agregar opciones de admin
        if is_admin:
            destinations.extend([
                ft.NavigationRailDestination(
                    icon=ft.Icons.CATEGORY_OUTLINED,
                    selected_icon=ft.Icons.CATEGORY,
                    label="Categorías"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                    label="Usuarios"
                ),
            ])
        
        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=destinations,
            on_change=self.on_nav_change,
        )
        
        # AppBar superior (header)
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Sistema de Gestión de Socios",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Container(expand=True),  # Spacer
                    # Badge de rol
                    ft.Container(
                        content=ft.Text(
                            self.user.get("rol", "").replace("_", " ").upper(),
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                        padding=8,
                        border_radius=5
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.ACCOUNT_CIRCLE,
                        icon_color=ft.Colors.WHITE,
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            self.user.get("nombre_completo", "Usuario"),
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Text(
                                            self.user.get("email", ""),
                                            size=11,
                                            color=ft.Colors.GREY_600
                                        )
                                    ],
                                    spacing=2
                                ),
                                disabled=True
                            ),
                            ft.PopupMenuItem(),  # Divider
                            ft.PopupMenuItem(
                                text="Cerrar Sesión",
                                icon=ft.Icons.LOGOUT,
                                on_click=lambda _: self.on_logout()
                            )
                        ]
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ft.Colors.BLUE,
            padding=15,
            height=60
        )
        
        # Layout principal
        self.content = ft.Column(
            [
                header,
                ft.Row(
                    [
                        nav_rail,
                        ft.VerticalDivider(width=1),
                        self.content_container
                    ],
                    expand=True,
                    spacing=0
                )
            ],
            spacing=0,
            expand=True
        )
        
        self.expand = True
        self.padding = 0
        
        # Cargar vista inicial
        self.load_view("socios")
    
    def on_nav_change(self, e):
        """Cambiar de vista según navegación"""
        # Verificar si es admin
        is_admin = self.user.get("rol") in ["super_admin", "administrador"]
        
        # Mapeo de vistas
        if is_admin:
            views = ["socios", "cuotas", "escaner_qr", "historial_accesos", "reportes", "categorias", "usuarios"]
        else:
            views = ["socios", "cuotas", "escaner_qr", "historial_accesos", "reportes"]
        
        selected = e.control.selected_index
        
        if selected < len(views):
            self.load_view(views[selected])
    
    def load_view(self, view_name: str):
        """Cargar una vista específica"""
        self.current_view = view_name
        
        # Limpiar contenedor
        self.content_container.content = None
        
        # Cargar vista correspondiente
        if view_name == "socios":
            self.content_container.content = SociosView(self.page)
        elif view_name == "cuotas":
            self.content_container.content = CuotasView(self.page)
        elif view_name == "escaner_qr":
            self.content_container.content = AccesosQRView(self.page)
        elif view_name == "historial_accesos":
            self.content_container.content = AccesosView(self.page)
        elif view_name == "reportes":
            self.content_container.content = ReportesView(self.page)
        elif view_name == "categorias":
            self.content_container.content = CategoriasView(self.page)
        elif view_name == "usuarios":
            self.content_container.content = UsuariosView(self.page)
        
        # Actualizar página
        if self.page:
            self.page.update()