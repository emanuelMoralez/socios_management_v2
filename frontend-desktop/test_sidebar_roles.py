"""
Test para verificar el rol del usuario y la creación de botones
"""
import flet as ft
from src.views.main_layout import MainLayout

def main(page: ft.Page):
    page.title = "Test Sidebar"
    page.window.width = 1280
    page.window.height = 800
    
    # Simular diferentes usuarios con roles
    usuarios_test = [
        {
            "id": 1,
            "username": "super_admin",
            "rol": "SUPER_ADMIN"
        },
        {
            "id": 2,
            "username": "admin",
            "rol": "ADMINISTRADOR"
        },
        {
            "id": 3,
            "username": "operador",
            "rol": "OPERADOR"
        },
        {
            "id": 4,
            "username": "portero",
            "rol": "PORTERO"
        }
    ]
    
    # Selector de usuario
    current_user_index = [0]  # Lista para mutabilidad
    
    def on_logout():
        print("Logout")
    
    def cambiar_usuario(e):
        current_user_index[0] = (current_user_index[0] + 1) % len(usuarios_test)
        cargar_layout()
    
    def cargar_layout():
        page.clean()
        
        user = usuarios_test[current_user_index[0]]
        print(f"\n{'='*60}")
        print(f"CARGANDO LAYOUT PARA: {user['username']} ({user['rol']})")
        print(f"{'='*60}\n")
        
        # Botón para cambiar usuario
        cambiar_btn = ft.ElevatedButton(
            f"Cambiar Usuario (actual: {user['username']})",
            on_click=cambiar_usuario,
            bgcolor=ft.Colors.ORANGE
        )
        
        # Crear MainLayout
        main_layout = MainLayout(
            page=page,
            user=user,
            on_logout=on_logout,
            initial_view="dashboard"
        )
        
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=cambiar_btn,
                        padding=20,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    main_layout
                ],
                spacing=0,
                expand=True
            )
        )
        page.update()
    
    # Cargar layout inicial
    cargar_layout()

if __name__ == "__main__":
    ft.app(target=main)
