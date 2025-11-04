"""
Test de diagnóstico para ver qué está fallando
"""
import flet as ft
from src.services.api_client import api_client
from src.views.dashboard_view import DashboardView
from src.utils.notification_manager import NotificationManager

def main(page: ft.Page):
    page.title = "Test Dashboard"
    page.window.width = 1280
    page.window.height = 800
    
    # Simular usuario
    user = {
        "username": "admin",
        "rol": "SUPER_ADMIN",
        "id": 1
    }
    
    # Crear notification manager
    notification_manager = NotificationManager(page)
    
    # AppBar
    notification_badge = notification_manager.create_notification_badge()
    page.appbar = ft.AppBar(
        title=ft.Text("Test Dashboard"),
        bgcolor=ft.Colors.BLUE,
        actions=[notification_badge]
    )
    
    # Función de logout dummy
    def on_logout():
        print("Logout")
    
    # Función de navegación dummy
    def navigate(view_key):
        print(f"Navigate to: {view_key}")
    
    print("Creando DashboardView...")
    
    try:
        # Crear dashboard
        dashboard = DashboardView(
            page=page,
            user=user,
            on_logout=on_logout,
            navigate_callback=navigate
        )
        
        print("Dashboard creado exitosamente")
        print(f"Dashboard controls: {len(dashboard.controls)}")
        
        # Agregar a la página
        page.add(dashboard)
        page.update()
        
        print("Dashboard agregado a la página")
        
        # Cargar datos
        print("Cargando datos del dashboard...")
        dashboard.load_dashboard_data()
        
        print("✅ Todo cargado correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Mostrar error en pantalla
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED),
                        ft.Text("Error al cargar dashboard", size=20, color=ft.Colors.RED),
                        ft.Text(str(e), size=14),
                        ft.Text("Ver consola para más detalles", size=12, color=ft.Colors.GREY)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                expand=True,
                alignment=ft.alignment.center
            )
        )

if __name__ == "__main__":
    print("="*60)
    print("INICIANDO TEST DE DASHBOARD")
    print("="*60)
    ft.app(target=main)
