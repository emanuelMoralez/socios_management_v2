"""
Ejemplos de uso del APIClient con manejo de excepciones
frontend-desktop/src/services/api_client_usage_examples.py

Este archivo muestra cómo usar correctamente el api_client con las
excepciones personalizadas para mejor UX.
"""

from src.services.api_client import (
    api_client,
    APIException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APITimeoutError
)
import flet as ft


# ==================== EJEMPLO 1: Login con manejo de errores ====================

async def ejemplo_login(username: str, password: str, page: ft.Page):
    """Ejemplo de login con manejo completo de errores"""
    try:
        # Intentar login
        result = await api_client.login(username, password)
        
        # Si llega aquí, login exitoso
        user = await api_client.get_current_user()
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"¡Bienvenido {user['nombre']}!"),
            bgcolor=ft.colors.GREEN
        )
        page.snack_bar.open = True
        
        # Navegar al dashboard
        # ... código de navegación ...
        
    except AuthenticationError as e:
        # Credenciales inválidas o sesión expirada
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"❌ {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True
        
    except ValidationError as e:
        # Datos inválidos (username vacío, etc.)
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"⚠️ Verifica los datos: {str(e)}"),
            bgcolor=ft.colors.ORANGE
        )
        page.snack_bar.open = True
        
    except APITimeoutError:
        # Servidor no responde
        page.snack_bar = ft.SnackBar(
            content=ft.Text("⏱️ El servidor no responde. Intenta más tarde."),
            bgcolor=ft.colors.AMBER
        )
        page.snack_bar.open = True
        
    except APIException as e:
        # Otros errores de API
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(e)}"),
            bgcolor=ft.colors.RED_400
        )
        page.snack_bar.open = True


# ==================== EJEMPLO 2: Cargar lista con auto-refresh ====================

async def ejemplo_cargar_miembros(page: ft.Page):
    """
    El auto-refresh de tokens es transparente.
    Si el access_token expiró, se renueva automáticamente.
    """
    try:
        # Esta llamada puede renovar el token automáticamente si expiró
        response = await api_client.get_miembros(page=1, page_size=20)
        
        miembros = response["data"]
        # ... mostrar en la UI ...
        
    except AuthenticationError:
        # Solo llega aquí si el refresh_token también expiró
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Sesión expirada. Por favor inicia sesión nuevamente."),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True
        
        # Redirigir al login
        api_client.logout()
        # ... navegar a login ...
        
    except APIException as e:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error al cargar socios: {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True


# ==================== EJEMPLO 3: Crear miembro con validación ====================

async def ejemplo_crear_miembro(data: dict, page: ft.Page):
    """Ejemplo de creación con manejo de errores de validación"""
    try:
        miembro = await api_client.create_miembro(data)
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✅ Socio {miembro['nombre']} creado exitosamente"),
            bgcolor=ft.colors.GREEN
        )
        page.snack_bar.open = True
        
        return miembro
        
    except ValidationError as e:
        # Datos inválidos (email mal formado, campos requeridos, etc.)
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"⚠️ Datos inválidos: {str(e)}"),
            bgcolor=ft.colors.ORANGE
        )
        page.snack_bar.open = True
        return None
        
    except AuthenticationError:
        # Token expirado (se intentó renovar pero falló)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Sesión expirada. Por favor inicia sesión nuevamente."),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True
        return None


# ==================== EJEMPLO 4: Validar QR con estados ====================

