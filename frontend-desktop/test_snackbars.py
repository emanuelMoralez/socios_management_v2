#!/usr/bin/env python3
"""
Test rápido de snackbars en Flet
"""
import flet as ft
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.error_handler import show_success, show_warning, handle_api_error
from services.api_client import ValidationError


def main(page: ft.Page):
    page.title = "Test de Snackbars"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    def test_success(e):
        show_success(page, "¡Operación exitosa!")
    
    def test_warning(e):
        show_warning(page, "Esto es una advertencia")
    
    def test_validation_error(e):
        # Simular ValidationError con detalles
        error = ValidationError(
            message="Datos inválidos",
            status_code=422,
            details={
                "errors": [
                    {
                        "field": "email",
                        "message": "value is not a valid email address: There must be something after the @-sign."
                    },
                    {
                        "field": "telefono",
                        "message": "ensure this value has at least 10 characters"
                    }
                ]
            }
        )
        handle_api_error(page, error, "crear socio")
    
    page.add(
        ft.Column(
            [
                ft.Text("Test de Snackbars", size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.ElevatedButton(
                    "Mostrar Success (Verde)",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=test_success,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                    )
                ),
                ft.ElevatedButton(
                    "Mostrar Warning (Naranja)",
                    icon=ft.Icons.WARNING,
                    on_click=test_warning,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE_700,
                        color=ft.Colors.WHITE,
                    )
                ),
                ft.ElevatedButton(
                    "Mostrar ValidationError (Naranja con detalles)",
                    icon=ft.Icons.ERROR,
                    on_click=test_validation_error,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.DEEP_ORANGE_700,
                        color=ft.Colors.WHITE,
                    )
                ),
                ft.Divider(height=20),
                ft.Text("👆 Click en los botones para probar los snackbars", 
                       size=12, 
                       color=ft.Colors.GREY_700),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
