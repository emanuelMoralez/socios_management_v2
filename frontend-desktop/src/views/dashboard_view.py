"""
Vista de Dashboard Principal
frontend-desktop/src/views/dashboard_view.py
"""
import flet as ft
from src.services.api_client import api_client
from datetime import datetime, date, timedelta


class DashboardView(ft.Column):
    """Dashboard principal con KPIs y estadísticas"""
    
    def __init__(self, page: ft.Page, user: dict = None, on_logout=None, navigate_callback=None):
        super().__init__()
        self.page = page
        self.user = user
        self.on_logout = on_logout
        self.navigate_callback = navigate_callback
        
        # Contenedores para datos dinámicos
        self.kpi_socios = None
        self.kpi_ingresos = None
        self.kpi_morosidad = None
        self.kpi_accesos = None
        self.alertas_container = None
        self.grafico_ingresos = None
        self.grafico_accesos = None
        
        # Construir UI
        self.build_ui()
    
    def build_ui(self):
        """Construir interfaz del dashboard"""
        
        # Header compacto con título y botón de refresh
        header = ft.Row(
            [
                ft.Text(
                    "📊 Dashboard",
                    size=24,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    size=12,
                    color=ft.Colors.GREY_600
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Actualizar",
                    on_click=lambda _: self.load_dashboard_data(),
                    icon_color=ft.Colors.BLUE,
                    icon_size=20
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # KPIs principales (más compactos)
        self.kpi_socios = self._create_kpi_skeleton()
        self.kpi_ingresos = self._create_kpi_skeleton()
        self.kpi_morosidad = self._create_kpi_skeleton()
        self.kpi_accesos = self._create_kpi_skeleton()
        
        kpis_row = ft.Row(
            [
                self.kpi_socios,
                self.kpi_ingresos,
                self.kpi_morosidad,
                self.kpi_accesos,
            ],
            spacing=10,
            wrap=False
        )
        
        # Gráficos más compactos
        self.grafico_ingresos = ft.Container(
            content=ft.Column(
                [ft.ProgressRing(width=30, height=30)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
            height=280
        )
        
        self.grafico_accesos = ft.Container(
            content=ft.Column(
                [ft.ProgressRing(width=30, height=30)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
            height=280
        )
        
        graficos_row = ft.Row(
            [
                self.grafico_ingresos,
                self.grafico_accesos,
            ],
            spacing=10
        )
        
        # Alertas y acciones rápidas (más compactas)
        self.alertas_container = ft.Container(
            content=ft.Column(
                [ft.ProgressRing(width=30, height=30)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
            height=280
        )
        
        acciones_rapidas = self._create_acciones_rapidas()
        
        bottom_row = ft.Row(
            [
                self.alertas_container,
                acciones_rapidas,
            ],
            spacing=10
        )
        
        # Ensamblar todo con menos espaciado
        self.controls = [
            header,
            ft.Divider(height=1),
            kpis_row,
            graficos_row,
            bottom_row,
        ]
        
        self.spacing = 15
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
    
    def load_dashboard_data(self):
        """Cargar datos del dashboard"""
        self.page.run_task(self._load_dashboard_data)
    
    async def _load_dashboard_data(self):
        """Cargar datos del dashboard (async)"""
        try:
            # Cargar datos del dashboard
            dashboard_data = await api_client.get_dashboard()
            
            # Actualizar KPIs
            self._update_kpis(dashboard_data)
            
            # Actualizar gráficos
            await self._update_graficos(dashboard_data)
            
            # Actualizar alertas
            await self._update_alertas()
            
        except Exception as e:
            self.show_error(f"Error al cargar dashboard: {e}")
    
    def _update_kpis(self, data: dict):
        """Actualizar KPIs con datos del servidor"""
        socios_data = data.get("socios", {})
        finanzas_data = data.get("finanzas_mes", {})
        accesos_data = data.get("accesos", {})
        
        # KPI Socios
        total_socios = socios_data.get("total", 0)
        activos = socios_data.get("activos", 0)
        porcentaje_activos = (activos / total_socios * 100) if total_socios > 0 else 0
        
        self.kpi_socios.content = self._create_kpi_content(
            titulo="Socios",
            valor=str(total_socios),
            subtitulo=f"{activos} activos ({porcentaje_activos:.1f}%)",
            icono=ft.Icons.PEOPLE,
            color=ft.Colors.BLUE,
            tendencia="up" if porcentaje_activos > 80 else "neutral"
        )
        
        # KPI Ingresos
        ingresos = finanzas_data.get("ingresos", 0)
        balance = finanzas_data.get("balance", 0)
        
        self.kpi_ingresos.content = self._create_kpi_content(
            titulo="Ingresos del Mes",
            valor=f"${ingresos:,.0f}",
            subtitulo=f"Balance: ${balance:,.0f}",
            icono=ft.Icons.ATTACH_MONEY,
            color=ft.Colors.GREEN,
            tendencia="up" if balance > 0 else "down"
        )
        
        # KPI Morosidad
        morosos = socios_data.get("morosos", 0)
        porcentaje_morosos = socios_data.get("porcentaje_morosos", 0)
        
        self.kpi_morosidad.content = self._create_kpi_content(
            titulo="Morosidad",
            valor=str(morosos),
            subtitulo=f"{porcentaje_morosos:.1f}% del total",
            icono=ft.Icons.WARNING,
            color=ft.Colors.ORANGE if morosos > 0 else ft.Colors.GREEN,
            tendencia="down" if porcentaje_morosos < 10 else "up"
        )
        
        # KPI Accesos
        accesos_hoy = accesos_data.get("hoy", 0)
        
        self.kpi_accesos.content = self._create_kpi_content(
            titulo="Accesos Hoy",
            valor=str(accesos_hoy),
            subtitulo=datetime.now().strftime("%d/%m/%Y"),
            icono=ft.Icons.DOOR_FRONT_DOOR,
            color=ft.Colors.PURPLE,
            tendencia="neutral"
        )
        
        # Actualizar todos los KPIs
        self.kpi_socios.update()
        self.kpi_ingresos.update()
        self.kpi_morosidad.update()
        self.kpi_accesos.update()
    
    async def _update_graficos(self, data: dict):
        """Actualizar gráficos con datos reales"""
        
        # Gráfico de ingresos (datos históricos reales)
        try:
            historico_data = await api_client.get_ingresos_historicos(meses=6)
            historico = historico_data.get("historico", [])
            
            meses = [h.get("mes") for h in historico]
            valores_ingresos = [h.get("ingresos", 0) for h in historico]
            
            self.grafico_ingresos.content = self._create_bar_chart(
                titulo="Ingresos Últimos 6 Meses",
                categorias=meses,
                valores=valores_ingresos,
                color=ft.Colors.GREEN,
                formato_valor="$"
            )
            self.grafico_ingresos.update()
            
        except Exception as e:
            self.grafico_ingresos.content = ft.Text(
                f"Error al cargar ingresos: {e}",
                color=ft.Colors.RED
            )
            self.grafico_ingresos.update()
        
        # Gráfico de accesos (datos reales por hora)
        try:
            accesos_data = await api_client.get_accesos_detallados()
            accesos_por_hora = accesos_data.get("accesos_por_hora", [])
            estadisticas = accesos_data.get("estadisticas", {})
            
            # Filtrar solo horas con actividad o cada 3 horas
            horas = []
            cantidades = []
            
            for hora_data in accesos_por_hora:
                hora = hora_data.get("hora", "00:00")
                total = hora_data.get("total", 0)
                hora_num = int(hora.split(":")[0])
                
                # Mostrar si hay actividad o cada 3 horas
                if total > 0 or hora_num % 3 == 0:
                    horas.append(hora)
                    cantidades.append(total)
            
            # Crear gráfico con información adicional de hora pico
            grafico_content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Accesos por Horario (Hoy)",
                                size=16,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(
                                    f"🔥 Pico: {estadisticas.get('hora_pico', 'N/A')} ({estadisticas.get('accesos_hora_pico', 0)} accesos)",
                                    size=11,
                                    color=ft.Colors.ORANGE
                                ),
                                bgcolor=ft.Colors.ORANGE_50,
                                padding=8,
                                border_radius=5
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(height=1),
                    ft.Row(
                        self._create_bar_elements(horas, cantidades, ft.Colors.BLUE),
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO,
                        alignment=ft.MainAxisAlignment.START
                    )
                ],
                spacing=10
            )
            
            self.grafico_accesos.content = grafico_content
            self.grafico_accesos.update()
            
        except Exception as e:
            self.grafico_accesos.content = ft.Text(
                f"Error al cargar accesos: {e}",
                color=ft.Colors.RED
            )
            self.grafico_accesos.update()
    
    async def _update_alertas(self):
        """Actualizar panel de alertas"""
        try:
            # Obtener datos de morosidad
            morosidad_data = await api_client.get_reporte_morosidad()
            morosos = morosidad_data.get("morosos", [])
            
            # Top 5 morosos con mayor deuda
            top_morosos = sorted(morosos, key=lambda x: x.get("deuda", 0), reverse=True)[:5]
            
            alertas = []
            
            # Alerta de morosidad
            if len(morosos) > 0:
                alertas.append(
                    self._create_alerta(
                        titulo="⚠️ Socios Morosos",
                        descripcion=f"{len(morosos)} socios con deudas pendientes",
                        color=ft.Colors.ORANGE,
                        accion_texto="Ver Detalles",
                        accion=lambda: self.navigate_to("reportes")
                    )
                )
            
            # Alertas de top morosos
            for moroso in top_morosos[:3]:
                alertas.append(
                    self._create_alerta_compacta(
                        f"{moroso.get('nombre_completo', 'N/A')}",
                        f"Deuda: ${moroso.get('deuda', 0):,.2f}",
                        ft.Colors.RED_100
                    )
                )
            
            # Si no hay alertas
            if not alertas:
                alertas.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.CHECK_CIRCLE, size=60, color=ft.Colors.GREEN),
                                ft.Text(
                                    "¡Todo en orden!",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN
                                ),
                                ft.Text("No hay alertas pendientes", color=ft.Colors.GREY_600)
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10
                        ),
                        padding=20
                    )
                )
            
            self.alertas_container.content = ft.Column(
                [
                    ft.Text("🔔 Alertas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    *alertas
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            )
            self.alertas_container.update()
            
        except Exception as e:
            self.alertas_container.content = ft.Text(
                f"Error al cargar alertas: {e}",
                color=ft.Colors.RED
            )
            self.alertas_container.update()
    
    def _create_kpi_skeleton(self):
        """Crear skeleton loader para KPI (compacto)"""
        return ft.Container(
            content=ft.Column(
                [ft.ProgressRing(width=16, height=16)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
            height=110
        )
    
    def _create_kpi_content(
        self,
        titulo: str,
        valor: str,
        subtitulo: str,
        icono,
        color,
        tendencia: str = "neutral"
    ):
        """Crear contenido de KPI (compacto)"""
        # Icono de tendencia (más pequeño)
        if tendencia == "up":
            tendencia_icon = ft.Icon(ft.Icons.TRENDING_UP, color=ft.Colors.GREEN, size=16)
        elif tendencia == "down":
            tendencia_icon = ft.Icon(ft.Icons.TRENDING_DOWN, color=ft.Colors.RED, size=16)
        else:
            tendencia_icon = ft.Icon(ft.Icons.REMOVE, color=ft.Colors.GREY, size=16)
        
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icono, size=32, color=color),
                        ft.Container(expand=True),
                        tendencia_icon
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Text(titulo, size=12, color=ft.Colors.GREY_600),
                ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(subtitulo, size=10, color=ft.Colors.GREY_500),
            ],
            spacing=3
        )
    
    def _create_bar_chart(
        self,
        titulo: str,
        categorias: list,
        valores: list,
        color,
        formato_valor: str = ""
    ):
        """Crear gráfico de barras simple"""
        barras = self._create_bar_elements(categorias, valores, color, formato_valor)
        
        return ft.Column(
            [
                ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row(
                    barras,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.START
                )
            ],
            spacing=10
        )
    
    def _create_bar_elements(
        self,
        categorias: list,
        valores: list,
        color,
        formato_valor: str = ""
    ):
        """Crear elementos de barras para el gráfico"""
        max_valor = max(valores) if valores else 1
        
        barras = []
        for cat, val in zip(categorias, valores):
            altura = (val / max_valor * 150) if max_valor > 0 else 0
            
            # Mostrar valor solo si es mayor a 0
            valor_texto = ""
            if val > 0:
                if formato_valor == "$":
                    valor_texto = f"{formato_valor}{val:,.0f}"
                else:
                    valor_texto = str(int(val))
            
            barras.append(
                ft.Column(
                    [
                        ft.Text(
                            valor_texto,
                            size=10,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Container(
                            bgcolor=color if val > 0 else ft.Colors.GREY_300,
                            height=max(altura, 20),
                            width=40,
                            border_radius=5,
                        ),
                        ft.Text(cat, size=10, color=ft.Colors.GREY_600),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5
                )
            )
        
        return barras
    
    def _create_alerta(self, titulo: str, descripcion: str, color, accion_texto: str, accion):
        """Crear alerta destacada"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(descripcion, size=12, color=ft.Colors.GREY_600),
                        ],
                        spacing=5,
                        expand=True
                    ),
                    ft.TextButton(
                        accion_texto,
                        on_click=lambda _: accion()
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=color + "20",  # Color con transparencia
            border=ft.border.all(1, color),
            border_radius=8,
            padding=15
        )
    
    def _create_alerta_compacta(self, titulo: str, descripcion: str, bgcolor):
        """Crear alerta compacta"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(descripcion, size=11, color=ft.Colors.GREY_700),
                ],
                spacing=3
            ),
            bgcolor=bgcolor,
            border_radius=5,
            padding=10
        )
    
    def _create_acciones_rapidas(self):
        """Crear panel de acciones rápidas (compacto)"""
        acciones = [
            {
                "titulo": "Registrar Pago",
                "icono": ft.Icons.ATTACH_MONEY,
                "color": ft.Colors.GREEN,
                "accion": lambda: self.navigate_to("cuotas")
            },
            {
                "titulo": "Nuevo Socio",
                "icono": ft.Icons.PERSON_ADD,
                "color": ft.Colors.BLUE,
                "accion": lambda: self.navigate_to("socios")
            },
            {
                "titulo": "Ver Reportes",
                "icono": ft.Icons.ASSESSMENT,
                "color": ft.Colors.ORANGE,
                "accion": lambda: self.navigate_to("reportes")
            },
            {
                "titulo": "Validar Acceso",
                "icono": ft.Icons.QR_CODE_SCANNER,
                "color": ft.Colors.PURPLE,
                "accion": lambda: self.navigate_to("accesos")
            },
        ]
        
        botones = []
        for acc in acciones:
            botones.append(
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(acc["icono"], color=ft.Colors.WHITE, size=18),
                            ft.Text(acc["titulo"], color=ft.Colors.WHITE, size=11),
                        ],
                        spacing=8
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=acc["color"],
                        padding=10
                    ),
                    on_click=lambda _, a=acc["accion"]: a(),
                    expand=True
                )
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("⚡ Acciones Rápidas", size=14, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Column(botones, spacing=8)
                ],
                spacing=8
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
            height=280
        )
    
    def navigate_to(self, route: str):
        """Navegar a otra vista"""
        if self.navigate_callback:
            self.navigate_callback(route)
        else:
            self.show_info(f"Navegar a: {route}")
    
    def show_error(self, message: str):
        """Mostrar error"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_info(self, message: str):
        """Mostrar información"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.BLUE
        )
        self.page.snack_bar.open = True
        self.page.update()
