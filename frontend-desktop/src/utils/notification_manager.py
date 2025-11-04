"""
Gestor de Notificaciones para la App
frontend-desktop/src/utils/notification_manager.py
"""
import flet as ft
from datetime import datetime
from typing import Callable, Optional
import asyncio


class NotificationManager:
    """Gestor de notificaciones en tiempo real"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.notification_badge = None
        self.badge_counter = None
        self.notification_count = 0
        self.notifications = []
        self.check_interval = 300  # 5 minutos
        self.is_checking = False
        self.last_morosos_count = 0
        
    def create_notification_badge(self) -> ft.Container:
        """Crear badge de notificaciones para el AppBar"""
        # Badge visual personalizado usando Stack
        icon_button = ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS,
            icon_color=ft.Colors.WHITE,
            on_click=lambda _: self.show_notifications_panel(),
            tooltip="Notificaciones"
        )
        
        # Contador badge
        self.badge_counter = ft.Container(
            content=ft.Text(
                str(self.notification_count) if self.notification_count > 0 else "",
                size=10,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE
            ),
            bgcolor=ft.Colors.RED,
            width=18,
            height=18,
            border_radius=9,
            alignment=ft.alignment.center,
            visible=self.notification_count > 0
        )
        
        # Stack para superponer badge sobre icono
        self.notification_badge = ft.Stack(
            [
                icon_button,
                ft.Container(
                    content=self.badge_counter,
                    right=0,
                    top=5
                )
            ],
            width=48,
            height=48
        )
        
        return self.notification_badge
    
    def update_badge_count(self, count: int):
        """Actualizar contador del badge"""
        self.notification_count = count
        if self.badge_counter:
            self.badge_counter.content.value = str(count) if count > 0 else ""
            self.badge_counter.visible = count > 0
            self.page.update()
    
    def add_notification(
        self,
        titulo: str,
        mensaje: str,
        tipo: str = "info",  # info, warning, error, success
        accion: Optional[Callable] = None,
        accion_texto: str = "Ver"
    ):
        """Agregar nueva notificación"""
        # Mapeo de tipos a colores e iconos
        config = {
            "info": {"color": ft.Colors.BLUE, "icon": ft.Icons.INFO},
            "warning": {"color": ft.Colors.ORANGE, "icon": ft.Icons.WARNING},
            "error": {"color": ft.Colors.RED, "icon": ft.Icons.ERROR},
            "success": {"color": ft.Colors.GREEN, "icon": ft.Icons.CHECK_CIRCLE},
        }
        
        notif_config = config.get(tipo, config["info"])
        
        notification = {
            "id": len(self.notifications),
            "titulo": titulo,
            "mensaje": mensaje,
            "tipo": tipo,
            "color": notif_config["color"],
            "icon": notif_config["icon"],
            "fecha": datetime.now(),
            "leida": False,
            "accion": accion,
            "accion_texto": accion_texto
        }
        
        self.notifications.insert(0, notification)  # Más recientes primero
        self.update_badge_count(len([n for n in self.notifications if not n["leida"]]))
        
        # Mostrar snackbar para notificaciones importantes
        if tipo in ["warning", "error"]:
            self.show_snackbar(titulo, mensaje, tipo)
    
    def show_snackbar(self, titulo: str, mensaje: str, tipo: str):
        """Mostrar snackbar con la notificación"""
        color_map = {
            "info": ft.Colors.BLUE,
            "warning": ft.Colors.ORANGE,
            "error": ft.Colors.RED,
            "success": ft.Colors.GREEN,
        }
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.WARNING if tipo == "warning" else ft.Icons.ERROR,
                        color=ft.Colors.WHITE
                    ),
                    ft.Column(
                        [
                            ft.Text(titulo, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(mensaje, size=12, color=ft.Colors.WHITE),
                        ],
                        spacing=2,
                        expand=True
                    )
                ],
                spacing=10
            ),
            bgcolor=color_map.get(tipo, ft.Colors.BLUE),
            duration=5000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show_notifications_panel(self):
        """Mostrar panel lateral con todas las notificaciones"""
        
        def cerrar_panel(e):
            panel.open = False
            self.page.update()
        
        def marcar_leida(notif_id):
            for notif in self.notifications:
                if notif["id"] == notif_id:
                    notif["leida"] = True
            self.update_badge_count(len([n for n in self.notifications if not n["leida"]]))
            self.show_notifications_panel()  # Refrescar panel
        
        def marcar_todas_leidas(e):
            for notif in self.notifications:
                notif["leida"] = True
            self.update_badge_count(0)
            cerrar_panel(e)
        
        # Crear lista de notificaciones
        notif_items = []
        
        if not self.notifications:
            notif_items.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=60, color=ft.Colors.GREY),
                            ft.Text("No hay notificaciones", color=ft.Colors.GREY_600)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10
                    ),
                    padding=40
                )
            )
        else:
            for notif in self.notifications[:20]:  # Últimas 20
                tiempo_transcurrido = self._format_tiempo(notif["fecha"])
                
                notif_item = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(notif["icon"], color=notif["color"], size=30),
                            ft.Column(
                                [
                                    ft.Text(
                                        notif["titulo"],
                                        size=14,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        notif["mensaje"],
                                        size=12,
                                        color=ft.Colors.GREY_700
                                    ),
                                    ft.Text(
                                        tiempo_transcurrido,
                                        size=10,
                                        color=ft.Colors.GREY_500
                                    ),
                                ],
                                spacing=3,
                                expand=True
                            ),
                            ft.Column(
                                [
                                    control for control in [
                                        ft.IconButton(
                                            icon=ft.Icons.CHECK,
                                            icon_size=16,
                                            tooltip="Marcar como leída",
                                            on_click=lambda _, nid=notif["id"]: marcar_leida(nid)
                                        ) if not notif["leida"] else ft.Icon(
                                            ft.Icons.CHECK_CIRCLE,
                                            color=ft.Colors.GREEN,
                                            size=16
                                        ),
                                        ft.TextButton(
                                            notif["accion_texto"],
                                            on_click=lambda _, n=notif: n["accion"]() if n["accion"] else None
                                        ) if notif["accion"] else None
                                    ] if control is not None
                                ],
                                spacing=5
                            )
                        ],
                        spacing=10
                    ),
                    bgcolor=ft.Colors.GREY_50 if notif["leida"] else ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=15
                )
                
                notif_items.append(notif_item)
        
        # Panel lateral - Construir lista de controles sin None
        panel_controls = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "🔔 Notificaciones",
                            size=20,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            on_click=cerrar_panel
                        )
                    ]
                ),
                padding=ft.padding.only(left=20, right=10, top=10, bottom=10)
            ),
            ft.Divider(),
        ]
        
        # Agregar botón "Marcar todas" solo si hay notificaciones no leídas
        if any(not n["leida"] for n in self.notifications):
            panel_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.TextButton(
                                "Marcar todas como leídas",
                                on_click=marcar_todas_leidas
                            ),
                        ]
                    ),
                    padding=ft.padding.only(left=20, right=20)
                )
            )
        
        # Agregar lista de notificaciones
        panel_controls.append(
            ft.Column(
                notif_items,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        
        panel = ft.NavigationDrawer(
            controls=panel_controls,
            bgcolor=ft.Colors.WHITE
        )
        
        self.page.drawer = panel
        panel.open = True
        self.page.update()
    
    def _format_tiempo(self, fecha: datetime) -> str:
        """Formatear tiempo transcurrido"""
        ahora = datetime.now()
        diff = ahora - fecha
        
        if diff.days > 0:
            return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            horas = diff.seconds // 3600
            return f"Hace {horas} hora{'s' if horas > 1 else ''}"
        elif diff.seconds >= 60:
            minutos = diff.seconds // 60
            return f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return "Hace unos segundos"
    
    async def start_background_check(self, check_morosos_callback):
        """Iniciar chequeo en background de nuevos morosos"""
        self.is_checking = True
        
        while self.is_checking:
            try:
                # Ejecutar callback para verificar morosos
                nuevos_morosos = await check_morosos_callback()
                
                # Si hay cambios, notificar
                if nuevos_morosos > self.last_morosos_count:
                    diferencia = nuevos_morosos - self.last_morosos_count
                    self.add_notification(
                        titulo="⚠️ Nuevos Socios Morosos",
                        mensaje=f"Se detectaron {diferencia} nuevo(s) socio(s) con morosidad",
                        tipo="warning",
                        accion=lambda: self.page.go("/reportes"),
                        accion_texto="Ver Reportes"
                    )
                
                self.last_morosos_count = nuevos_morosos
                
            except Exception as e:
                print(f"Error en background check: {e}")
            
            # Esperar antes del próximo chequeo
            await asyncio.sleep(self.check_interval)
    
    def stop_background_check(self):
        """Detener chequeo en background"""
        self.is_checking = False
    
    def clear_notifications(self):
        """Limpiar todas las notificaciones"""
        self.notifications.clear()
        self.update_badge_count(0)