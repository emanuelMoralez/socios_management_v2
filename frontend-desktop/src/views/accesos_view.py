"""
Vista de Accesos
frontend-desktop/src/views/accesos_view.py
"""
import flet as ft
from src.services.api_client import api_client


class AccesosView(ft.Column):
    """Vista de historial de accesos"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        
        # Resumen
        self.resumen_row = ft.Row(spacing=20)
        
        # Tabla
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha/Hora")),
                ft.DataColumn(ft.Text("Socio")),
                ft.DataColumn(ft.Text("Ubicación")),
                ft.DataColumn(ft.Text("Resultado")),
                ft.DataColumn(ft.Text("Mensaje")),
            ],
            rows=[],
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        self.build_ui()
        
    # Cargar datos
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        self.page.run_task(self.load_resumen)
        self.page.run_task(self.load_accesos)
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            ft.Text("Control de Accesos", size=24, weight=ft.FontWeight.BOLD),
            
            ft.Divider(),
            
            # Resumen
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Resumen", size=18, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            self.resumen_row
                        ]
                    ),
                    padding=20
                )
            ),
            
            ft.Divider(),
            
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
    
    async def load_resumen(self):
        """Cargar resumen de accesos"""
        try:
            resumen = await api_client.get_resumen_accesos()
            
            self.resumen_row.controls = [
                self.create_stat_card("Hoy", str(resumen.get("hoy", 0)), ft.Colors.BLUE),
                self.create_stat_card("Esta Semana", str(resumen.get("semana", 0)), ft.Colors.GREEN),
                self.create_stat_card("Este Mes", str(resumen.get("mes", 0)), ft.Colors.PURPLE),
                self.create_stat_card("Rechazos Hoy", str(resumen.get("rechazos_hoy", 0)), ft.Colors.RED),
            ]
            
            self.resumen_row.update()
            
        except Exception as e:
            print(f"Error cargando resumen: {e}")
    
    def create_stat_card(self, title: str, value: str, color):
        """Crear tarjeta de estadística"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=14, color=ft.Colors.GREY_600),
                    ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=color),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
    
    async def load_accesos(self):
        """Cargar historial de accesos"""
        self.loading.visible = True
        self.update()
        
        try:
            response = await api_client.get_accesos(page=1, page_size=20)
            items = response.get("items", [])
            
            self.data_table.rows.clear()
            
            for acceso in items:
                resultado = acceso.get("resultado", "")
                
                # Color según resultado
                if resultado == "permitido":
                    color = ft.Colors.GREEN
                    icon = "[OK]"
                elif resultado == "rechazado":
                    color = ft.Colors.RED
                    icon = "[ERROR]"
                else:
                    color = ft.Colors.ORANGE
                    icon = "[WARN]"
                
                self.data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(acceso.get("fecha_hora", "")[:16])),
                            ft.DataCell(ft.Text(acceso.get("nombre_miembro", ""))),
                            ft.DataCell(ft.Text(acceso.get("ubicacion", ""))),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        f"{icon} {resultado.upper()}",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE
                                    ),
                                    bgcolor=color,
                                    padding=5,
                                    border_radius=5
                                )
                            ),
                            ft.DataCell(ft.Text(acceso.get("mensaje", "")[:50])),
                        ]
                    )
                )
            
            self.update()
            
        except Exception as e:
            self.show_snackbar(f"Error: {e}", error=True)
        
        finally:
            self.loading.visible = False
            self.update()
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()