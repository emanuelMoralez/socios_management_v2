"""
Vista de Gestión de Usuarios del Sistema - CORREGIDA
frontend-desktop/src/views/usuarios_view.py
"""
import flet as ft
from src.services.api_client import api_client
from src.utils.error_handler import handle_api_error_with_banner, show_success
from src.components.error_banner import ErrorBanner, SuccessBanner


class UsuariosView(ft.Column):
    """Vista de administración de usuarios del sistema"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.usuarios = []
        
        # Tabla de usuarios
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Nombre Completo")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Rol")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Último Login")),
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
                        "Gestión de Usuarios",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.ElevatedButton(
                        "Nuevo Usuario",
                        icon=ft.Icons.PERSON_ADD,
                        on_click=lambda _: self.show_nuevo_usuario_dialog()
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
                            "Los usuarios son los operadores del sistema (administradores, porteros, etc.)",
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
                        on_click=lambda _: self.page.run_task(self.load_usuarios)
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
            self.page.run_task(self.load_usuarios)
    
    async def load_usuarios(self):
        """Cargar lista de usuarios"""
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            usuarios = await api_client.get_usuarios()
            self.update_table(usuarios)
            
        except Exception as e:
            self.show_snackbar(f"Error: {e}", error=True)
        
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()
    
    def update_table(self, usuarios: list):
        """Actualizar tabla con datos"""
        self.data_table.rows.clear()
        
        for usuario in usuarios:
            # Color según rol
            rol = usuario.get("rol", "")
            if rol == "super_admin":
                rol_color = ft.Colors.PURPLE
            elif rol == "administrador":
                rol_color = ft.Colors.BLUE
            elif rol == "operador":
                rol_color = ft.Colors.GREEN
            elif rol == "portero":
                rol_color = ft.Colors.ORANGE
            else:
                rol_color = ft.Colors.GREY
            
            # Estado
            is_active = usuario.get("is_active", False)
            estado_icon = ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.CANCEL
            estado_color = ft.Colors.GREEN if is_active else ft.Colors.RED
            
            # Último login
            last_login = usuario.get("last_login")
            if last_login:
                last_login_text = last_login[:16]  # YYYY-MM-DD HH:MM
            else:
                last_login_text = "Nunca"
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(usuario.get("username", ""))),
                        ft.DataCell(ft.Text(usuario.get("nombre_completo", ""))),
                        ft.DataCell(ft.Text(usuario.get("email", ""))),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    rol.replace("_", " ").upper(),
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=rol_color,
                                padding=5,
                                border_radius=5
                            )
                        ),
                        ft.DataCell(
                            ft.Icon(
                                estado_icon,
                                color=estado_color,
                                size=20
                            )
                        ),
                        ft.DataCell(ft.Text(last_login_text, size=12)),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Editar",
                                        on_click=lambda e, u=usuario: self.show_edit_usuario_dialog(u)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                                        tooltip="Cambiar rol",
                                        on_click=lambda e, u=usuario: self.show_cambiar_rol_dialog(u)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.POWER_SETTINGS_NEW if is_active else ft.Icons.CHECK_CIRCLE_OUTLINE,
                                        tooltip="Desactivar" if is_active else "Activar",
                                        icon_color=ft.Colors.RED if is_active else ft.Colors.GREEN,
                                        on_click=lambda e, u=usuario: self.page.run_task(
                                            self.toggle_usuario_active,
                                            u
                                        )
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
    
    def show_nuevo_usuario_dialog(self):
        """Mostrar diálogo para crear usuario"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        # Campos
        username_field = ft.TextField(
            label="Username *",
            hint_text="Sin espacios ni caracteres especiales",
            autofocus=True
        )
        
        email_field = ft.TextField(
            label="Email *",
            keyboard_type=ft.KeyboardType.EMAIL
        )
        
        password_field = ft.TextField(
            label="Contraseña *",
            password=True,
            can_reveal_password=True,
            hint_text="Mínimo 8 caracteres"
        )
        
        confirm_password_field = ft.TextField(
            label="Confirmar Contraseña *",
            password=True,
            can_reveal_password=True
        )
        
        nombre_field = ft.TextField(label="Nombre *")
        apellido_field = ft.TextField(label="Apellido *")
        telefono_field = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.PHONE)
        
        rol_dropdown = ft.Dropdown(
            label="Rol *",
            value="operador",
            options=[
                ft.dropdown.Option("super_admin", "Super Admin"),
                ft.dropdown.Option("administrador", "Administrador"),
                ft.dropdown.Option("operador", "Operador"),
                ft.dropdown.Option("portero", "Portero"),
                ft.dropdown.Option("consulta", "Solo Consulta"),
            ]
        )
        
        async def guardar_usuario(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            # Validaciones
            if not all([
                username_field.value,
                email_field.value,
                password_field.value,
                nombre_field.value,
                apellido_field.value
            ]):
                error_banner.show_error("⚠️ Completa los campos obligatorios (*)")
                return
            
            if password_field.value != confirm_password_field.value:
                error_banner.show_error("⚠️ Las contraseñas no coinciden")
                return
            
            if len(password_field.value) < 8:
                error_banner.show_error("⚠️ La contraseña debe tener al menos 8 caracteres")
                return
            
            try:
                data = {
                    "username": username_field.value.strip(),
                    "email": email_field.value.strip(),
                    "password": password_field.value,
                    "confirm_password": confirm_password_field.value,
                    "nombre": nombre_field.value.strip(),
                    "apellido": apellido_field.value.strip(),
                    "telefono": telefono_field.value.strip() if telefono_field.value else "",
                    "rol": rol_dropdown.value
                }
                
                print(f"[DEBUG] Creando usuario: {data['username']}")
                
                # Usar el endpoint de registro directamente
                import httpx
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{api_client.base_url}/auth/register",
                        headers=api_client._get_headers(),
                        json=data
                    )
                    
                    # Manejar respuesta
                    if response.status_code == 201:
                        # Éxito
                        dialogo.open = False
                        self.page.update()
                        
                        show_success(self.page, "✓ Usuario creado exitosamente")
                        await self.load_usuarios()
                    else:
                        # Error - mostrar en banner
                        try:
                            error_detail = response.json().get("detail", "Error desconocido")
                            if isinstance(error_detail, list):
                                # Formato Pydantic
                                errors = [f"{err.get('loc', [''])[1]}: {err.get('msg', '')}" for err in error_detail]
                                error_banner.show_errors(errors)
                            elif isinstance(error_detail, dict):
                                # Formato dict de campos
                                error_banner.show_validation_errors(error_detail)
                            else:
                                # String simple
                                error_banner.show_error(f"❌ {error_detail}")
                        except:
                            error_banner.show_error(f"❌ Error HTTP {response.status_code}")
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                handle_api_error_with_banner(ex, error_banner, "crear usuario")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo Usuario del Sistema"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Formulario
                        ft.Text("Credenciales", weight=ft.FontWeight.BOLD),
                        username_field,
                        email_field,
                        password_field,
                        confirm_password_field,
                        ft.Divider(),
                        ft.Text("Información Personal", weight=ft.FontWeight.BOLD),
                        ft.Row([nombre_field, apellido_field], spacing=10),
                        telefono_field,
                        ft.Divider(),
                        ft.Text("Permisos", weight=ft.FontWeight.BOLD),
                        rol_dropdown,
                        ft.Container(
                            content=ft.Text(
                                "⚠️ Super Admin tiene acceso total al sistema",
                                size=11,
                                color=ft.Colors.ORANGE_700,
                                italic=True
                            ),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=8,
                            border_radius=5
                        )
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=500
                ),
                width=450,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Crear Usuario",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: self.page.run_task(guardar_usuario, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_edit_usuario_dialog(self, usuario: dict):
        """Mostrar diálogo para editar usuario"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        # Extraer nombre y apellido del nombre_completo
        nombre_completo = usuario.get("nombre_completo", "")
        if ", " in nombre_completo:
            apellido, nombre = nombre_completo.split(", ", 1)
        else:
            nombre = nombre_completo
            apellido = ""
        
        email_field = ft.TextField(
            label="Email",
            value=usuario.get("email", ""),
            keyboard_type=ft.KeyboardType.EMAIL
        )
        
        nombre_field = ft.TextField(
            label="Nombre",
            value=nombre
        )
        
        apellido_field = ft.TextField(
            label="Apellido",
            value=apellido
        )
        
        telefono_field = ft.TextField(
            label="Teléfono",
            value=usuario.get("telefono", "") or ""
        )
        
        async def guardar_cambios(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            try:
                data = {
                    "email": email_field.value,
                    "nombre": nombre_field.value,
                    "apellido": apellido_field.value,
                    "telefono": telefono_field.value or None
                }
                
                import httpx
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.put(
                        f"{api_client.base_url}/usuarios/{usuario['id']}",
                        headers=api_client._get_headers(),
                        json=data
                    )
                    response.raise_for_status()
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "✓ Usuario actualizado")
                await self.load_usuarios()
                
            except Exception as ex:
                handle_api_error_with_banner(ex, error_banner, "actualizar usuario")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar Usuario - {usuario.get('username', '')}"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Información del usuario
                        ft.Text(
                            f"ID: {usuario.get('id')} | Rol: {usuario.get('rol', '').replace('_', ' ').upper()}",
                            size=12,
                            color=ft.Colors.GREY_600
                        ),
                        ft.Divider(),
                        
                        # Formulario
                        email_field,
                        ft.Row([nombre_field, apellido_field], spacing=10),
                        telefono_field,
                    ],
                    spacing=10
                ),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Guardar",
                    icon=ft.Icons.SAVE,
                    on_click=lambda e: self.page.run_task(guardar_cambios, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_cambiar_rol_dialog(self, usuario: dict):
        """Mostrar diálogo para cambiar rol"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        rol_dropdown = ft.Dropdown(
            label="Nuevo Rol",
            value=usuario.get("rol", ""),
            options=[
                ft.dropdown.Option("super_admin", "Super Admin"),
                ft.dropdown.Option("administrador", "Administrador"),
                ft.dropdown.Option("operador", "Operador"),
                ft.dropdown.Option("portero", "Portero"),
                ft.dropdown.Option("consulta", "Solo Consulta"),
            ]
        )
        
        async def cambiar_rol(e):
            """Cambia el rol del usuario con validaciones de seguridad"""
            try:
                error_banner.hide()
                success_banner.hide()
                
                # Validación 1: Rol seleccionado
                if not rol_dropdown.value or not rol_dropdown.value.strip():
                    error_banner.show_error('Debe seleccionar un rol')
                    return
                
                # Validación 2: Rol diferente al actual
                if rol_dropdown.value == usuario.get("rol"):
                    error_banner.show_validation_errors([
                        'El nuevo rol debe ser diferente al rol actual'
                    ])
                    return
                
                # Validación 3: No degradar al único Super Admin (crítico)
                if usuario.get("rol") == "super_admin" and rol_dropdown.value != "super_admin":
                    # Verificar si es el único super admin
                    super_admins = [u for u in self.usuarios if u.get("rol") == "super_admin" and u.get("is_active")]
                    if len(super_admins) <= 1:
                        error_banner.show_error(
                            '⚠️ No se puede cambiar el rol del único Super Admin activo. '
                            'Debe haber al menos un Super Admin en el sistema.'
                        )
                        return
                
                data = {
                    "usuario_id": usuario["id"],
                    "nuevo_rol": rol_dropdown.value
                }
                
                import httpx
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{api_client.base_url}/usuarios/cambiar-rol",
                        headers=api_client._get_headers(),
                        json=data
                    )
                    response.raise_for_status()
                
                show_success(self.page, f"Rol actualizado a {rol_dropdown.value.replace('_', ' ').title()}")
                dialogo.open = False
                self.page.update()
                await self.load_usuarios()
                
            except Exception as ex:
                handle_api_error_with_banner(ex, error_banner, 'cambiar el rol')
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.BLUE),
                    ft.Text("Cambiar Rol de Usuario")
                ],
                spacing=10
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        error_banner,
                        success_banner,
                        ft.Text(
                            f"Usuario: {usuario.get('nombre_completo', '')}",
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            f"Rol actual: {usuario.get('rol', '').replace('_', ' ').upper()}",
                            color=ft.Colors.GREY_700
                        ),
                        ft.Divider(),
                        rol_dropdown,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Permisos por rol:", weight=ft.FontWeight.BOLD, size=12),
                                    ft.Text("• Super Admin: Acceso total", size=11),
                                    ft.Text("• Administrador: Gestión completa", size=11),
                                    ft.Text("• Operador: Registro de datos", size=11),
                                    ft.Text("• Portero: Solo control de acceso", size=11),
                                    ft.Text("• Consulta: Solo lectura", size=11),
                                ],
                                spacing=3
                            ),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=10,
                            border_radius=5
                        )
                    ],
                    spacing=10
                ),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Cambiar Rol",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: self.page.run_task(cambiar_rol, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    async def toggle_usuario_active(self, usuario: dict):
        """Activar/desactivar usuario"""
        try:
            is_active = usuario.get("is_active", False)
            accion = "desactivar" if is_active else "activar"
            
            # Confirmar
            confirmar = await self.show_confirm_dialog(
                f"¿Estás seguro de {accion} el usuario {usuario.get('username', '')}?",
                f"El usuario {'no podrá' if is_active else 'podrá'} iniciar sesión."
            )
            
            if not confirmar:
                return
            
            data = {
                "usuario_id": usuario["id"],
                "activar": not is_active
            }
            
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{api_client.base_url}/usuarios/toggle-active",
                    headers=api_client._get_headers(),
                    json=data
                )
                response.raise_for_status()
            
            self.show_snackbar(f"✓ Usuario {accion}do")
            await self.load_usuarios()
            
        except Exception as e:
            self.show_snackbar(f"Error: {e}", error=True)
    
    async def show_confirm_dialog(self, title: str, message: str) -> bool:
        """Mostrar diálogo de confirmación y esperar respuesta"""
        resultado = {"confirmed": False}
        
        def confirmar(e):
            resultado["confirmed"] = True
            dialogo.open = False
            self.page.update()
        
        def cancelar(e):
            resultado["confirmed"] = False
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Confirmar", on_click=confirmar),
            ],
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
        
        # Esperar a que se cierre el diálogo
        import asyncio
        while dialogo.open:
            await asyncio.sleep(0.1)
        
        return resultado["confirmed"]
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()