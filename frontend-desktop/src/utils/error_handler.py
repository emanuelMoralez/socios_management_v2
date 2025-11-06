"""
Utilidad para manejo estandarizado de errores de API
frontend-desktop/src/utils/error_handler.py

Este módulo proporciona una función centralizada para manejar errores
de las llamadas al API, mostrando mensajes apropiados al usuario.
"""
import flet as ft
from src.services.api_client import (
    APIException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APITimeoutError
)


def _show_snackbar(page: ft.Page, message: str, bgcolor: str, duration: int = 3000):
    """
    Helper interno para mostrar snackbars de forma consistente.
    
    Args:
        page: Página de Flet
        message: Mensaje a mostrar
        bgcolor: Color de fondo
        duration: Duración en milisegundos
    """
    snackbar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=bgcolor,
        duration=duration,
    )
    page.overlay.append(snackbar)
    snackbar.open = True
    page.update()


def handle_api_error(page: ft.Page, error: Exception, context: str = "") -> bool:
    """
    Maneja un error de API mostrando un snackbar apropiado al usuario.
    
    Args:
        page: Página de Flet donde mostrar el mensaje
        error: Excepción capturada
        context: Contexto opcional (ej: "crear socio", "cargar pagos")
    
    Returns:
        bool: True si el error fue manejado, False si debe propagarse
        
    Ejemplo:
        ```python
        try:
            data = await api_client.create_miembro(datos)
        except Exception as e:
            if handle_api_error(page, e, "crear socio"):
                return  # Error manejado, salir
            raise  # Error no reconocido, re-lanzar
        ```
    """
    context_msg = f" al {context}" if context else ""
    
    # ValidationError - 422 Unprocessable Entity
    if isinstance(error, ValidationError):
        message = f"⚠️ Datos inválidos{context_msg}"
        
        # Extraer detalles si están disponibles
        if hasattr(error, 'details') and error.details:
            details = error.details
            if isinstance(details, dict):
                # Formato 1: Backend personalizado {"errors": [{"field": "...", "message": "..."}]}
                if "errors" in details and isinstance(details["errors"], list):
                    errors = []
                    for err in details["errors"][:3]:  # Max 3 errores
                        if isinstance(err, dict):
                            field = err.get("field", "campo")
                            msg = err.get("message", "inválido")
                            errors.append(f"• {field}: {msg}")
                    if errors:
                        message += "\n" + "\n".join(errors)
                # Formato 2: FastAPI estándar {"detail": [...]}
                elif "detail" in details and isinstance(details["detail"], list):
                    errors = []
                    for err in details["detail"][:3]:  # Max 3 errores
                        if isinstance(err, dict):
                            field = err.get("loc", [""])[- 1] if "loc" in err else "campo"
                            msg = err.get("msg", "inválido")
                            errors.append(f"• {field}: {msg}")
                    if errors:
                        message += "\n" + "\n".join(errors)
                # Formato 3: Mensaje simple {"detail": "mensaje"}
                elif "detail" in details:
                    message += f"\n{details['detail']}"
            elif isinstance(details, str):
                message += f"\n{details}"
        
        # Adjuntar request_id si existe
        req_id = getattr(error, "request_id", None)
        if not req_id and hasattr(error, "details") and isinstance(error.details, dict):
            req_id = error.details.get("request_id")
        if req_id:
            message += f"\nID: {req_id}"

        _show_snackbar(page, message, ft.Colors.ORANGE_700, 5000)
        return True
    
    # AuthenticationError - 401 Unauthorized
    elif isinstance(error, AuthenticationError):
        message = "🔐 Sesión expirada o no autorizado"
        if context:
            message += f"\n{context.capitalize()} requiere autenticación"
        
        # Adjuntar request_id si existe
        req_id = getattr(error, "request_id", None)
        if req_id:
            message += f"\nID: {req_id}"

        _show_snackbar(page, message, ft.Colors.RED_700, 4000)
        
        # Opcional: redirigir a login después de 2 segundos
        # page.go("/login")  # Descomentar si quieres auto-redirect
        return True
    
    # NotFoundError - 404 Not Found
    elif isinstance(error, NotFoundError):
        resource = context or "recurso solicitado"
        message = f"🔍 No encontrado: {resource}"
        
        if hasattr(error, 'details') and error.details:
            if isinstance(error.details, dict) and "detail" in error.details:
                message += f"\n{error.details['detail']}"
        
        # Adjuntar request_id si existe
        req_id = getattr(error, "request_id", None)
        if req_id:
            message += f"\nID: {req_id}"

        _show_snackbar(page, message, ft.Colors.BLUE_GREY_700, 4000)
        return True
    
    # APITimeoutError - Timeout
    elif isinstance(error, APITimeoutError):
        message = "⏱️ La operación tardó demasiado"
        if context:
            message += f"\n{context.capitalize()} excedió el tiempo límite"
        message += "\nIntenta nuevamente o contacta al administrador"
        
        # Adjuntar request_id si existe
        req_id = getattr(error, "request_id", None)
        if req_id:
            message += f"\nID: {req_id}"

        _show_snackbar(page, message, ft.Colors.DEEP_ORANGE_700, 5000)
        return True
    
    # APIException genérica (4xx, 5xx)
    elif isinstance(error, APIException):
        status = getattr(error, 'status_code', None)
        
        if status and 500 <= status < 600:
            # Error del servidor
            message = "🔧 Error del servidor"
            if context:
                message += f" al {context}"
            message += "\nIntenta nuevamente en unos momentos"
        else:
            # Otro error de API
            message = f"❌ Error{context_msg}"
            if hasattr(error, 'details') and error.details:
                if isinstance(error.details, dict) and "detail" in error.details:
                    message += f"\n{error.details['detail']}"
                elif isinstance(error.details, str):
                    message += f"\n{error.details}"
        
        # Adjuntar request_id si existe
        req_id = getattr(error, "request_id", None)
        if not req_id and hasattr(error, "details") and isinstance(error.details, dict):
            req_id = error.details.get("request_id")
        if req_id:
            message += f"\nID: {req_id}"

        _show_snackbar(page, message, ft.Colors.RED_900, 5000)
        return True
    
    # Error no reconocido (conexión, red, etc.)
    else:
        message = "⚠️ Error de comunicación con la API"
        if context:
            message += f" al {context}"
        message += f"\n{str(error)[:100]}"  # Limitar longitud

        _show_snackbar(page, message, ft.Colors.GREY_800, 5000)
        return True


