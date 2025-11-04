"""
Layout principal con sidebar de navegación
frontend-desktop/src/views/main_layout.py
"""
import flet as ft
from src.services.api_client import api_client


class MainLayout(ft.Row):
    """Layout principal con sidebar y contenido"""
    
    def __init__(self, page: ft.Page, user: dict, on_logout, initial_view="dashboard"):
        super().__init__()
        self.page = page
        self.user = user
        self.on_logout = on_logout
        self.current_view = initial_view
        self.content_container = ft.Container()
        
        # Construir UI
        self.build_ui()
    
    def build_ui(self):
        """Construir interfaz principal"""
        # Sidebar
        sidebar = self._create_sidebar()
        
        # Área de contenido principal
        self.content_container = ft.Container(
            expand=True,
            padding=20,
            bgcolor=ft.Colors.GREY_50
        )
        
        # Ensamblar layout
        self.controls = [
            sidebar,
            self.content_container
        ]
        
        self.spacing = 0
        self.expand = True
    
    def _create_sidebar(self):
        """Crear barra lateral de navegación"""
        # Usuario info
        user_info = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=50, color=ft.Colors.WHITE),
                    ft.Text(
                        self.user.get("username", "Usuario"),
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        self.user.get("rol", ""),
                        size=12,
                        color=ft.Colors.WHITE70
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=20,
            bgcolor=ft.Colors.BLUE_900
        )
        
        # Menú de navegación (valores en minúsculas con guion bajo según el enum del backend)
        menu_items = [
            {
                "key": "dashboard",
                "icon": ft.Icons.DASHBOARD,
                "label": "Dashboard",
                "show_to": ["super_admin", "administrador", "operador", "portero"]
            },
            {
                "key": "socios",
                "icon": ft.Icons.PEOPLE,
                "label": "Socios",
                "show_to": ["super_admin", "administrador", "operador"]
            },
            {
                "key": "cuotas",
                "icon": ft.Icons.ATTACH_MONEY,
                "label": "Pagos",
                "show_to": ["super_admin", "administrador", "operador"]
            },
            {
                "key": "categorias",
                "icon": ft.Icons.CATEGORY,
                "label": "Categorías",
                "show_to": ["super_admin", "administrador"]
            },
            {
                "key": "accesos",
                "icon": ft.Icons.QR_CODE_SCANNER,
                "label": "Accesos",
                "show_to": ["super_admin", "administrador", "operador", "portero"]
            },
            {
                "key": "reportes",
                "icon": ft.Icons.ASSESSMENT,
                "label": "Reportes",
                "show_to": ["super_admin", "administrador"]
            },
            {
                "key": "usuarios",
                "icon": ft.Icons.ADMIN_PANEL_SETTINGS,
                "label": "Usuarios",
                "show_to": ["super_admin", "administrador"]
            },
        ]
        
        # Filtrar menú según rol
        user_rol = self.user.get("rol", "")
        print(f"DEBUG: Usuario rol = {user_rol}")
        menu_buttons = []
        
        for item in menu_items:
            if user_rol in item["show_to"]:
                print(f"DEBUG: Agregando menú: {item['label']}")
                btn = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(item["icon"], color=ft.Colors.WHITE, size=24),
                            ft.Text(item["label"], color=ft.Colors.WHITE, size=14)
                        ],
                        spacing=15
                    ),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_700 if self.current_view == item["key"] else None,
                    border_radius=8,
                    on_click=lambda e, key=item["key"]: self.navigate_to(key),
                    ink=True
                )
                menu_buttons.append(btn)
        
        print(f"DEBUG: Total botones de menú creados: {len(menu_buttons)}")
        
        # Botón de logout
        logout_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.WHITE, size=24),
                    ft.Text("Cerrar Sesión", color=ft.Colors.WHITE, size=14)
                ],
                spacing=15
            ),
            padding=15,
            border_radius=8,
            on_click=lambda e: self.on_logout(),
            ink=True
        )
        
        # Ensamblar sidebar
        sidebar = ft.Container(
            content=ft.Column(
                [
                    user_info,
                    ft.Divider(color=ft.Colors.WHITE24, height=1),
                    ft.Container(
                        content=ft.Column(
                            menu_buttons,
                            spacing=5,
                            scroll=ft.ScrollMode.AUTO
                        ),
                        padding=10,
                        expand=True
                    ),
                    ft.Divider(color=ft.Colors.WHITE24, height=1),
                    ft.Container(content=logout_btn, padding=10)
                ],
                spacing=0,
                expand=True  # ← IMPORTANTE: La columna debe expandirse verticalmente
            ),
            width=200,
            bgcolor=ft.Colors.BLUE_800,
            # NO usar expand aquí - el width fijo se respeta sin expand
        )
        
        print(f"DEBUG: Sidebar creada con {len(menu_buttons)} botones")
        return sidebar
    
    def navigate_to(self, view_key: str):
        """Navegar a una vista específica"""
        if view_key == self.current_view:
            return
        
        self.current_view = view_key
        
        # Actualizar sidebar para resaltar la opción actual
        self.controls[0] = self._create_sidebar()
        
        # Cargar vista correspondiente
        self.load_view(view_key)
        
        self.update()
    
    def load_view(self, view_key: str):
        """Cargar vista en el contenedor principal"""
        # Limpiar contenedor
        self.content_container.content = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(),
                    ft.Text(f"Cargando {view_key}...")
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            expand=True,
            alignment=ft.alignment.center
        )
        self.content_container.update()
        
        # Cargar vista de forma asíncrona
        self.page.run_task(self._load_view_async, view_key)
    
    async def _load_view_async(self, view_key: str):
        """Cargar vista de forma asíncrona"""
        try:
            if view_key == "dashboard":
                from src.views.dashboard_view import DashboardView
                view = DashboardView(
                    self.page, 
                    self.user, 
                    self.on_logout,
                    navigate_callback=self.navigate_to
                )
                # Actualizar contenedor primero
                self.content_container.content = view
                self.content_container.update()
                # Cargar datos del dashboard
                view.load_dashboard_data()
            
            elif view_key == "socios":
                from src.views.socios_view import SociosView
                view = SociosView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            elif view_key == "cuotas":
                from src.views.cuotas_view import CuotasView
                view = CuotasView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            elif view_key == "categorias":
                from src.views.categorias_view import CategoriasView
                view = CategoriasView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            elif view_key == "accesos":
                from src.views.accesos_view import AccesosView
                view = AccesosView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            elif view_key == "reportes":
                from src.views.reportes_view import ReportesView
                view = ReportesView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            elif view_key == "usuarios":
                from src.views.usuarios_view import UsuariosView
                view = UsuariosView(self.page)
                self.content_container.content = view
                self.content_container.update()
            
            else:
                view = ft.Text(f"Vista '{view_key}' no encontrada", size=20)
                self.content_container.content = view
                self.content_container.update()
            
        except Exception as e:
            error_view = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED),
                        ft.Text(f"Error al cargar {view_key}", size=20, color=ft.Colors.RED),
                        ft.Text(str(e), size=14, color=ft.Colors.GREY_700)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                expand=True,
                alignment=ft.alignment.center
            )
            self.content_container.content = error_view
            self.content_container.update()
