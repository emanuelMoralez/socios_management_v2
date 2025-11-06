"""
Vista de Control de Accesos con Escáner QR
frontend-desktop/src/views/accesos_qr_view.py
"""
import flet as ft
from src.services.api_client import api_client
from datetime import datetime
import asyncio


class AccesosQRView(ft.Column):
    """Vista de control de accesos con escáner QR en tiempo real"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.escaneando = False
        self.camara_activa = False
        
        # Estado
        self.ultimo_qr = None
        self.validando = False
        
        # Estadísticas
        self.stats = {
            "total_hoy": 0,
            "entradas_hoy": 0,
            "rechazos_hoy": 0,
            "advertencias_hoy": 0
        }
        
        # Crear controles individuales primero
        self.camera_image = ft.Image(
            width=560,
            height=420,
            fit=ft.ImageFit.CONTAIN,
            visible=False  # Oculto hasta que se active la cámara
        )
        
        # Referencias para guía QR
        self.qr_guide = None
        self.qr_instruction = None
        
        # Placeholder cuando la cámara está inactiva
        self.camera_placeholder = ft.Column(
            [
                ft.Icon(
                    ft.Icons.QR_CODE_SCANNER,
                    size=120,
                    color=ft.Colors.GREY_400
                ),
                ft.Text(
                    "Presiona 'Iniciar Escáner'\npara activar la cámara",
                    size=16,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )
        
        self.loading_indicator = ft.ProgressRing(
            width=50,
            height=50,
            stroke_width=4,
            color=ft.Colors.GREEN,
            visible=False
        )
        
        self.status_text = ft.Text(
            "",
            size=14,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
            visible=False
        )
        
        # Preview de cámara
        self.camera_preview = ft.Stack(
            [
                # Fondo gris neutro
                ft.Container(
                    width=560,
                    height=420,
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=10
                ),
                # Placeholder (visible cuando cámara inactiva)
                ft.Container(
                    content=self.camera_placeholder,
                    alignment=ft.alignment.center
                ),
                # Imagen de la cámara (oculta inicialmente)
                ft.Container(
                    content=self.camera_image,
                    alignment=ft.alignment.center
                ),
                # Guía de centrado para QR (solo visible cuando cámara activa)
                self._create_qr_guide(),
                # Texto instructivo (solo visible cuando cámara activa)
                self._create_qr_instruction(),
                # Estado de escaneo
                ft.Container(
                    content=ft.Column(
                        [
                            self.loading_indicator,
                            self.status_text
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    alignment=ft.alignment.center
                )
            ],
            width=560,
            height=420
        )
        
        # Panel de resultado
        self.resultado_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.QR_CODE_SCANNER,
                        size=60,
                        color=ft.Colors.GREY_400
                    ),
                    ft.Text(
                        "Esperando escaneo...",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15
            ),
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            padding=20,
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Cards de estadísticas
        self.card_total = self.create_stat_card("Total Hoy", "0", ft.Icons.PEOPLE, ft.Colors.BLUE)
        self.card_entradas = self.create_stat_card("Permitidos", "0", ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN)
        self.card_rechazos = self.create_stat_card("Rechazados", "0", ft.Icons.CANCEL, ft.Colors.RED)
        self.card_advertencias = self.create_stat_card("Advertencias", "0", ft.Icons.WARNING, ft.Colors.ORANGE)
        
        # Últimos accesos
        self.ultimos_accesos_list = ft.Column(
            [], 
            spacing=5, 
            scroll=ft.ScrollMode.AUTO, 
            height=700,
            expand=True
        )
        
        # Construir UI
        self.build_ui()
    
    def create_stat_card(self, title: str, value: str, icon, color):
        """Crear card de estadística"""
        value_text = ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=color)
        
        card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(title, size=12, color=ft.Colors.GREY_600),
                    value_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
            )
        )
        
        card.data = {"value_text": value_text}
        return card
    
    def _create_qr_guide(self):
        """Crear guía QR con referencia guardada"""
        self.qr_guide = ft.Container(
            content=ft.Container(
                width=250,
                height=250,
                border=ft.border.all(4, ft.Colors.GREEN_400),
                border_radius=20,
            ),
            alignment=ft.alignment.center,
            visible=False
        )
        return self.qr_guide
    
    def _create_qr_instruction(self):
        """Crear instrucción QR con referencia guardada"""
        self.qr_instruction = ft.Container(
            content=ft.Text(
                "Centra el código QR en el recuadro",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            ),
            alignment=ft.alignment.top_center,
            padding=15,
            visible=False
        )
        return self.qr_instruction
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            # Título y controles
            ft.Row(
                [
                    ft.Text(
                        "Control de Accesos - Escáner QR",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Iniciar Escáner",
                                icon=ft.Icons.CAMERA_ALT,
                                on_click=lambda _: self.toggle_scanner(),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
                            ),
                            ft.ElevatedButton(
                                "Actualizar",
                                icon=ft.Icons.REFRESH,
                                on_click=lambda _: self.page.run_task(self.load_estadisticas)
                            ),
                        ],
                        spacing=10
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
            ft.Divider(),
            
            # Estadísticas
            ft.Row(
                [
                    self.card_total,
                    self.card_entradas,
                    self.card_rechazos,
                    self.card_advertencias
                ],
                spacing=15
            ),
            
            ft.Divider(),
            
            # Layout principal: 3 COLUMNAS (40% - 30% - 30%)
            ft.Row(
                [
                    # COLUMNA 1: Escáner QR (40% del ancho)
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.QR_CODE_SCANNER, size=24, color=ft.Colors.BLUE),
                                        ft.Text(
                                            "Escáner de QR",
                                            size=18,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                    ],
                                    spacing=10
                                ),
                                ft.Row(
                                    [
                                        ft.Text("Estado:", size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            "⚫ Inactivo",
                                            size=12,
                                            color=ft.Colors.GREY,
                                            data={"status_indicator": True}
                                        )
                                    ],
                                    spacing=5
                                ),
                                ft.Divider(height=5),
                                self.camera_preview,
                            ],
                            spacing=10,
                            expand=True
                        ),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        expand=4,  # 40% del espacio
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
                        )
                    ),
                    
                    # COLUMNA 2: Resultado de Validación (30% del ancho)
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=24, color=ft.Colors.GREEN),
                                        ft.Text(
                                            "Resultado",
                                            size=18,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                    ],
                                    spacing=10
                                ),
                                ft.Divider(height=5),
                                self.resultado_panel
                            ],
                            spacing=10,
                            expand=True
                        ),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        expand=3,  # 30% del espacio
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
                        )
                    ),
                    
                    # COLUMNA 3: Últimos Accesos (30% del ancho)
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.HISTORY, size=24, color=ft.Colors.BLUE),
                                        ft.Text(
                                            "Historial",
                                            size=18,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                    ],
                                    spacing=10
                                ),
                                ft.Divider(),
                                self.ultimos_accesos_list
                            ],
                            spacing=10,
                            expand=True
                        ),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        expand=3,  # 30% del espacio
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
                        )
                    )
                ],
                spacing=15,
                expand=True,
                alignment=ft.MainAxisAlignment.START
            )
        ]
        
        self.spacing = 15
        self.expand = True
    
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        if self.page:
            self.page.run_task(self.load_estadisticas)
    
    async def load_estadisticas(self):
        """Cargar estadísticas del día"""
        try:
            stats = await api_client.get_estadisticas_accesos()
            
            # Actualizar stats
            self.stats["total_hoy"] = stats.get("total_hoy", 0)
            self.stats["entradas_hoy"] = stats.get("entradas_hoy", 0)
            self.stats["rechazos_hoy"] = stats.get("rechazos_hoy", 0)
            self.stats["advertencias_hoy"] = stats.get("advertencias_hoy", 0)
            
            # Actualizar cards
            self.card_total.data["value_text"].value = str(self.stats["total_hoy"])
            self.card_entradas.data["value_text"].value = str(self.stats["entradas_hoy"])
            self.card_rechazos.data["value_text"].value = str(self.stats["rechazos_hoy"])
            self.card_advertencias.data["value_text"].value = str(self.stats["advertencias_hoy"])
            
            self.card_total.update()
            self.card_entradas.update()
            self.card_rechazos.update()
            self.card_advertencias.update()
            
            # Cargar últimos accesos
            await self.load_ultimos_accesos()
            
        except Exception as e:
            self.show_snackbar(f"Error cargando estadísticas: {e}", error=True)
    
    async def load_ultimos_accesos(self):
        """Cargar últimos 10 accesos"""
        try:
            resumen = await api_client.get_resumen_accesos()
            ultimos = resumen.get("ultimos_accesos", [])
            
            self.ultimos_accesos_list.controls.clear()
            
            for acceso in ultimos[:10]:
                resultado = acceso.get("resultado", "")
                
                if resultado == "permitido":
                    color = ft.Colors.GREEN
                    icon = ft.Icons.CHECK_CIRCLE
                elif resultado == "rechazado":
                    color = ft.Colors.RED
                    icon = ft.Icons.CANCEL
                else:
                    color = ft.Colors.ORANGE
                    icon = ft.Icons.WARNING
                
                self.ultimos_accesos_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(icon, color=color),
                            title=ft.Text(acceso.get("nombre_miembro", "")),
                            subtitle=ft.Text(
                                f"{acceso.get('numero_miembro', '')} - {acceso.get('fecha_hora', '')[:16]}"
                            ),
                            trailing=ft.Container(
                                content=ft.Text(
                                    resultado.upper(),
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE
                                ),
                                bgcolor=color,
                                padding=5,
                                border_radius=5
                            )
                        ),
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5
                    )
                )
            
            self.ultimos_accesos_list.update()
            
        except Exception as e:
            print(f"Error cargando últimos accesos: {e}")
    
    def toggle_scanner(self):
        """Activar/desactivar escáner"""
        if not self.escaneando:
            self.start_scanner()
        else:
            self.stop_scanner()
    
    def start_scanner(self):
        """Iniciar escáner QR"""
        self.escaneando = True
        self.show_snackbar("🟢 Escáner activado - Muestra el QR a la cámara")
        
        # Ocultar placeholder y mostrar cámara
        self.camera_placeholder.visible = False
        self.camera_image.visible = True
        
        # Mostrar guías de QR
        self.qr_guide.visible = True
        self.qr_instruction.visible = True
        self.qr_guide.update()
        self.qr_instruction.update()
        
        self.camera_preview.update()
        
        # Actualizar UI
        self.update_status_indicator("🟢 Activo - Escaneando...", ft.Colors.GREEN)
        
        # Iniciar bucle de escaneo
        self.page.run_task(self.scan_loop)
    
    def stop_scanner(self):
        """Detener escáner"""
        self.escaneando = False
        self.show_snackbar("⚫ Escáner detenido")
        
        # Mostrar placeholder y ocultar cámara
        self.camera_placeholder.visible = True
        self.camera_image.visible = False
        
        # Ocultar guías de QR
        self.qr_guide.visible = False
        self.qr_instruction.visible = False
        self.qr_guide.update()
        self.qr_instruction.update()
        
        self.camera_preview.update()
        
        self.update_status_indicator("⚫ Inactivo", ft.Colors.GREY)
    
    async def scan_loop(self):
        """Bucle principal de escaneo"""
        try:
            import cv2
            import base64
            from pyzbar import pyzbar
            
            # Abrir cámara
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.show_snackbar("Error: No se pudo acceder a la cámara", error=True)
                self.escaneando = False
                return
            
            while self.escaneando:
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Mostrar preview
                _, buffer = cv2.imencode('.jpg', frame)
                jpg_as_text = base64.b64encode(buffer).decode()
                self.camera_image.src_base64 = jpg_as_text
                self.camera_image.update()
                
                # Detectar QR
                barcodes = pyzbar.decode(frame)
                
                for barcode in barcodes:
                    qr_data = barcode.data.decode('utf-8')
                    
                    # Evitar escaneos duplicados
                    if qr_data != self.ultimo_qr and not self.validando:
                        self.ultimo_qr = qr_data
                        print(f"[QR DETECTADO] {qr_data}")
                        
                        # Validar QR
                        await self.validar_qr(qr_data)
                        
                        # Esperar 3 segundos antes del siguiente escaneo
                        await asyncio.sleep(3)
                        self.ultimo_qr = None
                
                await asyncio.sleep(0.1)  # 10 FPS
            
            # Liberar cámara
            cap.release()
            
        except ImportError:
            self.show_snackbar(
                "Error: Instala las dependencias: pip install opencv-python pyzbar",
                error=True
            )
            self.escaneando = False
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error en el escáner: {e}", error=True)
            self.escaneando = False
    
    async def validar_qr(self, qr_code: str):
        """Validar QR con el backend"""
        self.validando = True
        
        # Mostrar loading
        self.loading_indicator.visible = True
        self.status_text.value = "Validando..."
        self.status_text.visible = True
        self.loading_indicator.update()
        self.status_text.update()
        
        try:
            # Llamar al API
            response = await api_client.validar_acceso_qr(
                qr_code=qr_code,
                ubicacion="Entrada Principal"
            )
            
            # Mostrar resultado
            await self.mostrar_resultado(response)
            
            # Actualizar estadísticas
            await self.load_estadisticas()
            
            # Reproducir sonido según resultado
            self.play_sound(response.get("nivel_alerta", "error"))
            
        except Exception as e:
            self.mostrar_error(str(e))
        
        finally:
            self.loading_indicator.visible = False
            self.status_text.visible = False
            self.loading_indicator.update()
            self.status_text.update()
            self.validando = False
    
    async def mostrar_resultado(self, response: dict):
        """Mostrar resultado de la validación"""
        acceso_permitido = response.get("acceso_permitido", False)
        nivel_alerta = response.get("nivel_alerta", "error")
        mensaje = response.get("mensaje", "")
        miembro = response.get("miembro", {})
        
        # Color según resultado
        if nivel_alerta == "success":
            color = ft.Colors.GREEN
            icon = ft.Icons.CHECK_CIRCLE
            bgcolor = ft.Colors.GREEN_50
        elif nivel_alerta == "warning":
            color = ft.Colors.ORANGE
            icon = ft.Icons.WARNING
            bgcolor = ft.Colors.ORANGE_50
        else:
            color = ft.Colors.RED
            icon = ft.Icons.CANCEL
            bgcolor = ft.Colors.RED_50
        
        # Actualizar panel de resultado
        self.resultado_panel.content = ft.Column(
            [
                ft.Icon(icon, size=80, color=color),
                ft.Text(
                    "PERMITIDO" if acceso_permitido else "DENEGADO",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=10),
                ft.Text(
                    miembro.get("nombre_completo", ""),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    f"N°: {miembro.get('numero_miembro', '')}",
                    size=14,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    miembro.get("categoria", ""),
                    size=12,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=10),
                ft.Container(
                    content=ft.Text(
                        mensaje.replace("[OK]", "").replace("[WARN]", "").replace("[ERROR]", "").strip(),
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=bgcolor,
                    padding=10,
                    border_radius=8,
                    border=ft.border.all(2, color)
                ),
                ft.Divider(height=10),
                ft.Text(
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}",
                    size=11,
                    color=ft.Colors.GREY_600
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        )
        self.resultado_panel.bgcolor = bgcolor
        self.resultado_panel.update()
    
    def mostrar_error(self, error_msg: str):
        """Mostrar error en el panel"""
        self.resultado_panel.content = ft.Column(
            [
                ft.Icon(ft.Icons.ERROR, size=50, color=ft.Colors.RED),
                ft.Text(
                    "ERROR",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED
                ),
                ft.Divider(),
                ft.Text(
                    error_msg,
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.RED_700
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        self.resultado_panel.bgcolor = ft.Colors.RED_50
        self.resultado_panel.update()
    
    def update_status_indicator(self, text: str, color):
        """Actualizar indicador de estado"""
        # Buscar el Text con el data status_indicator en los controles
        for control in self.controls:
            if isinstance(control, ft.Row):
                for item in control.controls:
                    if isinstance(item, (ft.Container, ft.Column)):
                        self._find_and_update_status(item, text, color)
    
    def _find_and_update_status(self, container, text: str, color):
        """Buscar recursivamente el indicador de estado"""
        if hasattr(container, 'content'):
            content = container.content
            if isinstance(content, (ft.Column, ft.Row)):
                for control in content.controls:
                    if hasattr(control, 'controls'):
                        for subcontrol in control.controls:
                            if isinstance(subcontrol, ft.Text) and hasattr(subcontrol, 'data'):
                                if subcontrol.data and subcontrol.data.get("status_indicator"):
                                    subcontrol.value = text
                                    subcontrol.color = color
                                    subcontrol.update()
                                    return
                    self._find_and_update_status(control, text, color)
    
    def play_sound(self, nivel_alerta: str):
        """Reproducir sonido según resultado (opcional)"""
        # TODO: Implementar reproducción de sonidos
        # Para Windows: import winsound
        # Para multiplataforma: usar pygame o playsound
        pass
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()