async def ejemplo_validar_qr(qr_code: str, page: ft.Page):
    """Ejemplo de validación de QR en control de acceso"""
    try:
        resultado = await api_client.validar_acceso_qr(
            qr_code=qr_code,
            ubicacion="Puerta Principal"
        )
        
        # Verificar resultado
        if resultado["resultado"] == "permitido":
            # VERDE - Acceso permitido
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    f"✅ ACCESO PERMITIDO\n"
                    f"{resultado['miembro']['nombre']} {resultado['miembro']['apellido']}\n"
                    f"Categoría: {resultado['miembro']['categoria_nombre']}"
                ),
                bgcolor=ft.colors.GREEN,
                duration=3000
            )
        
        elif resultado["resultado"] == "advertencia":
            # AMARILLO - Permitido con advertencia
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    f"⚠️ ADVERTENCIA\n"
                    f"{resultado['miembro']['nombre']}\n"
                    f"Motivo: {resultado.get('motivo', 'Deuda pendiente')}"
                ),
                bgcolor=ft.colors.AMBER,
                duration=4000
            )
        
        else:  # rechazado
            # ROJO - Acceso denegado
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    f"❌ ACCESO DENEGADO\n"
                    f"Motivo: {resultado.get('motivo', 'Estado inválido')}"
                ),
                bgcolor=ft.colors.RED,
                duration=5000
            )
        
        page.snack_bar.open = True
        return resultado
        
    except NotFoundError:
        # QR no existe en la base de datos
        page.snack_bar = ft.SnackBar(
            content=ft.Text("❌ Código QR no válido o no registrado"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True
        
    except APIException as e:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True


# ==================== EJEMPLO 5: Exportar con timeout ====================

async def ejemplo_exportar_excel(page: ft.Page, dialog: ft.AlertDialog):
    """Ejemplo de exportación con indicador de carga"""
    try:
        # Mostrar diálogo de carga
        dialog.title = ft.Text("Exportando...")
        dialog.content = ft.Column([
            ft.ProgressRing(),
            ft.Text("Generando archivo Excel, por favor espera...")
        ])
        page.dialog = dialog
        dialog.open = True
        page.update()
        
        # Exportar (timeout de 60s)
        excel_bytes = await api_client.exportar_socios_excel(estado="activo")
        
        # Guardar archivo
        import datetime
        filename = f"socios_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with open(filename, "wb") as f:
            f.write(excel_bytes)
        
        # Cerrar diálogo de carga
        dialog.open = False
        page.update()
        
        # Mostrar éxito
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✅ Archivo exportado: {filename}"),
            bgcolor=ft.colors.GREEN
        )
        page.snack_bar.open = True
        
    except APITimeoutError:
        dialog.open = False
        page.update()
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                "⏱️ La exportación está tardando mucho. "
                "Intenta con menos registros o filtra por categoría."
            ),
            bgcolor=ft.colors.AMBER,
            duration=5000
        )
        page.snack_bar.open = True
        
    except APIException as e:
        dialog.open = False
        page.update()
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error al exportar: {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True


# ==================== EJEMPLO 6: Preview antes de enviar emails ====================

async def ejemplo_enviar_recordatorios(page: ft.Page):
    """Ejemplo de envío masivo con preview"""
    try:
        # 1. Primero obtener preview
        preview = await api_client.preview_morosos(
            solo_morosos=True,
            dias_mora_minimo=5
        )
        
        total_socios = len(preview["socios"])
        con_email = sum(1 for s in preview["socios"] if s.get("email"))
        
        # 2. Mostrar confirmación
        confirmar = await mostrar_dialogo_confirmacion(
            page,
            f"¿Enviar recordatorios a {con_email} socios con email?\n"
            f"({total_socios} socios morosos en total)"
        )
        
        if not confirmar:
            return
        
        # 3. Enviar
        resultado = await api_client.enviar_recordatorios_masivos(
            solo_morosos=True,
            dias_mora_minimo=5
        )
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                f"✅ Recordatorios enviados\n"
                f"Exitosos: {resultado['total_enviados']}\n"
                f"Fallidos: {resultado['total_fallidos']}"
            ),
            bgcolor=ft.colors.GREEN,
            duration=5000
        )
        page.snack_bar.open = True
        
    except APITimeoutError:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("⏱️ El envío está tardando. Se está procesando en background."),
            bgcolor=ft.colors.AMBER
        )
        page.snack_bar.open = True
        
    except APIException as e:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True


async def mostrar_dialogo_confirmacion(page: ft.Page, mensaje: str) -> bool:
    """Helper para mostrar diálogo de confirmación"""
    # Implementación del diálogo...
    pass


# ==================== EJEMPLO 7: Dashboard con auto-refresh ====================

async def ejemplo_cargar_dashboard(page: ft.Page):
    """Ejemplo de carga del dashboard con KPIs"""
    try:
        # El nuevo método get_dashboard() con timeout de 30s
        dashboard_data = await api_client.get_dashboard()
        
        # dashboard_data contiene:
        # - total_socios_activos
        # - total_socios_inactivos
        # - ingresos_mes_actual
        # - total_morosidad
        # - accesos_hoy
        # - graficos (datos para charts)
        
        # Actualizar UI con los datos...
        return dashboard_data
        
    except AuthenticationError:
        # Token expirado, redirigir a login
        api_client.logout()
        # ... navegar a login ...
        
    except APIException as e:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error al cargar dashboard: {str(e)}"),
            bgcolor=ft.colors.RED
        )
        page.snack_bar.open = True
        return None


# ==================== RESUMEN DE MEJORAS ====================

"""
MEJORAS IMPLEMENTADAS:

1. ✅ Auto-refresh de tokens (transparente)
   - Si access_token expira, se renueva automáticamente con refresh_token
   - Solo si ambos expiran, lanza AuthenticationError

2. ✅ Excepciones personalizadas:
   - AuthenticationError (401)
   - ValidationError (422)
   - NotFoundError (404)
   - APITimeoutError (timeout)
   - APIException (otros errores)

3. ✅ Métodos unificados y sin duplicados:
   - get_accesos() con todos los filtros
   - get_estadisticas_accesos() con timeout
   - Eliminados: obtener_historial_accesos, obtener_resumen_accesos, etc.

4. ✅ Métodos nuevos agregados:
   - get_dashboard() - KPIs del panel principal
   - cambiar_estado_miembro() - Cambiar estado con motivo
   - get_miembro_estado_financiero() - Estado financiero detallado
   - registrar_acceso_manual() - Backup sin QR
   - preview_morosos() - Vista previa antes de enviar emails
   - exportar_accesos_excel() - Exportar accesos (estaba duplicado)

5. ✅ Mejor documentación:
   - Docstrings completos con Args y Returns
   - Ejemplos de uso en este archivo
   - Manejo de errores específico por caso de uso

6. ✅ Timeouts apropiados:
   - 30s para operaciones normales
   - 60s para exportaciones Excel
   - 120s para envíos masivos de email

TOTAL DE MÉTODOS: 45+ (organizados, sin duplicados)
"""
