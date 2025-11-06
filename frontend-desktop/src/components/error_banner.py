"""
Componente reutilizable de Banner de Error para modales
frontend-desktop/src/components/error_banner.py
"""
import flet as ft


class ErrorBanner(ft.Container):
    """
    Banner de error reutilizable para mostrar mensajes dentro de modales/formularios.
    
    Uso:
        ```python
        # 1. Crear el banner
        error_banner = ErrorBanner()
        
        # 2. Agregar al modal/formulario
        ft.Column([
            error_banner,
            campo1,
            campo2,
            ...
        ])
        
        # 3. Mostrar error
        error_banner.show_error("Email inválido")
        
        # 4. Mostrar múltiples errores
        error_banner.show_errors([
            "Email inválido",
            "Teléfono debe tener 10 dígitos"
        ])
        
        # 5. Ocultar
        error_banner.hide()
        ```
    """
    
    def __init__(
        self,
        error_type: str = "validation",  # "validation", "error", "warning"
        **kwargs
    ):
        """
        Inicializar banner de error.
        
        Args:
            error_type: Tipo de error ("validation", "error", "warning")
            **kwargs: Argumentos adicionales para ft.Container
        """
        self.error_type = error_type
        
        # Configuración de colores según tipo
        self.colors = {
            "validation": {
                "bg": ft.Colors.ORANGE_700,
                "icon": ft.Icons.WARNING_AMBER_ROUNDED,
                "icon_color": ft.Colors.WHITE,
            },
            "error": {
                "bg": ft.Colors.RED_700,
                "icon": ft.Icons.ERROR_OUTLINE,
                "icon_color": ft.Colors.WHITE,
            },
            "warning": {
                "bg": ft.Colors.ORANGE_400,
                "icon": ft.Icons.INFO_OUTLINE,
                "icon_color": ft.Colors.WHITE,
            }
        }
        
        # Obtener colores según tipo
        config = self.colors.get(error_type, self.colors["validation"])
        
        # Texto del mensaje (puede ser múltiples líneas)
        self.message_text = ft.Text(
            "",
            color=ft.Colors.WHITE,
            size=13,
            expand=True,
        )
        
        # Botón de cerrar (opcional)
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.WHITE,
            icon_size=16,
            on_click=lambda _: self.hide(),
            tooltip="Cerrar",
        )
        
        # Contenido del banner
        banner_content = ft.Row(
            [
                ft.Icon(
                    config["icon"],
                    color=config["icon_color"],
                    size=20
                ),
                self.message_text,
                self.close_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        
        # Inicializar container
        super().__init__(
            content=banner_content,
            bgcolor=config["bg"],
            padding=12,
            border_radius=8,
            visible=False,  # Oculto por defecto
            animate_opacity=200,  # Animación simple de opacidad
            **kwargs
        )
    
    def show_error(self, message: str, auto_hide: bool = False, duration: int = 5000):
        """
        Mostrar un mensaje de error único.
        
        Args:
            message: Mensaje a mostrar
            auto_hide: Si True, oculta automáticamente después de 'duration'
            duration: Duración en ms antes de ocultar (solo si auto_hide=True)
        """
        self.message_text.value = message
        self.visible = True
        
        if self.page:
            self.page.update()
        
        # Auto-hide solo si está habilitado Y hay página
        if auto_hide and self.page:
            def hide_delayed():
                import time
                time.sleep(duration / 1000)
                self.hide()
            
            import threading
            threading.Thread(target=hide_delayed, daemon=True).start()
    
    def show_errors(self, errors: list, auto_hide: bool = False, duration: int = 5000):
        """
        Mostrar múltiples mensajes de error.
        
        Args:
            errors: Lista de mensajes de error
            auto_hide: Si True, oculta automáticamente después de 'duration'
            duration: Duración en ms antes de ocultar
        """
        if not errors:
            self.hide()
            return
        
        # Formatear múltiples errores como lista
        if len(errors) == 1:
            message = errors[0]
        else:
            message = "\n".join([f"• {err}" for err in errors])
        
        self.show_error(message, auto_hide, duration)
    
    def show_validation_errors(self, error_details: dict):
        """
        Mostrar errores de validación del backend.
        
        Args:
            error_details: Dict con detalles del error (formato backend o FastAPI)
        """
        errors = []
        
        if isinstance(error_details, dict):
            # Formato 1: Backend personalizado {"errors": [...]}
            if "errors" in error_details and isinstance(error_details["errors"], list):
                for err in error_details["errors"][:5]:  # Max 5 errores
                    if isinstance(err, dict):
                        field = err.get("field", "campo")
                        # Simplificar "body -> email" a "email"
                        if " -> " in field:
                            field = field.split(" -> ")[-1]
                        message = err.get("message", "inválido")
                        errors.append(f"{field}: {message}")
            
            # Formato 2: FastAPI estándar {"detail": [...]}
            elif "detail" in error_details and isinstance(error_details["detail"], list):
                for err in error_details["detail"][:5]:
                    if isinstance(err, dict):
                        field = err.get("loc", [""])[- 1] if "loc" in err else "campo"
                        msg = err.get("msg", "inválido")
                        errors.append(f"{field}: {msg}")
            
            # Formato 3: Mensaje simple {"detail": "mensaje"}
            elif "detail" in error_details:
                errors.append(str(error_details["detail"]))
        
        if errors:
            self.show_errors(errors)
        else:
            self.show_error("Datos inválidos. Por favor revisa los campos.")
    
    def hide(self):
        """Ocultar el banner."""
        self.visible = False
        if self.page:
            self.page.update()
    
    def update_type(self, error_type: str):
        """
        Cambiar el tipo de error y actualizar colores.
        
        Args:
            error_type: Nuevo tipo ("validation", "error", "warning")
        """
        if error_type in self.colors:
            self.error_type = error_type
            config = self.colors[error_type]
            self.bgcolor = config["bg"]
            
            # Actualizar icono (primer hijo del Row)
            if isinstance(self.content, ft.Row) and len(self.content.controls) > 0:
                icon = self.content.controls[0]
                if isinstance(icon, ft.Icon):
                    icon.name = config["icon"]
                    icon.color = config["icon_color"]
            
            if self.page:
                self.page.update()


class SuccessBanner(ft.Container):
    """
    Banner de éxito para operaciones completadas.
    Similar a ErrorBanner pero con estilo de éxito.
    """
    
    def __init__(self, **kwargs):
        self.message_text = ft.Text(
            "",
            color=ft.Colors.WHITE,
            size=13,
            expand=True,
        )
        
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.WHITE,
            icon_size=16,
            on_click=lambda _: self.hide(),
            tooltip="Cerrar",
        )
        
        banner_content = ft.Row(
            [
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.WHITE, size=20),
                self.message_text,
                self.close_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        
        super().__init__(
            content=banner_content,
            bgcolor=ft.Colors.GREEN_700,
            padding=12,
            border_radius=8,
            visible=False,
            animate_opacity=200,  # Animación simple de opacidad
            **kwargs
        )
    
    def show(self, message: str, auto_hide: bool = True, duration: int = 3000):
        """Mostrar mensaje de éxito."""
        self.message_text.value = message
        self.visible = True
        
        if self.page:
            self.page.update()
        
        if auto_hide and self.page:
            import asyncio
            async def hide_after_delay():
                await asyncio.sleep(duration / 1000)
                self.hide()
            
            self.page.run_task(hide_after_delay)
    
    def hide(self):
        """Ocultar banner."""
        self.visible = False
        if self.page:
            self.page.update()
