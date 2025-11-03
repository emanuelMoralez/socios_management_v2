"""
Vista de Reportes
frontend-desktop/src/views/reportes_view.py
"""
import flet as ft
from src.services.api_client import api_client
from datetime import date, datetime, timedelta
import asyncio


class ReportesView(ft.Column):
    """Vista de reportes y estadísticas"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        # Contenedor de reporte actual
        self.reporte_container = ft.Container(
            expand=True,
            padding=20
        )
        
        # Construir UI
        self.build_ui()
    
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        # Cargar reporte por defecto
        self.load_reporte_socios()
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            # Título
            ft.Text(
                "Reportes y Estadísticas",
                size=24,
                weight=ft.FontWeight.BOLD
            ),
            
            ft.Divider(),
            
            # Selector de reportes
            ft.Container(
                content=ft.Row(
                    [
                        ft.ElevatedButton(
                            "Socios",
                            icon=ft.Icons.PEOPLE,
                            on_click=lambda _: self.load_reporte_socios()
                        ),
                        ft.ElevatedButton(
                            "Financiero",
                            icon=ft.Icons.ATTACH_MONEY,
                            on_click=lambda _: self.load_reporte_financiero()
                        ),
                        ft.ElevatedButton(
                            "Morosidad",
                            icon=ft.Icons.WARNING,
                            on_click=lambda _: self.load_reporte_morosidad()
                        ),
                        ft.ElevatedButton(
                            "Accesos",
                            icon=ft.Icons.DOOR_FRONT_DOOR,
                            on_click=lambda _: self.load_reporte_accesos()
                        ),
                    ],
                    spacing=10,
                    wrap=True
                ),
                bgcolor=ft.Colors.GREY_100,
                padding=15,
                border_radius=10
            ),
            
            ft.Divider(),
            
            # Contenedor de reporte
            self.reporte_container
        ]
        
        self.spacing = 10
        self.expand = True
    
    def load_reporte_socios(self):
        """Cargar reporte de socios"""
        self.page.run_task(self._load_reporte_socios)
    
    async def _load_reporte_socios(self):
        """Cargar reporte de socios (async)"""
        self.reporte_container.content = ft.Column(
            [ft.ProgressRing()],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.reporte_container.update()
        
        try:
            data = await api_client.get_reporte_socios()
            
            # Crear visualización
            self.reporte_container.content = ft.Column(
                [
                    ft.Text("Reporte de Socios", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # Resumen
                    ft.Row(
                        [
                            self._create_stat_box(
                                "Total Socios",
                                str(data.get("total", 0)),
                                ft.Icons.PEOPLE,
                                ft.Colors.BLUE
                            ),
                            self._create_stat_box(
                                "Activos",
                                str(data.get("activos", 0)),
                                ft.Icons.CHECK_CIRCLE,
                                ft.Colors.GREEN
                            ),
                            self._create_stat_box(
                                "Morosos",
                                str(data.get("morosos", 0)),
                                ft.Icons.WARNING,
                                ft.Colors.ORANGE
                            ),
                            self._create_stat_box(
                                "Suspendidos",
                                str(data.get("suspendidos", 0)),
                                ft.Icons.BLOCK,
                                ft.Colors.RED
                            ),
                        ],
                        spacing=10,
                        wrap=True
                    ),
                    
                    ft.Divider(height=30),
                    
                    # Por categoría
                    ft.Text("Distribución por Categoría", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self._create_categoria_chart(data.get("por_categoria", [])),
                    
                    ft.Divider(height=30),
                    
                    # Botón exportar
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Exportar a Excel",
                                icon=ft.Icons.FILE_DOWNLOAD,
                                on_click=lambda _: self.page.run_task(self.exportar_socios_excel),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
                                
                            ),
                            ft.ElevatedButton(
                                "Imprimir",
                                icon=ft.Icons.PRINT,
                                on_click=lambda _: self.show_snackbar("Imprimir próximamente")
                            ),
                        ],
                        spacing=10
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
            
        except Exception as e:
            self.reporte_container.content = ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED),
                    ft.Text(f"Error al cargar reporte: {e}", color=ft.Colors.RED)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        
        self.reporte_container.update()
    
    def load_reporte_financiero(self):
        """Cargar reporte financiero"""
        self.page.run_task(self._load_reporte_financiero)
    
    async def _load_reporte_financiero(self):
        """Cargar reporte financiero (async)"""
        self.reporte_container.content = ft.Column(
            [ft.ProgressRing()],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.reporte_container.update()
        
        try:
            # Calcular rango de fechas (último mes)
            fecha_hasta = date.today()
            fecha_desde = fecha_hasta - timedelta(days=30)
            
            data = await api_client.get_reporte_financiero(
                fecha_desde=fecha_desde.isoformat(),
                fecha_hasta=fecha_hasta.isoformat()
            )
            
            # Crear visualización
            self.reporte_container.content = ft.Column(
                [
                    ft.Text("Reporte Financiero", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Divider(),
                    
                    # Resumen financiero
                    ft.Row(
                        [
                            self._create_stat_box(
                                "Total Ingresos",
                                f"${data.get('total_ingresos', 0):,.2f}",
                                ft.Icons.TRENDING_UP,
                                ft.Colors.GREEN
                            ),
                            self._create_stat_box(
                                "Total Egresos",
                                f"${data.get('total_egresos', 0):,.2f}",
                                ft.Icons.TRENDING_DOWN,
                                ft.Colors.RED
                            ),
                            self._create_stat_box(
                                "Balance",
                                f"${data.get('balance', 0):,.2f}",
                                ft.Icons.ACCOUNT_BALANCE,
                                ft.Colors.BLUE
                            ),
                        ],
                        spacing=10,
                        wrap=True
                    ),
                    
                    ft.Divider(height=30),
                    
                    # Detalles
                    ft.Text("Detalle de Ingresos", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self._create_ingresos_table(data.get("ingresos_detalle", [])),
                    
                    ft.Divider(height=30),
                    
                    # Botones
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Exportar a Excel",
                                icon=ft.Icons.FILE_DOWNLOAD,
                                on_click=lambda _: self.page.run_task(
                                    self.exportar_pagos_excel,
                                    fecha_desde.isoformat(),
                                    fecha_hasta.isoformat()
                                ),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
                            ),
                        ]
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
            
        except Exception as e:
            self.reporte_container.content = ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED),
                    ft.Text(f"Error: {e}", color=ft.Colors.RED)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        
        self.reporte_container.update()
    
    def load_reporte_morosidad(self):
        """Cargar reporte de morosidad"""
        self.page.run_task(self._load_reporte_morosidad)
    
    async def _load_reporte_morosidad(self):
        """Cargar reporte de morosidad (async)"""
        self.reporte_container.content = ft.Column(
            [ft.ProgressRing()],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.reporte_container.update()
        
        try:
            data = await api_client.get_reporte_morosidad()
            
            morosos = data.get("morosos", [])
            total_deuda = sum(m.get("deuda", 0) for m in morosos)
            
            self.reporte_container.content = ft.Column(
                [
                    ft.Text("Reporte de Morosidad", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # Resumen
                    ft.Row(
                        [
                            self._create_stat_box(
                                "Socios Morosos",
                                str(len(morosos)),
                                ft.Icons.WARNING,
                                ft.Colors.RED
                            ),
                            self._create_stat_box(
                                "Deuda Total",
                                f"${total_deuda:,.2f}",
                                ft.Icons.ATTACH_MONEY,
                                ft.Colors.ORANGE
                            ),
                        ],
                        spacing=10
                    ),
                    
                    ft.Divider(height=30),
                    
                    # Tabla de morosos
                    ft.Text("Lista de Socios Morosos", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self._create_morosos_table(morosos),
                    
                    ft.Divider(height=30),
                    
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Exportar Lista",
                                icon=ft.Icons.FILE_DOWNLOAD,
                                on_click=lambda _: self.page.run_task(self.exportar_morosidad_excel),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
                            ),
                            ft.ElevatedButton(
                                "Enviar Recordatorios",
                                icon=ft.Icons.EMAIL,
                                on_click=lambda _: self.page.run_task(self.enviar_recordatorios_masivos),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700)
                            ),
                        ],
                        spacing=10
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
            
        except Exception as e:
            self.reporte_container.content = ft.Column(
                [
                    ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED),
                    ft.Text(f"Error: {e}", color=ft.Colors.RED)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        
        self.reporte_container.update()
    
    def load_reporte_accesos(self):
        """Cargar reporte de accesos completo"""
        async def load_data():
            try:
                # Obtener estadísticas y resumen
                estadisticas = await api_client.obtener_estadisticas_accesos()
                resumen = await api_client.obtener_resumen_accesos()
                
                # Obtener historial reciente (últimos 50)
                historial = await api_client.obtener_historial_accesos(
                    page=1,
                    page_size=50
                )
                
                # Crear contenido del reporte
                self.reporte_container.content = ft.Column(
                    [
                        # Título
                        ft.Row(
                            [
                                ft.Text(
                                    "📊 Reporte de Accesos",
                                    size=24,
                                    weight=ft.FontWeight.BOLD
                                ),
                                ft.Container(expand=True),
                                ft.ElevatedButton(
                                    "Exportar a Excel",
                                    icon=ft.icons.FILE_DOWNLOAD,
                                    on_click=lambda _: self.exportar_accesos_excel()
                                ),
                            ]
                        ),
                        
                        ft.Divider(),
                        
                        # Cards de estadísticas
                        ft.Text("Estadísticas del Día", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                self._create_stat_box(
                                    "Total Hoy",
                                    str(estadisticas.get("total_hoy", 0)),
                                    ft.icons.PEOPLE,
                                    ft.Colors.BLUE
                                ),
                                self._create_stat_box(
                                    "Permitidos",
                                    str(estadisticas.get("entradas_hoy", 0)),
                                    ft.icons.CHECK_CIRCLE,
                                    ft.Colors.GREEN
                                ),
                                self._create_stat_box(
                                    "Rechazados",
                                    str(estadisticas.get("rechazos_hoy", 0)),
                                    ft.icons.CANCEL,
                                    ft.Colors.RED
                                ),
                                self._create_stat_box(
                                    "Advertencias",
                                    str(estadisticas.get("advertencias_hoy", 0)),
                                    ft.icons.WARNING,
                                    ft.Colors.ORANGE
                                ),
                            ],
                            spacing=10,
                        ),
                        
                        ft.Container(height=20),
                        
                        # Resumen por período
                        ft.Text("Resumen por Período", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                self._create_info_card(
                                    "Esta Semana",
                                    str(resumen.get("semana", 0)),
                                    ft.icons.DATE_RANGE,
                                    ft.Colors.PURPLE
                                ),
                                self._create_info_card(
                                    "Este Mes",
                                    str(resumen.get("mes", 0)),
                                    ft.icons.CALENDAR_MONTH,
                                    ft.Colors.INDIGO
                                ),
                                self._create_info_card(
                                    "Promedio/Hora",
                                    f"{estadisticas.get('promedio_por_hora', 0):.1f}",
                                    ft.icons.SCHEDULE,
                                    ft.Colors.TEAL
                                ),
                            ],
                            spacing=10,
                        ),
                        
                        ft.Container(height=20),
                        
                        # Gráfico de accesos por hora
                        ft.Text("Accesos por Hora (Hoy)", size=18, weight=ft.FontWeight.BOLD),
                        self._create_accesos_chart(estadisticas.get("accesos_por_hora", [])),
                        
                        ft.Container(height=20),
                        
                        # Historial reciente
                        ft.Text("Historial Reciente", size=18, weight=ft.FontWeight.BOLD),
                        self._create_historial_accesos_table(historial.get("items", [])),
                        
                        # Filtros (para futuras mejoras)
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.icons.INFO_OUTLINE, color=ft.Colors.BLUE),
                                    ft.Text(
                                        "Mostrando últimos 50 accesos. "
                                        "Use 'Exportar a Excel' para reporte completo.",
                                        size=12,
                                        color=ft.Colors.GREY_600
                                    ),
                                ],
                                spacing=5
                            ),
                            padding=10,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=5,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10
                )
                
                self.reporte_container.update()
                
            except Exception as e:
                self.show_snackbar(f"Error al cargar accesos: {str(e)}", error=True)
        
        self.page.run_task(load_data)
    
    def _create_stat_box(self, title: str, value: str, icon, color):
        """Crear caja de estadística"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(title, size=12, color=ft.Colors.GREY_600),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=20,
            border=ft.border.all(2, color),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
    
    def _create_categoria_chart(self, categorias: list):
        """Crear gráfico de categorías"""
        if not categorias:
            return ft.Text("No hay datos", color=ft.Colors.GREY_600)
        
        rows = []
        for cat in categorias:
            nombre = cat.get("nombre", "Sin categoría")
            cantidad = cat.get("cantidad", 0)
            
            rows.append(
                ft.Row(
                    [
                        ft.Text(nombre, size=14, expand=True),
                        ft.Container(
                            content=ft.Text(
                                str(cantidad),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE
                            ),
                            bgcolor=ft.Colors.BLUE,
                            padding=10,
                            border_radius=5,
                            width=60,
                            alignment=ft.alignment.center
                        )
                    ],
                    spacing=10
                )
            )
        
        return ft.Column(rows, spacing=10)
    
    def _create_ingresos_table(self, ingresos: list):
        """Crear tabla de ingresos"""
        if not ingresos:
            return ft.Text("No hay datos", color=ft.Colors.GREY_600)
        
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Concepto")),
                ft.DataColumn(ft.Text("Cantidad")),
                ft.DataColumn(ft.Text("Monto Total")),
            ],
            rows=[]
        )
        
        for ingreso in ingresos:
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(ingreso.get("concepto", ""))),
                        ft.DataCell(ft.Text(str(ingreso.get("cantidad", 0)))),
                        ft.DataCell(
                            ft.Text(
                                f"${ingreso.get('total', 0):,.2f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN
                            )
                        ),
                    ]
                )
            )
        
        return ft.Container(
            content=table,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=10
        )
    
    def _create_morosos_table(self, morosos: list):
        """Crear tabla de morosos"""
        if not morosos:
            return ft.Text("No hay socios morosos", color=ft.Colors.GREEN)
        
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° Socio")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Deuda")),
                ft.DataColumn(ft.Text("Días Mora")),
            ],
            rows=[]
        )
        
        for moroso in morosos[:20]:  # Limitar a 20
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(moroso.get("numero_miembro", ""))),
                        ft.DataCell(ft.Text(moroso.get("nombre_completo", ""))),
                        ft.DataCell(
                            ft.Text(
                                f"${moroso.get('deuda', 0):,.2f}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.RED
                            )
                        ),
                        ft.DataCell(ft.Text(str(moroso.get("dias_mora", 0)))),
                    ]
                )
            )
        
        # Crear lista de controles
        controles = [table]

        # Solo agregar el texto si hay más de 20
        if len(morosos) > 20:
            controles.append(
                ft.Text(
                    f"Mostrando {min(20, len(morosos))} de {len(morosos)} socios",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            )

        return ft.Container(
            content=ft.Column(
                controles,
                scroll=ft.ScrollMode.AUTO                    
            ),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            padding=10,
            height=400
        )
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()

    # ============================================================================
    # MÉTODOS DE EXPORTACIÓN
    # ============================================================================

    async def exportar_socios_excel(self):
        """Exportar socios a Excel"""
        try:
            # Mostrar loading
            loading_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.ProgressRing(width=30, height=30),
                        ft.Text("Exportando a Excel...")
                    ],
                    spacing=10
                ),
                content=ft.Text("Por favor espera mientras se genera el archivo...")
            )
            
            self.page.overlay.append(loading_dialog)
            loading_dialog.open = True
            self.page.update()
            
            # Obtener archivo Excel del backend
            excel_bytes = await api_client.exportar_socios_excel()
            
            # Cerrar loading
            loading_dialog.open = False
            self.page.update()
            
            # Guardar archivo
            filename = f"socios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Usar file picker para guardar
            save_file_picker = ft.FilePicker(
                on_result=lambda e: self.on_export_save(e, excel_bytes)
            )
            self.page.overlay.append(save_file_picker)
            self.page.update()
            
            save_file_picker.save_file(
                file_name=filename,
                allowed_extensions=["xlsx"],
                dialog_title="Guardar reporte de socios"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error al exportar: {e}", error=True)

    async def exportar_pagos_excel(self, fecha_desde=None, fecha_hasta=None):
        """Exportar pagos a Excel"""
        try:
            loading_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.ProgressRing(width=30, height=30),
                        ft.Text("Exportando pagos...")
                    ],
                    spacing=10
                ),
                content=ft.Text("Generando archivo Excel...")
            )
            
            self.page.overlay.append(loading_dialog)
            loading_dialog.open = True
            self.page.update()
            
            # Obtener archivo
            excel_bytes = await api_client.exportar_pagos_excel(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            loading_dialog.open = False
            self.page.update()
            
            # Guardar
            filename = f"pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            save_file_picker = ft.FilePicker(
                on_result=lambda e: self.on_export_save(e, excel_bytes)
            )
            self.page.overlay.append(save_file_picker)
            self.page.update()
            
            save_file_picker.save_file(
                file_name=filename,
                allowed_extensions=["xlsx"],
                dialog_title="Guardar reporte de pagos"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error al exportar: {e}", error=True)

    async def exportar_morosidad_excel(self):
        """Exportar reporte de morosidad a Excel"""
        try:
            loading_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.ProgressRing(width=30, height=30),
                        ft.Text("Exportando morosidad...")
                    ],
                    spacing=10
                ),
                content=ft.Text("Generando archivo Excel...")
            )
            
            self.page.overlay.append(loading_dialog)
            loading_dialog.open = True
            self.page.update()
            
            excel_bytes = await api_client.exportar_morosidad_excel()
            
            loading_dialog.open = False
            self.page.update()
            
            filename = f"morosidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            save_file_picker = ft.FilePicker(
                on_result=lambda e: self.on_export_save(e, excel_bytes)
            )
            self.page.overlay.append(save_file_picker)
            self.page.update()
            
            save_file_picker.save_file(
                file_name=filename,
                allowed_extensions=["xlsx"],
                dialog_title="Guardar reporte de morosidad"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error al exportar: {e}", error=True)

    def on_export_save(self, e: ft.FilePickerResultEvent, excel_bytes: bytes):
        """Callback cuando se guarda el archivo exportado"""
        if e.path:
            try:
                with open(e.path, 'wb') as f:
                    f.write(excel_bytes)
                
                self.show_snackbar(f"✓ Archivo guardado: {e.path}")
                
            except Exception as ex:
                self.show_snackbar(f"Error al guardar archivo: {ex}", error=True)
        else:
            # Usuario canceló
            pass

    # ============================================================================
    # MÉTODOS DE NOTIFICACIONES
    # ============================================================================

    async def enviar_recordatorios_masivos(self):
        """Enviar recordatorios de cuota masivos"""
        
        # Campos de configuración
        solo_morosos = ft.Checkbox(
            label="Solo socios en estado MOROSO",
            value=True
        )
        
        dias_mora_field = ft.TextField(
            label="Días mínimos de mora",
            value="5",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200,
            hint_text="Ej: 5"
        )
        
        async def confirmar_envio(e):
            try:
                dias_mora = int(dias_mora_field.value or 5)
                
                if dias_mora < 0:
                    self.show_snackbar("Los días de mora deben ser positivos", error=True)
                    return
                
                # Confirmar acción
                confirmar_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        [
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=30),
                            ft.Text("Confirmar Envío Masivo")
                        ],
                        spacing=10
                    ),
                    content=ft.Text(
                        "¿Estás seguro de enviar recordatorios a TODOS los socios que cumplan los criterios?\n\n"
                        "Esta acción enviará emails automáticos.",
                        size=14
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: setattr(confirmar_dialog, 'open', False) or self.page.update()),
                        ft.ElevatedButton(
                            "Confirmar y Enviar",
                            icon=ft.Icons.SEND,
                            on_click=lambda _: self.page.run_task(procesar_envio, confirmar_dialog),
                            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700)
                        )
                    ]
                )
                
                self.page.overlay.append(confirmar_dialog)
                confirmar_dialog.open = True
                self.page.update()
                
            except ValueError:
                self.show_snackbar("Ingresa un número válido de días", error=True)
        
        async def procesar_envio(confirmar_dialog):
            # Cerrar diálogo de confirmación
            confirmar_dialog.open = False
            config_dialog.open = False
            self.page.update()
            
            # Mostrar loading
            loading_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    [
                        ft.ProgressRing(width=30, height=30),
                        ft.Text("Enviando recordatorios...")
                    ],
                    spacing=10
                ),
                content=ft.Text("Por favor espera, esto puede tomar unos momentos...")
            )
            
            self.page.overlay.append(loading_dialog)
            loading_dialog.open = True
            self.page.update()
            
            try:
                dias_mora = int(dias_mora_field.value or 5)
                
                # Llamar al API
                resultado = await api_client.enviar_recordatorios_masivos(
                    solo_morosos=solo_morosos.value,
                    dias_mora_minimo=dias_mora
                )
                
                loading_dialog.open = False
                self.page.update()
                
                # Mostrar resultado
                resultado_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=30),
                            ft.Text("Resultado del Envío")
                        ],
                        spacing=10
                    ),
                    content=ft.Column(
                        [
                            ft.Text(
                                f"✓ Recordatorios programados: {resultado.get('enviados', 0)}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN
                            ),
                            ft.Text(
                                f"✗ Fallidos: {resultado.get('fallidos', 0)}",
                                size=14,
                                color=ft.Colors.RED if resultado.get('fallidos', 0) > 0 else ft.Colors.GREY
                            ),
                            ft.Divider(),
                            ft.Text(
                                "Los emails se están enviando en segundo plano.",
                                size=12,
                                color=ft.Colors.GREY_700
                            )
                        ],
                        spacing=10,
                        tight=True
                    ),
                    actions=[
                        ft.TextButton(
                            "Cerrar",
                            on_click=lambda _: setattr(resultado_dialog, 'open', False) or self.page.update()
                        )
                    ]
                )
                
                self.page.overlay.append(resultado_dialog)
                resultado_dialog.open = True
                self.page.update()
                
                self.show_snackbar(f"✓ {resultado.get('enviados', 0)} recordatorios programados")
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                loading_dialog.open = False
                self.page.update()
                self.show_snackbar(f"Error: {ex}", error=True)
        
        def cerrar_config(e):
            config_dialog.open = False
            self.page.update()
        
        # Diálogo de configuración
        config_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("📧 Enviar Recordatorios Masivos"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Text(
                                "ℹ️ Esta función enviará recordatorios de cuota por email "
                                "a todos los socios que cumplan los criterios.",
                                size=12,
                                color=ft.Colors.GREY_700
                            ),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=10,
                            border_radius=5
                        ),
                        ft.Divider(),
                        ft.Text("Configuración", weight=ft.FontWeight.BOLD),
                        solo_morosos,
                        dias_mora_field,
                        ft.Divider(),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "⚠️ Requisitos:",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.ORANGE_700
                                    ),
                                    ft.Text("• Los socios deben tener email registrado", size=11),
                                    ft.Text("• Los socios deben tener deuda", size=11),
                                    ft.Text("• La configuración SMTP debe estar activa", size=11),
                                ],
                                spacing=3
                            ),
                            bgcolor=ft.Colors.ORANGE_50,
                            padding=10,
                            border_radius=5
                        )
                    ],
                    spacing=10
                ),
                width=450,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_config),
                ft.ElevatedButton(
                    "Enviar Recordatorios",
                    icon=ft.Icons.SEND,
                    on_click=lambda e: self.page.run_task(confirmar_envio, e),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(config_dialog)
        config_dialog.open = True
        self.page.update()
    
    def _create_info_card(self, title: str, value: str, icon, color):
        """Crear card de información"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=30, color=color),
                    ft.Column(
                        [
                            ft.Text(title, size=12, color=ft.Colors.GREY_600),
                            ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=2
                    ),
                ],
                spacing=10
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
    
    def _create_accesos_chart(self, accesos_por_hora: list):
        """Crear gráfico de accesos por hora"""
        if not accesos_por_hora:
            return ft.Text("No hay datos", color=ft.Colors.GREY_600)
        
        # Encontrar el máximo para escalar
        max_accesos = max([h.get("cantidad", 0) for h in accesos_por_hora], default=1)
        
        # Crear barras
        bars = []
        for hora_data in accesos_por_hora:
            hora = hora_data.get("hora", "00:00")
            cantidad = hora_data.get("cantidad", 0)
            
            # Solo mostrar horas con actividad o cada 3 horas
            hora_num = int(hora.split(":")[0])
            if cantidad > 0 or hora_num % 3 == 0:
                # Altura relativa
                altura = max(20, (cantidad / max_accesos * 200)) if max_accesos > 0 else 20
                
                bars.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        str(cantidad) if cantidad > 0 else "",
                                        size=10,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    alignment=ft.alignment.center
                                ),
                                ft.Container(
                                    bgcolor=ft.Colors.BLUE_400 if cantidad > 0 else ft.Colors.GREY_300,
                                    height=altura,
                                    width=30,
                                    border_radius=3,
                                ),
                                ft.Text(hora, size=9, color=ft.Colors.GREY_600),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2
                        ),
                        padding=2
                    )
                )
        
        return ft.Container(
            content=ft.Row(
                bars,
                scroll=ft.ScrollMode.AUTO,
                spacing=5
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            bgcolor=ft.Colors.WHITE,
            height=280
        )
    
    def _create_historial_accesos_table(self, accesos: list):
        """Crear tabla de historial de accesos"""
        if not accesos:
            return ft.Text("No hay accesos registrados", color=ft.Colors.GREY_600)
        
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha/Hora")),
                ft.DataColumn(ft.Text("Socio")),
                ft.DataColumn(ft.Text("N° Socio")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Resultado")),
                ft.DataColumn(ft.Text("Ubicación")),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
        )
        
        for acceso in accesos[:30]:  # Limitar a 30
            # Formatear fecha
            try:
                fecha_str = acceso.get("fecha_hora", "")
                if "T" in fecha_str:
                    fecha_obj = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                    fecha_formateada = fecha_obj.strftime("%d/%m %H:%M")
                else:
                    fecha_formateada = fecha_str[:16]
            except:
                fecha_formateada = fecha_str[:16] if fecha_str else "-"
            
            # Color según resultado
            resultado = acceso.get("resultado", "")
            if resultado == "permitido":
                color_resultado = ft.Colors.GREEN
                icon_resultado = "✓"
            elif resultado == "rechazado":
                color_resultado = ft.Colors.RED
                icon_resultado = "✗"
            else:  # advertencia
                color_resultado = ft.Colors.ORANGE
                icon_resultado = "⚠"
            
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(fecha_formateada, size=12)),
                        ft.DataCell(
                            ft.Text(
                                acceso.get("nombre_miembro", "Desconocido"),
                                size=12
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                acceso.get("numero_miembro", "-"),
                                size=12,
                                weight=ft.FontWeight.BOLD
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                acceso.get("tipo_acceso", "").upper(),
                                size=11
                            )
                        ),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.Text(icon_resultado, color=color_resultado),
                                    ft.Text(
                                        resultado.capitalize(),
                                        size=12,
                                        color=color_resultado,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ],
                                spacing=3
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                acceso.get("ubicacion", "-"),
                                size=11,
                                color=ft.Colors.GREY_600
                            )
                        ),
                    ]
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    table,
                    ft.Text(
                        f"Mostrando {min(30, len(accesos))} de {len(accesos)} accesos",
                        size=11,
                        color=ft.Colors.GREY_600
                    ) if len(accesos) > 30 else None
                ],
                spacing=5
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            bgcolor=ft.Colors.WHITE,
        )
    
    async def exportar_accesos_excel(self):
        """Exportar accesos a Excel"""
        try:
            # Obtener datos del backend
            excel_bytes = await api_client.exportar_accesos_excel()
            
            # Guardar archivo usando FilePicker
            filename = f"accesos_{date.today().strftime('%Y%m%d')}.xlsx"
            
            save_file_picker = ft.FilePicker(
                on_result=lambda e: self.on_export_save(e, excel_bytes)
            )
            self.page.overlay.append(save_file_picker)
            self.page.update()
            
            save_file_picker.save_file(
                file_name=filename,
                allowed_extensions=["xlsx"],
                dialog_title="Guardar reporte de accesos"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_snackbar(f"Error al exportar: {str(e)}", error=True)