def show_success(page: ft.Page, message: str):
    """
    Muestra un snackbar de éxito.
    
    Args:
        page: Página de Flet
        message: Mensaje a mostrar
    """
    _show_snackbar(page, f"✅ {message}", ft.Colors.GREEN_700, 3000)


def show_info(page: ft.Page, message: str):
    """
    Muestra un snackbar informativo.
    
    Args:
        page: Página de Flet
        message: Mensaje a mostrar
    """
    _show_snackbar(page, f"ℹ️ {message}", ft.Colors.BLUE_700, 3000)


def show_warning(page: ft.Page, message: str):
    """
    Muestra un snackbar de advertencia.
    
    Args:
        page: Página de Flet
        message: Mensaje a mostrar
    """
    _show_snackbar(page, f"⚠️ {message}", ft.Colors.ORANGE_700, 4000)


def handle_api_error_with_banner(error: Exception, error_banner, context: str = "") -> bool:
    """
    Maneja un error de API mostrando el mensaje en un ErrorBanner dentro del modal.
    
    Esta es una alternativa a handle_api_error() cuando quieres mostrar el error
    dentro del formulario/modal en lugar de un snackbar global.
    
    Args:
        error: Excepción capturada
        error_banner: Instancia de ErrorBanner donde mostrar el error
        context: Contexto opcional (ej: "crear socio")
    
    Returns:
        bool: True si el error fue manejado
        
    Ejemplo:
        ```python
        error_banner = ErrorBanner()
        
        try:
            data = await api_client.create_miembro(datos)
        except Exception as e:
            handle_api_error_with_banner(e, error_banner, "crear socio")
            return  # NO cerrar el modal
        ```
    """
    # ValidationError - mostrar detalles de campos
    if isinstance(error, ValidationError):
        if hasattr(error, 'details') and error.details:
            error_banner.show_validation_errors(error.details)
        else:
            error_banner.show_error(f"Datos inválidos{' al ' + context if context else ''}")
        return True
    
    # AuthenticationError
    elif isinstance(error, AuthenticationError):
        error_banner.update_type("error")
        error_banner.show_error("Sesión expirada. Por favor inicia sesión nuevamente.")
        return True
    
    # NotFoundError
    elif isinstance(error, NotFoundError):
        error_banner.update_type("error")
        message = f"No encontrado: {context}" if context else "Recurso no encontrado"
        error_banner.show_error(message)
        return True
    
    # APITimeoutError
    elif isinstance(error, APITimeoutError):
        error_banner.update_type("error")
        error_banner.show_error("La operación tardó demasiado. Intenta nuevamente.")
        return True
    
    # APIException genérica
    elif isinstance(error, APIException):
        error_banner.update_type("error")
        message = "Error al procesar la solicitud"
        if hasattr(error, 'details') and error.details:
            if isinstance(error.details, dict) and "detail" in error.details:
                message = str(error.details["detail"])
        error_banner.show_error(message)
        return True
    
    # Error genérico
    else:
        error_banner.update_type("error")
        error_banner.show_error(f"Error: {str(error)[:100]}")
        return True
