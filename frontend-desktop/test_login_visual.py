"""
Test visual para verificar que LoginView se renderiza
"""
import flet as ft
from src.views.login_view import LoginView

def main(page: ft.Page):
    page.title = "Test LoginView"
    page.window.width = 1280
    page.window.height = 800
    page.padding = 0
    
    def on_success(user_data):
        page.clean()
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("✅ LOGIN EXITOSO", size=30, color=ft.Colors.GREEN),
                        ft.Text(f"Usuario: {user_data.get('username', 'N/A')}", size=20),
                        ft.Text(f"Rol: {user_data.get('rol', 'N/A')}", size=20),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()
    
    print("Creando LoginView...")
    login_view = LoginView(on_success)
    print(f"LoginView creado: tipo={type(login_view)}")
    print(f"  - expand={login_view.expand}")
    print(f"  - content existe={login_view.content is not None}")
    
    print("Agregando a página...")
    page.add(login_view)
    print("LoginView agregado")
    page.update()
    print("Página actualizada")

if __name__ == "__main__":
    print("Iniciando test visual...")
    ft.app(target=main)
