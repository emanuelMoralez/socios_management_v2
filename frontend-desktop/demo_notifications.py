"""
Demo del NotificationManager - Prueba sin necesidad de login
"""
import flet as ft
from src.utils.notification_manager import NotificationManager
import asyncio
from datetime import datetime


def main(page: ft.Page):
    page.title = "Demo - NotificationManager"
    page.window.width = 1200
    page.window.height = 800
    
    # Crear instancia del notification manager
    notification_manager = NotificationManager(page)
    
    # Badge de notificaciones
    notification_badge = notification_manager.create_notification_badge()
    
    # AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("Demo - Sistema de Notificaciones"),
        bgcolor=ft.Colors.BLUE,
        actions=[notification_badge]
    )
    
    # Contadores
    notif_count = {"success": 0, "info": 0, "warning": 0, "error": 0}
    
    # Funciones para agregar notificaciones
    def add_success(e):
        notif_count["success"] += 1
        notification_manager.add_notification(
            titulo=f"✅ Operación Exitosa #{notif_count['success']}",
            mensaje=f"Pago registrado correctamente - {datetime.now().strftime('%H:%M:%S')}",
            tipo="success"
        )
    
    def add_info(e):
        notif_count["info"] += 1
        notification_manager.add_notification(
            titulo=f"ℹ️ Información #{notif_count['info']}",
            mensaje=f"Nueva actualización disponible - {datetime.now().strftime('%H:%M:%S')}",
            tipo="info"
        )
    
    def add_warning(e):
        notif_count["warning"] += 1
        notification_manager.add_notification(
            titulo=f"⚠️ Advertencia #{notif_count['warning']}",
            mensaje=f"Se detectaron {notif_count['warning']} socio(s) moroso(s) - {datetime.now().strftime('%H:%M:%S')}",
            tipo="warning",
            accion=lambda: page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Navegando a reportes..."), bgcolor=ft.Colors.BLUE)
            ),
            accion_texto="Ver Reportes"
        )
    
    def add_error(e):
        notif_count["error"] += 1
        notification_manager.add_notification(
            titulo=f"❌ Error #{notif_count['error']}",
            mensaje=f"No se pudo conectar con el servidor - {datetime.now().strftime('%H:%M:%S')}",
            tipo="error"
        )
    
    def clear_all(e):
        notification_manager.clear_notifications()
        for key in notif_count:
            notif_count[key] = 0
        page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Notificaciones limpiadas"), bgcolor=ft.Colors.GREEN)
        )
    
    async def simulate_background():
        """Simular chequeo en background"""
        count = 0
        while True:
            await asyncio.sleep(10)  # Cada 10 segundos para demo
            count += 1
            notification_manager.add_notification(
                titulo=f"🔄 Chequeo Automático #{count}",
                mensaje=f"Sistema verificado - {datetime.now().strftime('%H:%M:%S')}",
                tipo="info"
            )
    
    def start_background(e):
        page.run_task(simulate_background)
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Chequeo automático iniciado (cada 10 seg)"),
                bgcolor=ft.Colors.GREEN
            )
        )
    
    # UI
    content = ft.Column(
        [
            ft.Container(height=20),
            ft.Text(
                "🔔 Demo del Sistema de Notificaciones",
                size=28,
                weight=ft.FontWeight.BOLD
            ),
            ft.Text(
                "Haz click en los botones para simular diferentes tipos de notificaciones",
                size=14,
                color=ft.Colors.GREY_700
            ),
            ft.Divider(),
            
            ft.Container(height=20),
            
            # Botones de notificaciones
            ft.Text("Agregar Notificaciones:", size=18, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.ElevatedButton(
                        "✅ Success",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=add_success,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE
                        ),
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "ℹ️ Info",
                        icon=ft.Icons.INFO,
                        on_click=add_info,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE
                        ),
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "⚠️ Warning",
                        icon=ft.Icons.WARNING,
                        on_click=add_warning,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE,
                            color=ft.Colors.WHITE
                        ),
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "❌ Error",
                        icon=ft.Icons.ERROR,
                        on_click=add_error,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE
                        ),
                        expand=True
                    ),
                ],
                spacing=10
            ),
            
            ft.Container(height=20),
            
            # Acciones
            ft.Text("Acciones:", size=18, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.ElevatedButton(
                        "🔄 Iniciar Chequeo Automático",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=start_background,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE,
                            color=ft.Colors.WHITE
                        )
                    ),
                    ft.ElevatedButton(
                        "🗑️ Limpiar Todas",
                        icon=ft.Icons.DELETE_SWEEP,
                        on_click=clear_all,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_700,
                            color=ft.Colors.WHITE
                        )
                    ),
                ],
                spacing=10
            ),
            
            ft.Container(height=30),
            ft.Divider(),
            
            # Instrucciones
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("📋 Instrucciones:", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Haz click en los botones de colores para agregar notificaciones"),
                        ft.Text("2. Observa el badge 🔔 en el AppBar (esquina superior derecha)"),
                        ft.Text("3. El número indica notificaciones no leídas"),
                        ft.Text("4. Haz click en el badge 🔔 para abrir el panel de notificaciones"),
                        ft.Text("5. En el panel puedes:"),
                        ft.Text("   • Ver todas las notificaciones"),
                        ft.Text("   • Marcar como leída (botón ✓)"),
                        ft.Text("   • Ejecutar acciones (botón 'Ver Reportes' en warnings)"),
                        ft.Text("   • Marcar todas como leídas"),
                        ft.Text("6. Las notificaciones Warning y Error muestran snackbar automático"),
                        ft.Text("7. Inicia el chequeo automático para ver notificaciones cada 10 segundos"),
                    ],
                    spacing=8
                ),
                padding=20,
                border=ft.border.all(2, ft.Colors.BLUE_200),
                border_radius=10,
                bgcolor=ft.Colors.BLUE_50
            ),
            
            ft.Container(height=20),
            
            # Estadísticas
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("📊 Estadísticas:", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.Text(f"✅ Success: {notif_count['success']}", size=14),
                                ft.Text(f"ℹ️ Info: {notif_count['info']}", size=14),
                                ft.Text(f"⚠️ Warning: {notif_count['warning']}", size=14),
                                ft.Text(f"❌ Error: {notif_count['error']}", size=14),
                            ],
                            spacing=20
                        )
                    ],
                    spacing=10
                ),
                padding=15,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                bgcolor=ft.Colors.GREY_50
            )
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    page.add(
        ft.Container(
            content=content,
            padding=30,
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
