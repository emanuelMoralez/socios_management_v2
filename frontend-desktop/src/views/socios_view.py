"""
Vista de Gestión de Socios
frontend-desktop/src/views/socios_view.py
"""
import flet as ft
from src.services.api_client import api_client
from src.utils.error_handler import handle_api_error, show_success, handle_api_error_with_banner
from src.components.error_banner import ErrorBanner, SuccessBanner
from datetime import date, datetime


class SociosView(ft.Column):
    """Vista principal de gestión de socios"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.socios = []
        self.categorias = []
        self.current_page = 1
        self.total_pages = 1
        
        # Búsqueda
        self.search_field = ft.TextField(
            hint_text="Buscar por nombre, apellido o documento...",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda _: self.page.run_task(self.load_socios),
            expand=True
        )
        
        self.filter_estado = ft.Dropdown(
            label="Estado",
            hint_text="Todos",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("activo", "Activo"),
                ft.dropdown.Option("moroso", "Moroso"),
                ft.dropdown.Option("suspendido", "Suspendido"),
            ],
            width=200,
            on_change=lambda _: self.page.run_task(self.load_socios)
        )
        
        # Tabla de socios
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° Socio")),
                ft.DataColumn(ft.Text("Nombre Completo")),
                ft.DataColumn(ft.Text("Documento")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Saldo")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Paginación
        self.pagination = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False
        )
        
        # Construir UI
        self.build_ui()
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            # Título y botón nuevo
            ft.Row(
                [
                    ft.Text(
                        "Gestión de Socios",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.ElevatedButton(
                        "Nuevo Socio",
                        icon=ft.Icons.ADD,
                        on_click=lambda _: self.show_nuevo_socio_dialog()
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
            ft.Divider(),
            
            # Filtros
            ft.Row(
                [
                    self.search_field,
                    self.filter_estado,
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Actualizar",
                        on_click=lambda _: self.page.run_task(self.load_socios)
                    )
                ],
                spacing=10
            ),
            
            ft.Divider(),
            
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
            ),
            
            # Paginación
            self.pagination
        ]
        
        self.spacing = 10
        self.expand = True

    def _create_photo_controls(self, foto_seleccionada: dict, initial_url: str | None = None):
        """Crear controles reutilizables para manejo de foto (preview, botones, filepicker, cámara).
        Retorna un dict con widgets y helpers que el caller puede integrar en su diálogo.
        - foto_seleccionada: dict compartido para guardar 'data' y 'nombre'
        - initial_url: url de la foto existente (opcional)
        """
        # Componentes para la foto
        foto_preview = ft.Image(
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            visible=False
        )

        # Cargar foto inicial si se proporciona
        if initial_url:
            foto_preview.src = initial_url
            foto_preview.visible = True

        foto_texto = ft.Text(
            "Foto actual" if initial_url else "No se ha capturado ninguna foto",
            size=12,
            color=ft.Colors.GREEN if initial_url else ft.Colors.GREY_500,
            italic=not initial_url,
            expand=True
        )

        boton_limpiar_foto = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip="Eliminar foto",
            icon_color=ft.Colors.RED,
            visible=bool(initial_url)
        )

        # Container para los controles de foto
        foto_controls_container = ft.Column(
            [
                foto_texto,
                boton_limpiar_foto
            ],
            expand=True
        )

        # Contexto para la cámara (permite que el caller asigne el diálogo principal después)
        camara_context = {"dialogo_principal": None, "dialogo_camara": None}

        def on_file_selected(e: ft.FilePickerResultEvent):
            """Callback cuando se selecciona un archivo"""
            if e.files and len(e.files) > 0:
                file = e.files[0]
                import base64
                try:
                    with open(file.path, "rb") as f:
                        foto_bytes = f.read()
                        foto_base64 = base64.b64encode(foto_bytes).decode()

                        # Guardar en variable
                        foto_seleccionada["data"] = foto_base64
                        foto_seleccionada["nombre"] = file.name

                        # Mostrar preview
                        foto_preview.src_base64 = foto_base64
                        foto_preview.visible = True
                        foto_texto.value = f"✓ {file.name}"
                        foto_texto.color = ft.Colors.GREEN
                        foto_texto.italic = False
                        boton_limpiar_foto.visible = True

                        foto_controls_container.update()
                        foto_preview.update()

                except Exception as ex:
                    self.show_snackbar(f"Error al cargar imagen: {ex}", error=True)

        file_picker = ft.FilePicker(on_result=on_file_selected)

        def abrir_camara(e):
            """Abrir diálogo de cámara para tomar foto usando OpenCV"""
            # el caller debe haber asignado camara_context['dialogo_principal'] = dialogo
            dialogo_principal = camara_context.get("dialogo_principal")

            try:
                import cv2
                import numpy as np
                import base64

                # Abrir la cámara
                cap = cv2.VideoCapture(0)

                if not cap.isOpened():
                    self.show_snackbar("No se pudo acceder a la cámara", error=True)
                    return

                # Variables para el preview
                preview_image = ft.Image(
                    width=480,
                    height=360,
                    fit=ft.ImageFit.CONTAIN
                )

                # Stack para superponer la guía sobre la imagen
                preview_stack = ft.Stack(
                    [
                        preview_image,
                        # Guía de centrado - óvalo para la cara
                        ft.Container(
                            content=ft.Container(
                                width=200,
                                height=260,
                                border=ft.border.all(3, ft.Colors.GREEN_400),
                                border_radius=100,
                            ),
                            alignment=ft.alignment.center
                        ),
                        # Texto de ayuda
                        ft.Container(
                            content=ft.Text(
                                "Centra tu rostro en el óvalo",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
                            ),
                            alignment=ft.alignment.top_center,
                            padding=10
                        )
                    ],
                    width=480,
                    height=360
                )

                captura_guardada = {"frame": None}

                def actualizar_preview():
                    """Actualizar preview de la cámara en tiempo real"""
                    try:
                        ret, frame = cap.read()
                        if ret:
                            # Convertir frame a JPEG
                            _, buffer = cv2.imencode('.jpg', frame)
                            jpg_as_text = base64.b64encode(buffer).decode()

                            # Actualizar imagen preview
                            preview_image.src_base64 = jpg_as_text
                            if camara_context.get("dialogo_camara") and camara_context["dialogo_camara"].open:
                                camara_context["dialogo_camara"].content.update()
                    except Exception:
                        pass

                def capturar_foto(e):
                    """Capturar foto desde la cámara"""
                    try:
                        ret, frame = cap.read()
                        if ret:
                            captura_guardada["frame"] = frame.copy()

                            # Convertir a JPEG y base64
                            _, buffer = cv2.imencode('.jpg', frame)
                            foto_base64 = base64.b64encode(buffer).decode()

                            # Guardar en variable
                            foto_seleccionada["data"] = foto_base64
                            foto_seleccionada["nombre"] = "foto_capturada.jpg"

                            # Mostrar preview en el diálogo principal
                            foto_preview.src_base64 = foto_base64
                            foto_preview.visible = True
                            foto_texto.value = "✓ Foto capturada"
                            foto_texto.color = ft.Colors.GREEN
                            foto_texto.italic = False
                            boton_limpiar_foto.visible = True

                            # Liberar cámara
                            cap.release()

                            # Cerrar diálogo de cámara
                            if camara_context.get("dialogo_camara"):
                                camara_context["dialogo_camara"].open = False
                                try:
                                    self.page.overlay.remove(camara_context["dialogo_camara"])
                                except Exception:
                                    pass

                            # Asegurarse que el diálogo principal esté abierto
                            if dialogo_principal:
                                dialogo_principal.open = True

                            # Pequeño delay antes de actualizar
                            import time
                            time.sleep(0.1)

                            # Actualizar la página
                            self.page.update()

                            self.show_snackbar("Foto capturada exitosamente")
                        else:
                            self.show_snackbar("No se pudo capturar la foto", error=True)

                    except Exception as ex:
                        import traceback
                        traceback.print_exc()
                        self.show_snackbar(f"Error al capturar foto: {ex}", error=True)

                def cerrar_camara(e):
                    """Cerrar diálogo de cámara y liberar recursos"""
                    cap.release()
                    if camara_context.get("dialogo_camara"):
                        camara_context["dialogo_camara"].open = False
                        try:
                            self.page.overlay.remove(camara_context["dialogo_camara"])
                        except Exception:
                            pass

                    # Asegurarse que el diálogo principal esté abierto
                    if dialogo_principal:
                        dialogo_principal.open = True

                    self.page.update()

                # Crear diálogo de cámara
                dialogo_camara = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Capturar Foto - Centra el rostro"),
                    content=ft.Container(
                        content=ft.Column(
                            [
                                preview_stack,
                                ft.Text(
                                    "📸 Consejos: Buena iluminación, fondo neutro, mirar a la cámara",
                                    size=11,
                                    color=ft.Colors.GREY_600,
                                    text_align=ft.TextAlign.CENTER,
                                    #italic=True
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10
                        ),
                        width=500,
                        padding=20
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=cerrar_camara),
                        ft.ElevatedButton(
                            "Capturar",
                            icon=ft.Icons.CAMERA,
                            on_click=capturar_foto
                        )
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )

                camara_context["dialogo_camara"] = dialogo_camara
                self.page.overlay.append(dialogo_camara)
                dialogo_camara.open = True
                self.page.update()

                # Iniciar actualización del preview
                import time
                import threading

                def loop_preview():
                    while camara_context.get("dialogo_camara") and camara_context["dialogo_camara"].open:
                        actualizar_preview()
                        time.sleep(0.1)  # 10 FPS

                # Ejecutar preview en thread separado
                preview_thread = threading.Thread(target=loop_preview, daemon=True)
                preview_thread.start()

            except ImportError:
                self.show_snackbar("Instala opencv-python: pip install opencv-python", error=True)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.show_snackbar(f"Error al acceder a la cámara: {ex}", error=True)

        def limpiar_foto(e):
            """Limpiar foto seleccionada"""
            foto_seleccionada["data"] = None
            foto_seleccionada["nombre"] = None
            foto_preview.visible = False
            foto_texto.value = "No se ha capturado ninguna foto"
            foto_texto.color = ft.Colors.GREY_500
            foto_texto.italic = True
            boton_limpiar_foto.visible = False

            foto_preview.update()
            foto_controls_container.update()

        # Asignar el callback al botón
        boton_limpiar_foto.on_click = limpiar_foto

        boton_subir_foto = ft.ElevatedButton(
            "Subir Foto",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda _: file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png"],
                dialog_title="Seleccionar foto del socio"
            )
        )

        boton_tomar_foto = ft.ElevatedButton(
            "Tomar Foto",
            icon=ft.Icons.CAMERA_ALT,
            on_click=abrir_camara
        )

        return {
            "foto_preview": foto_preview,
            "foto_texto": foto_texto,
            "boton_limpiar_foto": boton_limpiar_foto,
            "foto_controls_container": foto_controls_container,
            "file_picker": file_picker,
            "boton_subir_foto": boton_subir_foto,
            "boton_tomar_foto": boton_tomar_foto,
            "camara_context": camara_context,
            "limpiar_foto": limpiar_foto,
        }
    
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        if self.page:
            self.page.run_task(self.load_categorias)
            self.page.run_task(self.load_socios)
    
    async def load_categorias(self):
        """Cargar categorías disponibles"""
        try:
            self.categorias = await api_client.get_categorias()
        except Exception as e:
            print(f"Error cargando categorías: {e}")
    
    async def load_socios(self):
        """Cargar lista de socios"""
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            query = self.search_field.value or None
            estado = self.filter_estado.value or None
            
            response = await api_client.get_miembros(
                page=self.current_page,
                page_size=20,
                q=query,
                estado=estado
            )
            
            items = response.get("items", [])
            pagination = response.get("pagination", {})
            
            self.total_pages = pagination.get("total_pages", 1)
            
            # Actualizar tabla
            self.update_table(items)
            
            # Actualizar paginación
            self.update_pagination(pagination)
            
        except Exception as e:
            handle_api_error(self.page, e, "cargar socios")
        
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()
    
    def update_table(self, socios: list):
        """Actualizar tabla con datos"""
        self.data_table.rows.clear()
        
        for socio in socios:
            # Color según estado
            estado = socio.get("estado", "")
            if estado == "activo":
                estado_color = ft.Colors.GREEN
            elif estado == "moroso":
                estado_color = ft.Colors.RED
            else:
                estado_color = ft.Colors.ORANGE
            
            # Saldo
            saldo = socio.get("saldo_cuenta", 0)
            saldo_text = f"${saldo:,.2f}"
            saldo_color = ft.Colors.GREEN if saldo >= 0 else ft.Colors.RED
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(socio.get("numero_miembro", ""))),
                        ft.DataCell(ft.Text(socio.get("nombre_completo", ""))),
                        ft.DataCell(ft.Text(socio.get("numero_documento", ""))),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    estado.upper(),
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=estado_color,
                                padding=5,
                                border_radius=5
                            )
                        ),
                        ft.DataCell(
                            ft.Text(saldo_text, color=saldo_color, weight=ft.FontWeight.BOLD)
                        ),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY,
                                        tooltip="Ver detalles",
                                        on_click=lambda e, s=socio: self.show_socio_details(s)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.QR_CODE,
                                        tooltip="Ver QR",
                                        on_click=lambda e, s=socio: self.page.run_task(self.show_qr_dialog, s)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        tooltip="Editar",
                                        on_click=lambda e, s=socio: self.page.run_task(self.show_edit_dialog, s)
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
    
    def update_pagination(self, pagination: dict):
        """Actualizar controles de paginación"""
        page = pagination.get("page", 1)
        total_pages = pagination.get("total_pages", 1)
        has_prev = pagination.get("has_prev", False)
        has_next = pagination.get("has_next", False)
        
        self.pagination.controls.clear()
        
        self.pagination.controls.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                disabled=not has_prev,
                on_click=lambda _: self.go_to_page(page - 1)
            )
        )
        
        self.pagination.controls.append(
            ft.Text(f"Página {page} de {total_pages}")
        )
        
        self.pagination.controls.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                disabled=not has_next,
                on_click=lambda _: self.go_to_page(page + 1)
            )
        )
        
        self.pagination.visible = total_pages > 1
        if self.page:
            self.page.update()
    
    def go_to_page(self, page: int):
        """Ir a página específica"""
        self.current_page = page
        self.page.run_task(self.load_socios)
    
    def show_nuevo_socio_dialog(self):
        """Mostrar diálogo para crear nuevo socio"""

        # Variable para almacenar la foto
        foto_seleccionada = {"data": None, "nombre": None}
        
        # Banner de error para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        # Campos del formulario
        nombre_field = ft.TextField(label="Nombre *", autofocus=True, expand=True)
        apellido_field = ft.TextField(label="Apellido *", expand=True)
        documento_field = ft.TextField(label="Documento *", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        email_field = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL, expand=True)
        telefono_field = ft.TextField(label="Teléfono", expand=True)
        celular_field = ft.TextField(label="Celular", expand=True)
        direccion_field = ft.TextField(label="Dirección", expand=True)
        localidad_field = ft.TextField(label="Localidad", expand=True)
        provincia_field = ft.TextField(label="Provincia", expand=True)
        cod_postal_field = ft.TextField(label="Código Postal", expand=True)
        
        categoria_dropdown = ft.Dropdown(
            label="Categoría *",
            expand=True,
            options=[
                ft.dropdown.Option(str(cat["id"]), cat["nombre"])
                for cat in self.categorias
            ] if self.categorias else []
        )

        # Crear controles reutilizables para la foto
        photo = self._create_photo_controls(foto_seleccionada)
        foto_preview = photo["foto_preview"]
        foto_controls_container = photo["foto_controls_container"]
        boton_subir_foto = photo["boton_subir_foto"]
        boton_tomar_foto = photo["boton_tomar_foto"]
        file_picker = photo["file_picker"]

        # Adjuntar file_picker al overlay
        self.page.overlay.append(file_picker)
        
        
        boton_limpiar_foto = photo["boton_limpiar_foto"]

        async def guardar_socio(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            if not all([nombre_field.value, apellido_field.value, documento_field.value]):
                error_banner.show_error("⚠️ Completa los campos obligatorios (*)")
                return
            
            if not categoria_dropdown.value:
                error_banner.show_error("⚠️ Debes seleccionar una categoría")
                return
            
            try:
                data = {
                    "nombre": nombre_field.value,
                    "apellido": apellido_field.value,
                    "numero_documento": documento_field.value,
                    "tipo_documento": "dni",
                    "email": email_field.value or None,
                    "telefono": telefono_field.value or None,
                    "celular": celular_field.value or None,
                    "direccion": direccion_field.value or None,
                    "localidad": localidad_field.value or None,
                    "provincia": provincia_field.value or None,
                    "cod_postal": cod_postal_field.value or None,
                    "categoria_id": int(categoria_dropdown.value),
                    "modulo_tipo": "generico"
                }
                
                # Agregar foto si existe
                if foto_seleccionada["data"]:
                    data["foto_base64"] = foto_seleccionada["data"]
                    
                await api_client.create_miembro(data)
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "Socio creado exitosamente")
                await self.load_socios()
                
            except Exception as e:
                # Usar error handler con banner para mostrar error en el diálogo
                handle_api_error_with_banner(e, error_banner, "crear socio")
                # NO cerrar el diálogo para que el usuario pueda corregir
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo Socio"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Formulario
                        ft.Text("Datos Personales", weight=ft.FontWeight.BOLD),
                        ft.Row([nombre_field, apellido_field], spacing=10),
                        documento_field,
                        email_field,
                        ft.Divider(),
                        ft.Text("Contacto", weight=ft.FontWeight.BOLD),
                        ft.Row([telefono_field, celular_field], spacing=10),
                        ft.Divider(),
                        ft.Text("Domicilio", weight=ft.FontWeight.BOLD),
                        direccion_field,
                        ft.Row([localidad_field, cod_postal_field], spacing=10),
                        provincia_field,
                        ft.Divider(),
                        ft.Text("Categoría y Foto", weight=ft.FontWeight.BOLD, size=14),
                        ft.Row(
                            [
                                categoria_dropdown,
                                boton_tomar_foto,
                                boton_subir_foto
                            ],
                            spacing=10,
                            expand=True,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        ft.Row(
                            [
                                foto_preview,
                                foto_controls_container
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.START
                        ),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                width=500,
                height=600,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Guardar",
                    on_click=lambda e: self.page.run_task(guardar_socio, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        # Si el control de foto tiene contexto de camara, asignar el dialogo principal
        try:
            if photo.get('camara_context'):
                photo['camara_context']['dialogo_principal'] = dialogo
        except Exception:
            pass
        self.page.update()
    
    def show_socio_details(self, socio: dict):
        """Mostrar detalles del socio"""
        
        # Espacio para foto o icono genérico
        if socio.get("foto_url"):
            foto_widget = ft.Image(
                src=socio["foto_url"],
                width=120,
                height=120,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(60),
                bgcolor=ft.Colors.GREY_200
            )
        else:
            foto_widget = ft.Container(
                content=ft.Icon(ft.Icons.PERSON, size=80, color=ft.Colors.GREY_400),
                width=120,
                height=120,
                bgcolor=ft.Colors.GREY_200,
                border_radius=60,
                alignment=ft.alignment.center
            )

        detalles = ft.Column(
            [
                ft.Container(
                    content=foto_widget,
                    alignment=ft.alignment.center,
                    padding=10
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BADGE),
                    title=ft.Text("Número de Socio"),
                    subtitle=ft.Text(socio.get("numero_miembro", ""))
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON),
                    title=ft.Text("Nombre Completo"),
                    subtitle=ft.Text(socio.get("nombre_completo", ""))
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CREDIT_CARD),
                    title=ft.Text("Documento"),
                    subtitle=ft.Text(socio.get("numero_documento", ""))
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.EMAIL),
                    title=ft.Text("Email"),
                    subtitle=ft.Text(socio.get("email", "No especificado"))
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PHONE),
                    title=ft.Text("Teléfono"),
                    subtitle=ft.Text(socio.get("telefono", "No especificado"))
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET),
                    title=ft.Text("Saldo de Cuenta"),
                    subtitle=ft.Text(
                        f"${socio.get('saldo_cuenta', 0):,.2f}",
                        color=ft.Colors.GREEN if socio.get("saldo_cuenta", 0) >= 0 else ft.Colors.RED
                    )
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            height=450
        )
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalles del Socio"),
            content=ft.Container(content=detalles, width=400),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar_dialogo)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    async def show_qr_dialog(self, socio: dict):
        """Mostrar QR del socio"""
        
        try:
            qr_bytes = await api_client.get_miembro_qr(socio["id"])
            
            import base64
            qr_base64 = base64.b64encode(qr_bytes).decode()
            
            def cerrar_dialogo(e):
                dialogo.open = False
                self.page.update()
            
            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"QR - {socio.get('nombre_completo', '')}"),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(
                                src_base64=qr_base64,
                                width=300,
                                height=300,
                                fit=ft.ImageFit.CONTAIN
                            ),
                            ft.Text(
                                socio.get("numero_miembro", ""),
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    padding=20,
                    width=350
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=cerrar_dialogo)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            self.page.overlay.append(dialogo)
            dialogo.open = True
            self.page.update()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error cargando QR: {e}", error=True)
    
    async def show_edit_dialog(self, socio: dict):
        """Mostrar diálogo para editar socio"""
        
        try:
            # Obtener datos completos del socio desde el backend
            socio_completo = await api_client.get_miembro(socio["id"])

            # Banners de error/éxito para el diálogo
            error_banner = ErrorBanner()
            success_banner = SuccessBanner()

            # Variable para almacenar la foto
            foto_seleccionada = {"data": None, "nombre": None}

            # Campos del formulario prellenados con datos actuales
            nombre_field = ft.TextField(
                label="Nombre *",
                value=socio_completo.get("nombre", ""), expand=True
            )
            apellido_field = ft.TextField(
                label="Apellido *",
                value=socio_completo.get("apellido", ""), expand=True
            )
            email_field = ft.TextField(
                label="Email",
                value=socio_completo.get("email", ""),
                keyboard_type=ft.KeyboardType.EMAIL, expand=True
            )
            telefono_field = ft.TextField(
                label="Teléfono",
                value=socio_completo.get("telefono", ""), expand=True
            )
            celular_field = ft.TextField(
                label="Celular",
                value=socio_completo.get("celular", ""), expand=True
            )
            direccion_field = ft.TextField(
                label="Dirección",
                value=socio_completo.get("direccion", ""), expand=True
            )
            localidad_field = ft.TextField(
                label="Localidad",
                value=socio_completo.get("localidad", ""), expand=True
            )
            provincia_field = ft.TextField(
                label="Provincia",
                value=socio_completo.get("provincia", ""), expand=True
            )
            cod_postal_field = ft.TextField(
                label="Código Postal",
                value=socio_completo.get("cod_postal", ""), expand=True
            )
            
            # Dropdown de categoría
            categoria_actual = socio.get("categoria", {})
            categoria_id_actual = categoria_actual.get("id") if categoria_actual else None
            
            categoria_dropdown = ft.Dropdown(
                label="Categoría *",
                expand=True,
                value=str(categoria_id_actual) if categoria_id_actual else None,
                options=[
                    ft.dropdown.Option(str(cat["id"]), cat["nombre"])
                for cat in self.categorias
                ] if self.categorias else []
            )
        
            observaciones_field = ft.TextField(
                label="Observaciones",
                value=socio.get("observaciones", ""),
                multiline=True,
                min_lines=2,
                max_lines=5
            )

            # Crear controles reutilizables para la foto (con foto inicial si existe)
            photo = self._create_photo_controls(foto_seleccionada, initial_url=socio_completo.get("foto_url"))
            foto_preview = photo["foto_preview"]
            foto_controls_container = photo["foto_controls_container"]
            boton_subir_foto = photo["boton_subir_foto"]
            boton_tomar_foto = photo["boton_tomar_foto"]
            file_picker = photo["file_picker"]
            camara_context = photo["camara_context"]

            # Adjuntar file_picker al overlay
            self.page.overlay.append(file_picker)

            # Asignar dialogo principal en el contexto de la cámara para que pueda reabrirse al cerrar
            camara_context["dialogo_principal"] = None  # se asignará más abajo una vez creado el dialogo
        
            async def guardar_cambios(e):
                # Limpiar mensajes previos
                error_banner.hide()
                success_banner.hide()
            
                # Validar campos requeridos
                if not all([nombre_field.value, apellido_field.value]):
                    error_banner.show_error("⚠️ Completa los campos obligatorios (*)")
                    return
            
                if not categoria_dropdown.value:
                    error_banner.show_error("⚠️ Debes seleccionar una categoría")
                    return
                
                try:
                    data = {
                        "nombre": nombre_field.value,
                        "apellido": apellido_field.value,
                        "email": email_field.value or None,
                        "telefono": telefono_field.value or None,
                        "celular": celular_field.value or None,
                        "direccion": direccion_field.value or None,
                        "localidad": localidad_field.value or None,
                        "provincia": provincia_field.value or None,
                        "cod_postal": cod_postal_field.value or None,
                        "categoria_id": int(categoria_dropdown.value),
                        "observaciones": observaciones_field.value or None
                    }
                    
                    # Agregar foto si existe una nueva
                    if foto_seleccionada["data"]:
                        data["foto_base64"] = foto_seleccionada["data"]
                
                    await api_client.update_miembro(socio["id"], data)
                    
                    dialogo.open = False
                    self.page.update()
                    
                    show_success(self.page, "Socio actualizado exitosamente")
                    await self.load_socios()
                
                except Exception as e:
                    # Usar error handler con banner para mostrar error en el diálogo
                    handle_api_error_with_banner(e, error_banner, "actualizar socio")
                    # NO cerrar el diálogo para que el usuario pueda corregir
     
            def cerrar_dialogo(e):
                dialogo.open = False
                self.page.update()
        
            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Editar Socio - {socio_completo.get('numero_miembro', '')}"),
                content=ft.Container(
                    content=ft.Column(
                        [
                            # Banners para mensajes en el diálogo
                            error_banner,
                            success_banner,
                            
                            # Información del socio
                            ft.Text(
                                f"Documento: {socio_completo.get('numero_documento', '')}",
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                            ft.Divider(),
                            
                            # Formulario
                            ft.Text("Datos Personales", weight=ft.FontWeight.BOLD, size=14),
                            ft.Row([nombre_field, apellido_field], spacing=10),
                            email_field,
                            ft.Divider(),
                            ft.Text("Contacto", weight=ft.FontWeight.BOLD, size=14),
                            ft.Row([telefono_field, celular_field], spacing=10),
                            ft.Divider(),
                            ft.Text("Domicilio", weight=ft.FontWeight.BOLD, size=14),
                            direccion_field,
                            ft.Row([localidad_field, cod_postal_field], spacing=10),
                            provincia_field,
                            ft.Divider(),
                            ft.Text("Categoría y Foto", weight=ft.FontWeight.BOLD, size=14),
                            ft.Row(
                                [
                                    categoria_dropdown,
                                    boton_tomar_foto,
                                    boton_subir_foto
                                ],
                                spacing=10
                            ),
                            ft.Row(
                                [
                                    foto_preview,
                                    foto_controls_container
                                ],
                                spacing=10,
                                alignment=ft.MainAxisAlignment.START
                            ),
                            ft.Divider(),
                            ft.Text("Observaciones", weight=ft.FontWeight.BOLD, size=14),
                            observaciones_field,
                        ],
                        spacing=10,
                        tight=True,
                        scroll=ft.ScrollMode.AUTO,
                        height=600
                    ),
                    width=500,
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

            # Si el control de foto tiene contexto de camara, asignar el dialogo principal
            try:
                if 'camara_context' in locals() and camara_context:
                    camara_context['dialogo_principal'] = dialogo
            except Exception:
                pass

            # Forzar actualización después de agregar el diálogo
            self.page.update()

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error al cargar datos del socio: {e}", error=True)
            self.show_snackbar(f"Error al cargar datos del socio: {e}", error=True)
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()