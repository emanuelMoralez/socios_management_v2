"""
Componente de Paginación Estandarizado
frontend-desktop/src/components/pagination.py
"""
import flet as ft


def create_pagination_controls(pagination: dict, on_page_change) -> ft.Row:
    """
    Crear controles de paginación estandarizados
    
    Args:
        pagination: Dict con información de paginación del backend
        on_page_change: Callback que recibe el número de página
    
    Returns:
        ft.Row con los controles de paginación
    """
    page = pagination.get("page", 1)
    total = pagination.get("total_pages", 1)
    has_prev = pagination.get("has_prev", False)
    has_next = pagination.get("has_next", False)
    
    return ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.FIRST_PAGE,
                disabled=not has_prev,
                on_click=lambda _: on_page_change(1),
                tooltip="Primera página"
            ),
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                disabled=not has_prev,
                on_click=lambda _: on_page_change(page - 1),
                tooltip="Página anterior"
            ),
            ft.Text(f"Página {page} de {total}"),
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                disabled=not has_next,
                on_click=lambda _: on_page_change(page + 1),
                tooltip="Página siguiente"
            ),
            ft.IconButton(
                icon=ft.Icons.LAST_PAGE,
                disabled=not has_next,
                on_click=lambda _: on_page_change(total),
                tooltip="Última página"
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5
    )
