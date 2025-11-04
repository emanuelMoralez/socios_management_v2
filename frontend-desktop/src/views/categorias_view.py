"""
Vista de Gestión de Categorías de Socios
frontend-desktop/src/views/categorias_view.py
"""
import flet as ft
from src.services.api_client import api_client
from src.utils.error_handler import handle_api_error_with_banner, show_success
from src.components.error_banner import ErrorBanner, SuccessBanner


class CategoriasView(ft.Column):
    """Vista de administración de categorías"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.categorias = []
        
        # Tabla de categorías
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Descripción")),
                ft.DataColumn(ft.Text("Cuota Base")),
                ft.DataColumn(ft.Text("Tipo Cuota")),
                ft.DataColumn(ft.Text("Cant. Socios")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Construir UI
        self.build_ui()
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            # Título y botón nuevo
            ft.Row(
                [
                    ft.Text(
                        "Gestión de Categorías",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.ElevatedButton(
                        "Nueva Categoría",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: self.show_nueva_categoria_dialog()
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
            ft.Divider(),
            
            # Info
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE),
                        ft.Text(
                            "Las categorías definen tipos de socios: Titular, Adherente, Cadete, etc.",
                            size=12,
                            color=ft.Colors.GREY_700,
                            expand=True
                        )
                    ],
                    spacing=10
                ),
                bgcolor=ft.Colors.BLUE_50,
                padding=10,
                border_radius=5
            ),
            
            ft.Divider(),
            
            # Botón actualizar
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Actualizar",
                        on_click=lambda _: self.page.run_task(self.load_categorias)
                    )
                ],
                alignment=ft.MainAxisAlignment.END
            ),
            
            # Loading
            self.loading,
            
            # Tabla
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=self.data_table,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=5,
                            padding=10
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                ),
                expand=True
            )
        ]
        
        self.spacing = 10
        self.expand = True
    
    def did_mount(self):
        """Llamado cuando el control se monta"""
        if self.page:
            self.page.run_task(self.load_categorias)
    
    async def load_categorias(self):
        """Cargar lista de categorías"""
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            categorias = await api_client.get_categorias()
            self.update_table(categorias)
            
        except Exception as e:
            self.show_snackbar(f"Error: {e}", error=True)
        
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()
    
    def update_table(self, categorias: list):
        """Actualizar tabla con datos"""
        self.data_table.rows.clear()
        
        for categoria in categorias:
            # Tipo de cuota
            tiene_fija = categoria.get("tiene_cuota_fija", True)
            tipo_cuota = "Fija" if tiene_fija else "Variable"
            tipo_color = ft.Colors.BLUE if tiene_fija else ft.Colors.ORANGE
            
            # Cantidad de socios (si viene del backend)
            cant_socios = categoria.get("cantidad_socios", 0)
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                categoria.get("nombre", ""),
                                weight=ft.FontWeight.BOLD
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                categoria.get("descripcion", "")[:40] + "..." 
                                if len(categoria.get("descripcion", "")) > 40 
                                else categoria.get("descripcion", ""),
                                size=12
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"${categoria.get('cuota_base', 0):,.2f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_700
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    tipo_cuota,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=tipo_color,
                                padding=5,
                                border_radius=5
                            )
                        ),
                        ft.DataCell(
                            ft.Text(str(cant_socios), color=ft.Colors.GREY_700)
                        ),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY,
                                        tooltip="Ver detalles",
                                        on_click=lambda e, c=categoria: self.show_categoria_details(c)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Editar",
                                        on_click=lambda e, c=categoria: self.show_edit_categoria_dialog(c)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar",
                                        icon_color=ft.Colors.RED,
                                        on_click=lambda e, c=categoria: self.page.run_task(
                                            self.eliminar_categoria,
                                            c
                                        ),
                                        disabled=cant_socios > 0
                                    ),
                                ],
                                spacing=0
                            )
                        ),
                    ]
                )
            )
        
        if self.page:
            self.page.update()
    
    def show_nueva_categoria_dialog(self):
        """Mostrar diálogo para crear categoría"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
            # Campos
        nombre_field = ft.TextField(
            label="Nombre *",
            hint_text="Ej: Titular, Adherente, Cadete",
            autofocus=True
        )
        
        descripcion_field = ft.TextField(
            label="Descripción",
            hint_text="Descripción de la categoría",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        cuota_base_field = ft.TextField(
            label="Cuota Base *",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$"
        )
        
        tiene_cuota_fija = ft.Checkbox(
            label="Cuota Fija (marcar si la cuota no varía)",
            value=True
        )
        
        caracteristicas_field = ft.TextField(
            label="Características",
            hint_text="Beneficios y características de esta categoría",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        async def guardar_categoria(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            # Validaciones
            if not nombre_field.value:
                error_banner.show_error("⚠️ El nombre de la categoría es obligatorio")
                return
            
            if not cuota_base_field.value:
                error_banner.show_error("⚠️ La cuota base es obligatoria")
                return
            
            # Validar monto numérico
            try:
                cuota = float(cuota_base_field.value)
                if cuota < 0:
                    error_banner.show_error("⚠️ La cuota no puede ser negativa")
                    return
            except ValueError:
                error_banner.show_error("⚠️ Ingresa un monto válido para la cuota")
                return
            
            try:
                # Preparar data según el schema del backend
                data = {
                    "nombre": nombre_field.value.strip(),
                    "descripcion": descripcion_field.value.strip() if descripcion_field.value else "",
                    "cuota_base": float(cuota),
                    "tiene_cuota_fija": tiene_cuota_fija.value,
                    "caracteristicas": caracteristicas_field.value.strip() if caracteristicas_field.value else "",
                    "modulo_tipo": "generico"
                }
                
                await api_client.create_categoria(data)
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "✓ Categoría creada exitosamente")
                await self.load_categorias()
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                handle_api_error_with_banner(ex, error_banner, "crear categoría")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nueva Categoría"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Formulario
                        nombre_field,
                        descripcion_field,
                        ft.Divider(),
                        ft.Text("Configuración Financiera", weight=ft.FontWeight.BOLD),
                        cuota_base_field,
                        tiene_cuota_fija,
                        ft.Container(
                            content=ft.Text(
                                "ℹ️ Las cuotas fijas tienen el mismo monto siempre.\n"
                                "Las variables pueden cambiar según consumo u otros factores.",
                                size=11,
                                color=ft.Colors.GREY_700,
                                #italic=True
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            padding=8,
                            border_radius=5
                        ),
                        ft.Divider(),
                        caracteristicas_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=450
                ),
                width=450,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Crear Categoría",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: self.page.run_task(guardar_categoria, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_edit_categoria_dialog(self, categoria: dict):
        """Mostrar diálogo para editar categoría"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        
        nombre_field = ft.TextField(
            label="Nombre *",
            value=categoria.get("nombre", "")
        )
        
        descripcion_field = ft.TextField(
            label="Descripción",
            value=categoria.get("descripcion", ""),
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        cuota_base_field = ft.TextField(
            label="Cuota Base *",
            value=str(categoria.get("cuota_base", 0)),
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$"
        )
        
        tiene_cuota_fija = ft.Checkbox(
            label="Cuota Fija",
            value=categoria.get("tiene_cuota_fija", True)
        )
        
        caracteristicas_field = ft.TextField(
            label="Características",
            value=categoria.get("caracteristicas", ""),
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        async def guardar_cambios(e):
            """Guarda los cambios realizados en la categoría"""
            try:
                error_banner.hide()
                success_banner.hide()
                
                # Validaciones individuales con mensajes específicos
                if not nombre_field.value or not nombre_field.value.strip():
                    error_banner.show_error('El nombre de la categoría es obligatorio')
                    return
                
                if not cuota_base_field.value or not cuota_base_field.value.strip():
                    error_banner.show_error('La cuota base es obligatoria')
                    return
                
                try:
                    cuota_valor = float(cuota_base_field.value.strip())
                    if cuota_valor < 0:
                        error_banner.show_error('La cuota base no puede ser negativa')
                        return
                except ValueError:
                    error_banner.show_error('La cuota base debe ser un número válido')
                    return
                
                # Preparar los datos
                datos_actualizados = {
                    'nombre': nombre_field.value.strip(),
                    'descripcion': descripcion_field.value.strip() if descripcion_field.value else None,
                    'cuota_base': cuota_valor,
                    'tiene_cuota_fija': tiene_cuota_fija.value,
                    'caracteristicas': [c.strip() for c in caracteristicas_field.value.split(',') if c.strip()] if caracteristicas_field.value else []
                }
                
                # Actualizar en la API
                response = await self.api_client.put(
                    f'/categorias/{categoria["id"]}',
                    datos_actualizados
                )
                
                if response.get('ok'):
                    show_success(self.page, 'Categoría actualizada exitosamente')
                    dialog.open = False
                    await self.page.update_async()
                    await self.cargar_categorias()
                else:
                    error_banner.show_error(response.get('error', 'Error al actualizar la categoría'))
                    
            except Exception as ex:
                handle_api_error_with_banner(ex, error_banner, 'actualizar la categoría')

        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar Categoría - {categoria.get('nombre', '')}"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"ID: {categoria.get('id')}",
                            size=12,
                            color=ft.Colors.GREY_600
                        ),
                        ft.Divider(),
                        error_banner,
                        success_banner,
                        nombre_field,
                        descripcion_field,
                        ft.Divider(),
                        ft.Text("Configuración Financiera", weight=ft.FontWeight.BOLD),
                        cuota_base_field,
                        tiene_cuota_fija,
                        ft.Divider(),
                        caracteristicas_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=450
                ),
                width=450,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Guardar Cambios",
                    icon=ft.Icons.SAVE,
                    on_click=lambda e: self.page.run_task(guardar_cambios, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_categoria_details(self, categoria: dict):
        """Mostrar detalles de la categoría"""
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(categoria.get("nombre", "")),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DESCRIPTION),
                            title=ft.Text("Descripción"),
                            subtitle=ft.Text(categoria.get("descripcion", "Sin descripción"))
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.ATTACH_MONEY),
                            title=ft.Text("Cuota Base"),
                            subtitle=ft.Text(
                                f"${categoria.get('cuota_base', 0):,.2f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_700
                            )
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PAYMENT),
                            title=ft.Text("Tipo de Cuota"),
                            subtitle=ft.Text(
                                "Fija" if categoria.get("tiene_cuota_fija") else "Variable"
                            )
                        ),
                        ft.Divider(),
                        ft.Text("Características", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                categoria.get("caracteristicas", "Sin características definidas"),
                                size=12
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            padding=10,
                            border_radius=5
                        ),
                    ],
                    spacing=10
                ),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar_dialogo)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    async def eliminar_categoria(self, categoria: dict):
        """Eliminar categoría"""
        try:
            # Confirmar
            def confirmar(e):
                resultado["confirmed"] = True
                dialogo_confirm.open = False
                self.page.update()
            
            def cancelar(e):
                resultado["confirmed"] = False
                dialogo_confirm.open = False
                self.page.update()
            
            resultado = {"confirmed": False}
            
            dialogo_confirm = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED),
                        ft.Text("Eliminar Categoría", color=ft.Colors.RED)
                    ],
                    spacing=10
                ),
                content=ft.Column(
                    [
                        ft.Text(
                            f"¿Estás seguro de eliminar la categoría '{categoria.get('nombre', '')}'?",
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Esta acción no se puede deshacer.",
                            color=ft.Colors.GREY_700
                        ),
                    ],
                    spacing=10,
                    tight=True
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.ElevatedButton(
                        "Eliminar",
                        icon=ft.Icons.DELETE,
                        on_click=confirmar,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED)
                    ),
                ],
            )
            
            self.page.overlay.append(dialogo_confirm)
            dialogo_confirm.open = True
            self.page.update()
            
            # Esperar confirmación
            import asyncio
            while dialogo_confirm.open:
                await asyncio.sleep(0.1)
            
            if not resultado["confirmed"]:
                return
            
            # Eliminar
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.delete(
                    f"{api_client.base_url}/miembros/categorias/{categoria['id']}",
                    headers=api_client._get_headers()
                )
                response.raise_for_status()
            
            self.show_snackbar("✓ Categoría eliminada")
            await self.load_categorias()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error: {e}", error=True)
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()