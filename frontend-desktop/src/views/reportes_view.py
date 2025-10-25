"""
Vista de Reportes
frontend-desktop/src/views/reportes_view.py
"""
import flet as ft
from src.services.api_client import api_client
from datetime import date, datetime, timedelta


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
                                "Exportar",
                                icon=ft.Icons.FILE_DOWNLOAD,
                                on_click=lambda _: self.show_snackbar("Exportar próximamente")
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
                                on_click=lambda _: self.show_snackbar("Exportar próximamente")
                            ),
                            ft.ElevatedButton(
                                "Enviar Recordatorios",
                                icon=ft.Icons.EMAIL,
                                on_click=lambda _: self.show_snackbar("Enviar recordatorios próximamente")
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
        """Cargar reporte de accesos"""
        self.reporte_container.content = ft.Column(
            [
                ft.Text("Reporte de Accesos", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("Próximamente", size=16, color=ft.Colors.GREY_600),
            ]
        )
        self.reporte_container.update()
    
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