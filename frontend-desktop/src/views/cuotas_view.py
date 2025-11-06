"""
Vista de Gestión de Cuotas y Pagos
frontend-desktop/src/views/cuotas_view.py
"""
import flet as ft
from src.services.api_client import api_client
from src.utils.error_handler import handle_api_error_with_banner, show_success
from src.components.error_banner import ErrorBanner, SuccessBanner
from datetime import date, datetime
from typing import Optional
from calendar import month_name


class CuotasView(ft.Column):
    """Vista principal de gestión de cuotas y pagos"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.pagos = []
        self.current_page = 1
        self.total_pages = 1
        
        # Filtros
        self.search_field = ft.TextField(
            hint_text="Buscar por número de socio o nombre...",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda _: self.page.run_task(self.load_pagos),
            expand=True
        )
        
        self.filter_estado = ft.Dropdown(
            label="Estado",
            hint_text="Todos",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("aprobado", "Aprobado"),
                ft.dropdown.Option("pendiente", "Pendiente"),
                ft.dropdown.Option("cancelado", "Cancelado"),
            ],
            width=150,
            on_change=lambda _: self.page.run_task(self.load_pagos)
        )
        
        self.filter_metodo = ft.Dropdown(
            label="Método",
            hint_text="Todos",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("efectivo", "Efectivo"),
                ft.dropdown.Option("transferencia", "Transferencia"),
                ft.dropdown.Option("debito", "Débito"),
                ft.dropdown.Option("credito", "Crédito"),
            ],
            width=150,
            on_change=lambda _: self.page.run_task(self.load_pagos)
        )
        
        self.fecha_inicio = ft.TextField(
            label="Fecha Desde",
            hint_text="YYYY-MM-DD",
            width=150
        )
        
        self.fecha_fin = ft.TextField(
            label="Fecha Hasta",
            hint_text="YYYY-MM-DD",
            width=150
        )
        
        # Cards de resumen
        self.card_ingresos = self.create_summary_card(
            "Total Ingresos",
            "$0.00",
            ft.Icons.TRENDING_UP,
            ft.Colors.GREEN
        )
        
        self.card_pagos = self.create_summary_card(
            "Pagos del Mes",
            "0",
            ft.Icons.RECEIPT_LONG,
            ft.Colors.BLUE
        )
        
        self.card_morosos = self.create_summary_card(
            "Socios Morosos",
            "0",
            ft.Icons.WARNING,
            ft.Colors.RED
        )
        
        self.card_saldo = self.create_summary_card(
            "Saldo Neto",
            "$0.00",
            ft.Icons.ACCOUNT_BALANCE_WALLET,
            ft.Colors.PURPLE
        )
        
        # Tabla de pagos
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Comprobante"), numeric=False),
                ft.DataColumn(ft.Text("Fecha"), numeric=False),
                ft.DataColumn(ft.Text("Socio"), numeric=False),
                ft.DataColumn(ft.Text("Concepto"), numeric=False),
                ft.DataColumn(ft.Text("Monto"), numeric=True),
                ft.DataColumn(ft.Text("Método"), numeric=False),
                ft.DataColumn(ft.Text("Estado"), numeric=False),
                ft.DataColumn(ft.Text("Acciones"), numeric=False),
            ],
            rows=[],
            column_spacing=10,
            horizontal_margin=12,
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        # Paginación
        self.pagination = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False
        )
        
        # Construir UI
        self.build_ui()
    
    def create_summary_card(self, title: str, value: str, icon, color):
        """Crear card de resumen"""
        value_text = ft.Text(value, size=24, weight=ft.FontWeight.BOLD)
        
        card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=40),
                            ft.Column(
                                [
                                    ft.Text(title, size=12, color=ft.Colors.GREY_600),
                                    value_text
                                ],
                                spacing=0
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                spacing=10
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
            )
        )
        
        # Guardar referencia al texto del valor
        card.data = {"value_text": value_text}
        
        return card
    
    def build_ui(self):
        """Construir interfaz"""
        self.controls = [
            # Título y botones
            ft.Row(
                [
                    ft.Text(
                        "Gestión de Cuotas",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Pago Rápido",
                                icon=ft.Icons.FLASH_ON,
                                on_click=lambda _: self.show_pago_rapido_dialog(),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_700
                                )
                            ),
                            ft.ElevatedButton(
                                "Registrar Pago",
                                icon=ft.Icons.ADD_CARD,
                                on_click=lambda _: self.show_registrar_pago_dialog()
                            ),
                        ],
                        spacing=10
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            
            ft.Divider(),
            
            # Cards de resumen
            ft.Row(
                [
                    self.card_ingresos,
                    self.card_pagos,
                    self.card_morosos,
                    self.card_saldo
                ],
                spacing=15
            ),
            
            ft.Divider(),
            
            # Filtros
            ft.Row(
                [
                    self.search_field,
                    self.filter_estado,
                    self.filter_metodo,
                    ft.IconButton(
                        icon=ft.Icons.FILTER_ALT,
                        tooltip="Filtros avanzados",
                        on_click=lambda _: self.show_filters_dialog()
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Actualizar",
                        on_click=lambda _: self.page.run_task(self.load_data)
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
                            padding=10,
                            expand=True
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
    
    def did_mount(self):
        """Llamado cuando el control se monta en la página"""
        if self.page:
            self.page.run_task(self.load_data)
    
    async def load_data(self):
        """Cargar todos los datos"""
        await self.load_resumen()
        await self.load_pagos()
    
    async def load_resumen(self):
        """Cargar resumen financiero"""
        try:
            resumen = await api_client.get_resumen_financiero()
            
            # Actualizar cards
            self.card_ingresos.data["value_text"].value = f"${resumen.get('total_ingresos', 0):,.2f}"
            self.card_pagos.data["value_text"].value = str(resumen.get('cantidad_pagos', 0))
            self.card_morosos.data["value_text"].value = str(resumen.get('cantidad_miembros_morosos', 0))
            self.card_saldo.data["value_text"].value = f"${resumen.get('saldo', 0):,.2f}"
            
            # Actualizar UI
            self.card_ingresos.update()
            self.card_pagos.update()
            self.card_morosos.update()
            self.card_saldo.update()
            
        except Exception as e:
            self.show_snackbar(f"Error cargando resumen: {e}", error=True)
    
    async def load_pagos(self):
        """Cargar lista de pagos"""
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            params = {
                "page": self.current_page,
                "page_size": 20
            }
            
            if self.filter_estado.value:
                params["estado"] = self.filter_estado.value
            
            if self.filter_metodo.value:
                params["metodo_pago"] = self.filter_metodo.value
            
            if self.fecha_inicio.value:
                params["fecha_inicio"] = self.fecha_inicio.value
            
            if self.fecha_fin.value:
                params["fecha_fin"] = self.fecha_fin.value
            
            response = await api_client.get_pagos(**params)
            
            items = response.get("items", [])
            pagination = response.get("pagination", {})
            
            self.total_pages = pagination.get("total_pages", 1)
            
            # Actualizar tabla
            self.update_table(items)
            
            # Actualizar paginación
            self.update_pagination(pagination)
            
        except Exception as e:
            self.show_snackbar(f"Error: {e}", error=True)
        
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()
    
    def update_table(self, pagos: list):
        """Actualizar tabla con datos"""
        self.data_table.rows.clear()
        
        for pago in pagos:
            # Color según estado
            estado = pago.get("estado", "")
            if estado == "aprobado":
                estado_color = ft.Colors.GREEN
            elif estado == "pendiente":
                estado_color = ft.Colors.ORANGE
            else:
                estado_color = ft.Colors.RED
            
            # Formato de monto
            monto = pago.get("monto_final", 0)
            monto_text = f"${monto:,.2f}"
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(pago.get("numero_comprobante", "-"), size=13)),
                        ft.DataCell(ft.Text(pago.get("fecha_pago", ""), size=13)),
                        ft.DataCell(ft.Text(pago.get("nombre_miembro", ""), size=13)),
                        ft.DataCell(ft.Text(pago.get("concepto", ""), size=13)),
                        ft.DataCell(
                            ft.Text(
                                monto_text,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_700,
                                size=13
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    pago.get("metodo_pago", "").capitalize(),
                                    size=12
                                ),
                                width=90
                            )
                        ),
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
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.VISIBILITY,
                                        tooltip="Ver detalles",
                                        icon_size=20,
                                        on_click=lambda e, p=pago: self.page.run_task(self.show_pago_details, p)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CANCEL,
                                        tooltip="Anular",
                                        icon_color=ft.Colors.RED,
                                        icon_size=20,
                                        on_click=lambda e, p=pago: self.page.run_task(self.show_anular_dialog, p),
                                        disabled=estado == "cancelado"
                                    ),
                                ],
                                spacing=5,
                                tight=True
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
        self.page.run_task(self.load_pagos)
    
    def show_pago_rapido_dialog(self):
        """Mostrar diálogo de pago rápido"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        # Búsqueda de socio
        socio_seleccionado = {"data": None}
        
        buscar_socio_field = ft.TextField(
            label="Buscar Socio *",
            hint_text="Nombre, apellido o documento",
            autofocus=True,
            expand=True
        )
        
        resultado_busqueda = ft.Column([], spacing=5, visible=False)
        
        # Mes y año
        mes_actual = date.today().month
        anio_actual = date.today().year
        
        mes_dropdown = ft.Dropdown(
            label="Mes *",
            value=str(mes_actual),
            options=[ft.dropdown.Option(str(i), month_name[i] if i <= 12 else "") for i in range(1, 13)],
            width=200
        )
        
        anio_field = ft.TextField(
            label="Año *",
            value=str(anio_actual),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=120
        )
        
        # Monto y método
        monto_field = ft.TextField(
            label="Monto *",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$",
            width=150
        )
        
        metodo_dropdown = ft.Dropdown(
            label="Método de Pago *",
            value="efectivo",
            options=[
                ft.dropdown.Option("efectivo", "Efectivo"),
                ft.dropdown.Option("transferencia", "Transferencia"),
                ft.dropdown.Option("debito", "Débito Automático"),
                ft.dropdown.Option("credito", "Tarjeta Crédito"),
            ],
            width=200
        )
        
        # Descuento
        aplicar_descuento = ft.Checkbox(label="Aplicar descuento", value=False)
        descuento_field = ft.TextField(
            label="% Descuento",
            hint_text="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
            visible=False
        )
        
        def toggle_descuento(e):
            descuento_field.visible = aplicar_descuento.value
            descuento_field.update()
        
        aplicar_descuento.on_change = toggle_descuento
        
        observaciones_field = ft.TextField(
            label="Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        # Info del socio seleccionado
        info_socio = ft.Container(
            content=ft.Text("No se ha seleccionado ningún socio", color=ft.Colors.GREY_600),
            visible=True
        )
        
        async def buscar_socio(e):
            query = buscar_socio_field.value
            if not query or len(query) < 3:
                error_banner.show_error("⚠️ Ingresa al menos 3 caracteres para buscar")
                return
            
            # Limpiar banner de error al buscar
            error_banner.hide()
            
            try:
                response = await api_client.get_miembros(q=query, page_size=5)
                items = response.get("items", [])
                
                resultado_busqueda.controls.clear()
                
                if not items:
                    resultado_busqueda.controls.append(
                        ft.Text("No se encontraron socios", color=ft.Colors.GREY)
                    )
                else:
                    for socio in items:
                        resultado_busqueda.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.PERSON),
                                    title=ft.Text(socio.get("nombre_completo", "")),
                                    subtitle=ft.Text(f"Doc: {socio.get('numero_documento', '')} - N°: {socio.get('numero_miembro', '')}"),
                                    on_click=lambda e, s=socio: seleccionar_socio(s)
                                ),
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=5,
                                ink=True
                            )
                        )
                
                resultado_busqueda.visible = True
                resultado_busqueda.update()
                
            except Exception as ex:
                handle_api_error_with_banner(ex, error_banner, "buscar socio")
        
        def seleccionar_socio(socio):
            socio_seleccionado["data"] = socio
            
            # Cargar monto de la categoría
            categoria = socio.get("categoria", {})
            cuota_base = categoria.get("cuota_base", 0)
            monto_field.value = str(cuota_base)
            
            # Actualizar info
            info_socio.content = ft.Column([
                ft.Text("✓ Socio Seleccionado", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                ft.Text(f"{socio.get('nombre_completo', '')}"),
                ft.Text(f"N°: {socio.get('numero_miembro', '')} - {categoria.get('nombre', '')}"),
            ], spacing=2)
            
            resultado_busqueda.visible = False
            
            info_socio.update()
            resultado_busqueda.update()
            monto_field.update()
        
        buscar_socio_field.on_submit = buscar_socio
        
        async def guardar_pago(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            # Validaciones locales
            if not socio_seleccionado["data"]:
                error_banner.show_error("⚠️ Debes seleccionar un socio")
                return
            
            if not monto_field.value:
                error_banner.show_error("⚠️ Debes ingresar un monto")
                return
            
            # Validar monto numérico
            try:
                monto = float(monto_field.value)
                if monto <= 0:
                    error_banner.show_error("⚠️ El monto debe ser mayor a cero")
                    return
            except ValueError:
                error_banner.show_error("⚠️ Ingresa un monto válido")
                return
            
            # Validar descuento si está aplicado
            if aplicar_descuento.value:
                try:
                    descuento = float(descuento_field.value) if descuento_field.value else 0
                    if descuento < 0 or descuento > 100:
                        error_banner.show_error("⚠️ El descuento debe estar entre 0 y 100%")
                        return
                except ValueError:
                    error_banner.show_error("⚠️ Ingresa un porcentaje de descuento válido")
                    return
            
            # Validar año
            try:
                anio = int(anio_field.value)
                if anio < 2000 or anio > 2100:
                    error_banner.show_error("⚠️ Ingresa un año válido")
                    return
            except ValueError:
                error_banner.show_error("⚠️ Ingresa un año válido")
                return
            
            try:
                data = {
                    "miembro_id": socio_seleccionado["data"]["id"],
                    "monto": monto,
                    "metodo_pago": metodo_dropdown.value,
                    "mes_periodo": int(mes_dropdown.value),
                    "anio_periodo": anio,
                    "aplicar_descuento": aplicar_descuento.value,
                    "porcentaje_descuento": float(descuento_field.value) if descuento_field.value else 0,
                    "observaciones": observaciones_field.value or None
                }
                
                await api_client.create_pago_rapido(data)
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "✓ Pago registrado exitosamente")
                await self.load_data()
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                handle_api_error_with_banner(ex, error_banner, "registrar pago")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚡ Pago Rápido - Cuota Mensual"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Formulario
                        ft.Text("Buscar Socio", weight=ft.FontWeight.BOLD),
                        buscar_socio_field,
                        resultado_busqueda,
                        info_socio,
                        ft.Divider(),
                        ft.Text("Período", weight=ft.FontWeight.BOLD),
                        ft.Row([mes_dropdown, anio_field], spacing=10),
                        ft.Divider(),
                        ft.Text("Pago", weight=ft.FontWeight.BOLD),
                        ft.Row([monto_field, metodo_dropdown], spacing=10),
                        ft.Row([aplicar_descuento, descuento_field], spacing=10),
                        ft.Divider(),
                        observaciones_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=500
                ),
                width=500,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Registrar Pago",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: self.page.run_task(guardar_pago, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_registrar_pago_dialog(self):
        """Mostrar diálogo de registro de pago completo"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        # Búsqueda de socio
        socio_seleccionado = {"data": None}
        
        buscar_socio_field = ft.TextField(
            label="Buscar Socio *",
            hint_text="Nombre, apellido o documento",
            autofocus=True,
            expand=True
        )
        
        resultado_busqueda = ft.Column([], spacing=5, visible=False)
        
        # Info del socio seleccionado
        info_socio = ft.Container(
            content=ft.Text("No se ha seleccionado ningún socio", color=ft.Colors.GREY_600),
            visible=True
        )
        
        # Tipo de pago
        tipo_dropdown = ft.Dropdown(
            label="Tipo de Pago *",
            value="cuota",
            options=[
                ft.dropdown.Option("cuota", "Cuota Mensual"),
                ft.dropdown.Option("inscripcion", "Inscripción"),
                ft.dropdown.Option("adicional", "Servicio Adicional"),
                ft.dropdown.Option("multa", "Multa"),
                ft.dropdown.Option("otro", "Otro"),
            ],
            width=200
        )
        
        concepto_field = ft.TextField(
            label="Concepto *",
            hint_text="Descripción del pago",
            expand=True
        )
        
        descripcion_field = ft.TextField(
            label="Descripción",
            hint_text="Detalle adicional",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        # Montos
        monto_field = ft.TextField(
            label="Monto Base *",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$",
            width=150
        )
        
        descuento_field = ft.TextField(
            label="Descuento",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$",
            value="0",
            width=150
        )
        
        recargo_field = ft.TextField(
            label="Recargo",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="$",
            value="0",
            width=150
        )
        
        total_text = ft.Text("Total: $0.00", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        
        def calcular_total(e=None):
            try:
                monto = float(monto_field.value or 0)
                descuento = float(descuento_field.value or 0)
                recargo = float(recargo_field.value or 0)
                total = monto - descuento + recargo
                total_text.value = f"Total: ${total:,.2f}"
                total_text.update()
            except:
                pass
        
        monto_field.on_change = calcular_total
        descuento_field.on_change = calcular_total
        recargo_field.on_change = calcular_total
        
        # Método de pago
        metodo_dropdown = ft.Dropdown(
            label="Método de Pago *",
            value="efectivo",
            options=[
                ft.dropdown.Option("efectivo", "Efectivo"),
                ft.dropdown.Option("transferencia", "Transferencia"),
                ft.dropdown.Option("debito", "Débito Automático"),
                ft.dropdown.Option("credito", "Tarjeta Crédito"),
            ],
            width=200
        )
        
        # Fechas
        fecha_pago_field = ft.TextField(
            label="Fecha de Pago",
            value=date.today().isoformat(),
            width=150
        )
        
        fecha_periodo_field = ft.TextField(
            label="Período (YYYY-MM-DD)",
            hint_text="Opcional",
            width=150
        )
        
        observaciones_field = ft.TextField(
            label="Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        
        async def buscar_socio(e):
            query = buscar_socio_field.value
            if not query or len(query) < 3:
                error_banner.show_error("⚠️ Ingresa al menos 3 caracteres para buscar")
                return
            
            # Limpiar banner de error al buscar
            error_banner.hide()
            
            try:
                response = await api_client.get_miembros(q=query, page_size=5)
                items = response.get("items", [])
                
                resultado_busqueda.controls.clear()
                
                if not items:
                    resultado_busqueda.controls.append(
                        ft.Text("No se encontraron socios", color=ft.Colors.GREY)
                    )
                else:
                    for socio in items:
                        resultado_busqueda.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(ft.Icons.PERSON),
                                    title=ft.Text(socio.get("nombre_completo", "")),
                                    subtitle=ft.Text(f"Doc: {socio.get('numero_documento', '')} - N°: {socio.get('numero_miembro', '')}"),
                                    on_click=lambda e, s=socio: seleccionar_socio(s)
                                ),
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=5,
                                ink=True
                            )
                        )
                
                resultado_busqueda.visible = True
                resultado_busqueda.update()
                
            except Exception as ex:
                handle_api_error_with_banner(ex, error_banner, "buscar socio")
        
        def seleccionar_socio(socio):
            socio_seleccionado["data"] = socio
            
            # Cargar monto de la categoría
            categoria = socio.get("categoria", {})
            cuota_base = categoria.get("cuota_base", 0)
            monto_field.value = str(cuota_base)
            
            # Actualizar info
            info_socio.content = ft.Column([
                ft.Text("✓ Socio Seleccionado", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                ft.Text(f"{socio.get('nombre_completo', '')}"),
                ft.Text(f"N°: {socio.get('numero_miembro', '')} - {categoria.get('nombre', '')}"),
            ], spacing=2)
            
            resultado_busqueda.visible = False
            
            info_socio.update()
            resultado_busqueda.update()
            monto_field.update()
            calcular_total()
        
        buscar_socio_field.on_submit = buscar_socio
        
        async def guardar_pago(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            # Validaciones locales
            if not socio_seleccionado["data"]:
                error_banner.show_error("⚠️ Debes seleccionar un socio")
                return
            
            if not concepto_field.value:
                error_banner.show_error("⚠️ Debes ingresar un concepto")
                return
            
            if not monto_field.value:
                error_banner.show_error("⚠️ Debes ingresar un monto")
                return
            
            # Validar montos numéricos
            try:
                monto = float(monto_field.value)
                descuento = float(descuento_field.value or 0)
                recargo = float(recargo_field.value or 0)
                
                if monto <= 0:
                    error_banner.show_error("⚠️ El monto debe ser mayor a cero")
                    return
                
                if descuento < 0:
                    error_banner.show_error("⚠️ El descuento no puede ser negativo")
                    return
                
                if recargo < 0:
                    error_banner.show_error("⚠️ El recargo no puede ser negativo")
                    return
                
                total = monto - descuento + recargo
                if total <= 0:
                    error_banner.show_error("⚠️ El monto final debe ser mayor a cero")
                    return
                    
            except ValueError:
                error_banner.show_error("⚠️ Ingresa valores numéricos válidos")
                return
            
            # Validar fecha
            try:
                datetime.fromisoformat(fecha_pago_field.value)
            except:
                error_banner.show_error("⚠️ Formato de fecha inválido (debe ser YYYY-MM-DD)")
                return
            
            try:
                data = {
                    "miembro_id": socio_seleccionado["data"]["id"],
                    "tipo": tipo_dropdown.value,
                    "concepto": concepto_field.value,
                    "descripcion": descripcion_field.value or None,
                    "monto": monto,
                    "descuento": descuento,
                    "recargo": recargo,
                    "metodo_pago": metodo_dropdown.value,
                    "fecha_pago": fecha_pago_field.value,
                    "fecha_periodo": fecha_periodo_field.value or None,
                    "observaciones": observaciones_field.value or None
                }
                
                await api_client.create_pago(data)
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "✓ Pago registrado exitosamente")
                await self.load_data()
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                handle_api_error_with_banner(ex, error_banner, "registrar pago")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Pago Completo"),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Formulario
                        ft.Text("Socio", weight=ft.FontWeight.BOLD),
                        buscar_socio_field,
                        resultado_busqueda,
                        info_socio,
                        ft.Divider(),
                        ft.Text("Detalles del Pago", weight=ft.FontWeight.BOLD),
                        ft.Row([tipo_dropdown, metodo_dropdown], spacing=10),
                        concepto_field,
                        descripcion_field,
                        ft.Divider(),
                        ft.Text("Montos", weight=ft.FontWeight.BOLD),
                        ft.Row([monto_field, descuento_field, recargo_field], spacing=10),
                        total_text,
                        ft.Divider(),
                        ft.Text("Fechas", weight=ft.FontWeight.BOLD),
                        ft.Row([fecha_pago_field, fecha_periodo_field], spacing=10),
                        ft.Divider(),
                        observaciones_field,
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=600
                ),
                width=600,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Registrar Pago",
                    icon=ft.Icons.CHECK,
                    on_click=lambda e: self.page.run_task(guardar_pago, e)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_filters_dialog(self):
        """Mostrar diálogo de filtros avanzados"""
        
        def aplicar_filtros(e):
            self.page.run_task(self.load_pagos)
            dialogo.open = False
            self.page.update()
        
        def limpiar_filtros(e):
            self.fecha_inicio.value = ""
            self.fecha_fin.value = ""
            self.filter_estado.value = ""
            self.filter_metodo.value = ""
            self.search_field.value = ""
            
            dialogo.open = False
            self.page.update()
            self.page.run_task(self.load_pagos)
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Filtros Avanzados"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Rango de Fechas", weight=ft.FontWeight.BOLD),
                        self.fecha_inicio,
                        self.fecha_fin,
                        ft.Divider(),
                        ft.Text("Estado y Método", weight=ft.FontWeight.BOLD),
                        self.filter_estado,
                        self.filter_metodo,
                    ],
                    spacing=10
                ),
                width=400,
                padding=20
            ),
            actions=[
                ft.TextButton("Limpiar", on_click=limpiar_filtros),
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton("Aplicar", on_click=aplicar_filtros),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    async def show_pago_details(self, pago: dict):
        """Mostrar detalles del pago"""
        try:
            # Obtener detalles completos
            pago_completo = await api_client.get_pago(pago["id"])
            
            miembro_info = pago_completo.get("miembro", {})
            
            def cerrar_dialogo(e):
                dialogo.open = False
                self.page.update()
            
            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Comprobante {pago_completo.get('numero_comprobante', '')}"),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.RECEIPT_LONG),
                                title=ft.Text("Concepto"),
                                subtitle=ft.Text(pago_completo.get("concepto", ""))
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text("Socio"),
                                subtitle=ft.Text(miembro_info.get("nombre_completo", ""))
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.CALENDAR_TODAY),
                                title=ft.Text("Fecha de Pago"),
                                subtitle=ft.Text(pago_completo.get("fecha_pago", ""))
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.ATTACH_MONEY),
                                title=ft.Text("Monto Base"),
                                subtitle=ft.Text(f"${pago_completo.get('monto', 0):,.2f}")
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.REMOVE_CIRCLE),
                                title=ft.Text("Descuento"),
                                subtitle=ft.Text(f"${pago_completo.get('descuento', 0):,.2f}")
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.ADD_CIRCLE),
                                title=ft.Text("Recargo"),
                                subtitle=ft.Text(f"${pago_completo.get('recargo', 0):,.2f}")
                            ),
                            ft.Divider(),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET),
                                title=ft.Text("TOTAL", weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(
                                    f"${pago_completo.get('monto_final', 0):,.2f}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN_700
                                )
                            ),
                            ft.Divider(),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.PAYMENT),
                                title=ft.Text("Método de Pago"),
                                subtitle=ft.Text(pago_completo.get("metodo_pago", "").capitalize())
                            ),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.INFO),
                                title=ft.Text("Estado"),
                                subtitle=ft.Text(pago_completo.get("estado", "").upper())
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        height=500
                    ),
                    width=450
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
            self.show_snackbar(f"Error cargando detalles: {e}", error=True)
    
    async def show_anular_dialog(self, pago: dict):
        """Mostrar diálogo para anular pago"""
        
        # Banners de error/éxito para el diálogo
        error_banner = ErrorBanner()
        success_banner = SuccessBanner()
        
        motivo_field = ft.TextField(
            label="Motivo de Anulación *",
            hint_text="Explica por qué se anula este pago (mínimo 10 caracteres)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            autofocus=True
        )
        
        async def confirmar_anulacion(e):
            # Limpiar mensajes previos
            error_banner.hide()
            success_banner.hide()
            
            # Validaciones locales
            if not motivo_field.value:
                error_banner.show_error("⚠️ Debes ingresar un motivo para la anulación")
                return
            
            if len(motivo_field.value.strip()) < 10:
                error_banner.show_error("⚠️ El motivo debe tener al menos 10 caracteres")
                return
            
            # Validación adicional: evitar motivos genéricos
            motivo_lower = motivo_field.value.strip().lower()
            if motivo_lower in ['sin motivo', 'error', 'anular', 'ninguno', 'na', 'n/a']:
                error_banner.show_error("⚠️ Por favor, proporciona un motivo más específico")
                return
            
            try:
                await api_client.anular_pago(pago["id"], motivo_field.value)
                
                dialogo.open = False
                self.page.update()
                
                show_success(self.page, "✓ Pago anulado correctamente")
                await self.load_data()
                
            except Exception as ex:
                import traceback
                traceback.print_exc()
                handle_api_error_with_banner(ex, error_banner, "anular pago")
        
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=30),
                    ft.Text("Anular Pago", color=ft.Colors.RED)
                ],
                spacing=10
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        # Banners para mensajes en el diálogo
                        error_banner,
                        success_banner,
                        
                        # Advertencia y datos del pago
                        ft.Text(
                            f"¿Estás seguro de anular el pago {pago.get('numero_comprobante', '')}?",
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Esta acción revertirá el saldo del socio y no se puede deshacer.",
                            color=ft.Colors.GREY_700
                        ),
                        ft.Divider(),
                        ft.Text(f"Concepto: {pago.get('concepto', '')}"),
                        ft.Text(f"Monto: ${pago.get('monto_final', 0):,.2f}"),
                        ft.Text(f"Socio: {pago.get('nombre_miembro', '')}"),
                        ft.Divider(),
                        motivo_field,
                    ],
                    spacing=10
                ),
                width=450,
                padding=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.ElevatedButton(
                    "Confirmar Anulación",
                    icon=ft.Icons.CANCEL,
                    on_click=lambda e: self.page.run_task(confirmar_anulacion, e),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def show_snackbar(self, message: str, error: bool = False):
        """Mostrar mensaje snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()