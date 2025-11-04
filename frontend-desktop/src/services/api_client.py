"""
Cliente HTTP para comunicación con la API
frontend-desktop/src/services/api_client.py
"""
import httpx
from typing import Optional, Dict, Any, Union
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/api")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class APIException(Exception):
    """Excepción base para errores de API"""
    def __init__(self, message: str, status_code: int = None, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(APIException):
    """Error de autenticación (401)"""
    def __init__(self, message: str = "No autenticado", status_code: int = 401, details: Any = None):
        super().__init__(message, status_code, details)


class APITimeoutError(APIException):
    """Error de timeout"""
    def __init__(self, message: str = "Timeout", status_code: int = None, details: Any = None):
        super().__init__(message, status_code, details)


class ValidationError(APIException):
    """Error de validación (422)"""
    def __init__(self, message: str = "Datos inválidos", status_code: int = 422, details: Any = None):
        super().__init__(message, status_code, details)


class NotFoundError(APIException):
    """Recurso no encontrado (404)"""
    def __init__(self, message: str = "No encontrado", status_code: int = 404, details: Any = None):
        super().__init__(message, status_code, details)


class APIClient:
    """Cliente para consumir la API del backend"""
    
    def __init__(self):
        self.base_url = API_URL
        self.timeout = API_TIMEOUT
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers para las peticiones"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        response_type: str = "json",
        timeout: Optional[int] = None,
        retry_auth: bool = True,
        **kwargs
    ) -> Union[Dict[str, Any], list, bytes]:
        """
        Método genérico para hacer peticiones HTTP
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Ruta del endpoint (sin base_url)
            response_type: "json" o "bytes"
            timeout: Timeout personalizado (usa self.timeout por defecto)
            retry_auth: Si True, intenta renovar token en caso de 401
            **kwargs: Argumentos adicionales para httpx (params, json, etc.)
        
        Returns:
            Respuesta en formato JSON o bytes
        
        Raises:
            AuthenticationError: Token expirado o inválido
            ValidationError: Datos inválidos (422)
            NotFoundError: Recurso no encontrado (404)
            APITimeoutError: Timeout de petición
            APIException: Otros errores de API
        """
        if timeout is None:
            timeout = self.timeout
        
        url = f"{self.base_url}/{endpoint}"
        
        # Agregar headers con token
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self._get_headers())
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, **kwargs)
                
                # Manejo de errores de autenticación con auto-refresh
                if response.status_code == 401 and retry_auth and self.refresh_token:
                    try:
                        # Intentar renovar token
                        await self.refresh_access_token()
                        # Reintentar request original (sin retry para evitar loop infinito)
                        return await self._request(
                            method, endpoint, response_type, timeout, 
                            retry_auth=False, **kwargs
                        )
                    except Exception:
                        # Si falla el refresh, limpiar tokens y lanzar error
                        self.token = None
                        self.refresh_token = None
                        raise AuthenticationError("Sesión expirada. Por favor inicia sesión nuevamente.")
                
                # Si es 401 sin refresh token o retry ya intentado
                if response.status_code == 401:
                    self.token = None
                    self.refresh_token = None
                    raise AuthenticationError("Sesión expirada. Por favor inicia sesión nuevamente.")
                
                # Manejo de otros códigos de error
                if response.status_code == 404:
                    raise NotFoundError(f"Recurso no encontrado: {endpoint}")
                
                if response.status_code == 422:
                    error_detail = response.json()
                    raise ValidationError(
                        message="Datos inválidos",
                        status_code=422,
                        details=error_detail
                    )
                
                # Para otros errores, usar raise_for_status de httpx
                response.raise_for_status()
                
                # Retornar según tipo de respuesta
                if response_type == "bytes":
                    return response.content
                else:
                    return response.json()
        
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"La petición excedió el tiempo límite de {timeout}s")
        except (AuthenticationError, ValidationError, NotFoundError, APITimeoutError):
            # Re-lanzar excepciones personalizadas
            raise
        except httpx.HTTPStatusError as e:
            # Otros errores HTTP
            raise APIException(f"Error HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            # Errores de red u otros
            raise APIException(f"Error de comunicación con la API: {str(e)}")
    
    # ==================== AUTENTICACIÓN ====================
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login y obtener tokens"""
        # No usar _request aquí porque no tiene token aún
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            
            # Guardar tokens
            self.token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            
            return data
    
    async def refresh_access_token(self) -> None:
        """
        Renovar access token usando refresh token
        
        Raises:
            AuthenticationError: Si el refresh token es inválido o expiró
        """
        if not self.refresh_token:
            raise AuthenticationError("No hay refresh token disponible")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": self.refresh_token}
            )
            
            if response.status_code != 200:
                raise AuthenticationError("No se pudo renovar el token")
            
            data = response.json()
            self.token = data.get("access_token")
            # Actualizar refresh token si viene uno nuevo
            if data.get("refresh_token"):
                self.refresh_token = data.get("refresh_token")
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Obtener usuario actual"""
        return await self._request("GET", "auth/me")
    
    def logout(self):
        """Cerrar sesión (limpiar tokens)"""
        self.token = None
        self.refresh_token = None
    
    # ==================== MIEMBROS ====================
    
    async def get_miembros(
        self,
        page: int = 1,
        page_size: int = 20,
        q: Optional[str] = None,
        estado: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener lista de miembros"""
        params = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        if estado:
            params["estado"] = estado
        
        return await self._request("GET", "miembros", params=params)
    
    async def get_miembro(self, miembro_id: int) -> Dict[str, Any]:
        """Obtener detalles de un miembro"""
        return await self._request("GET", f"miembros/{miembro_id}")
    
    async def create_miembro(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo miembro"""
        return await self._request("POST", "miembros", json=data)
    
    async def update_miembro(self, miembro_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar miembro"""
        return await self._request("PUT", f"miembros/{miembro_id}", json=data)
    
    async def delete_miembro(self, miembro_id: int) -> Dict[str, Any]:
        """Eliminar miembro"""
        return await self._request("DELETE", f"miembros/{miembro_id}")
    
    async def cambiar_estado_miembro(
        self,
        miembro_id: int,
        nuevo_estado: str,
        motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cambiar estado de un miembro (activo, inactivo, suspendido, baja)
        
        Args:
            miembro_id: ID del miembro
            nuevo_estado: Nuevo estado (activo, inactivo, suspendido, baja)
            motivo: Motivo del cambio (opcional)
        
        Returns:
            Miembro actualizado
        """
        data = {"nuevo_estado": nuevo_estado}
        if motivo:
            data["motivo"] = motivo
        
        return await self._request("POST", f"miembros/{miembro_id}/cambiar-estado", json=data)
    
    async def get_miembro_qr(self, miembro_id: int) -> bytes:
        """Descargar imagen QR del miembro"""
        return await self._request("GET", f"miembros/{miembro_id}/qr-image", response_type="bytes")
    
    async def get_miembro_estado_financiero(self, miembro_id: int) -> Dict[str, Any]:
        """
        Obtener estado financiero detallado de un miembro
        
        Returns:
            Dict con saldo, última cuota, días de mora, etc.
        """
        return await self._request("GET", f"miembros/{miembro_id}/estado-financiero")
    
    # ==================== CATEGORÍAS ====================
    
    async def get_categorias(self) -> list:
        """Obtener todas las categorías"""
        return await self._request("GET", "miembros/categorias")
    
    async def create_categoria(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear categoría"""
        return await self._request("POST", "miembros/categorias", json=data)
    
    # ==================== PAGOS ====================
    
    async def get_pagos(
        self,
        page: int = 1,
        page_size: int = 20,
        miembro_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        metodo_pago: Optional[str] = None,
        estado: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener lista de pagos"""
        params = {"page": page, "page_size": page_size}
        if miembro_id:
            params["miembro_id"] = miembro_id
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        if metodo_pago:
            params["metodo_pago"] = metodo_pago
        if estado:
            params["estado"] = estado
        
        return await self._request("GET", "pagos", params=params)
    
    async def get_pago(self, pago_id: int) -> Dict[str, Any]:
        """Obtener detalles de un pago"""
        return await self._request("GET", f"pagos/{pago_id}")
    
    async def create_pago(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar pago"""
        return await self._request("POST", "pagos", json=data)
    
    async def create_pago_rapido(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar pago rápido"""
        return await self._request("POST", "pagos/rapido", json=data)
    
    async def anular_pago(self, pago_id: int, motivo: str) -> Dict[str, Any]:
        """Anular un pago"""
        return await self._request(
            "POST", 
            f"pagos/{pago_id}/anular",
            json={"pago_id": pago_id, "motivo": motivo}
        )
    
    async def get_resumen_financiero(
        self,
        mes: Optional[int] = None,
        anio: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener resumen financiero"""
        params = {}
        if mes:
            params["mes"] = mes
        if anio:
            params["anio"] = anio
        
        return await self._request("GET", "pagos/resumen/financiero", params=params)
    
    async def get_movimientos_caja(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> list:
        """Obtener movimientos de caja"""
        params = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        if tipo:
            params["tipo"] = tipo
        
        return await self._request("GET", "pagos/movimientos", params=params)
    
    async def registrar_movimiento_caja(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar movimiento de caja"""
        return await self._request("POST", "pagos/movimientos", json=data)
    
    # ==================== ACCESOS ====================
    
    async def get_accesos(
        self,
        page: int = 1,
        page_size: int = 20,
        miembro_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        resultado: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener historial de accesos con filtros completos
        
        Args:
            page: Número de página
            page_size: Items por página
            miembro_id: Filtrar por miembro específico
            fecha_inicio: Fecha inicio (ISO format YYYY-MM-DD)
            fecha_fin: Fecha fin (ISO format YYYY-MM-DD)
            resultado: Filtrar por resultado (permitido, rechazado, advertencia)
        
        Returns:
            Respuesta paginada con historial de accesos
        """
        params = {"page": page, "page_size": page_size}
        if miembro_id:
            params["miembro_id"] = miembro_id
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        if resultado:
            params["resultado"] = resultado
        
        return await self._request("GET", "accesos/historial", params=params)
    
    async def get_resumen_accesos(self) -> Dict[str, Any]:
        """
        Obtener resumen de accesos (hoy, semana, mes)
        
        Returns:
            Resumen con totales por período
        """
        return await self._request("GET", "accesos/resumen", timeout=30)
    
    async def validar_acceso_qr(
        self,
        qr_code: str,
        ubicacion: Optional[str] = None,
        dispositivo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validar acceso mediante código QR
        
        Args:
            qr_code: Código QR escaneado (formato: CLUB-ID-CHECKSUM)
            ubicacion: Ubicación del acceso (ej: "Puerta Principal")
            dispositivo_id: ID del dispositivo que registra (opcional)
        
        Returns:
            Resultado de validación con estado (permitido/rechazado) y datos del miembro
        """
        data = {"qr_code": qr_code}
        if ubicacion:
            data["ubicacion"] = ubicacion
        if dispositivo_id:
            data["dispositivo_id"] = dispositivo_id
        
        return await self._request("POST", "accesos/validar-qr", json=data)
    
    async def registrar_acceso_manual(
        self,
        miembro_id: int,
        ubicacion: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registrar acceso manual (sin QR, para backup)
        
        Args:
            miembro_id: ID del miembro
            ubicacion: Ubicación del acceso
            observaciones: Notas adicionales
        
        Returns:
            Registro de acceso creado
        """
        data = {"miembro_id": miembro_id}
        if ubicacion:
            data["ubicacion"] = ubicacion
        if observaciones:
            data["observaciones"] = observaciones
        
        return await self._request("POST", "accesos/manual", json=data)
    
    async def get_estadisticas_accesos(self) -> Dict[str, Any]:
        """
        Obtener estadísticas detalladas de accesos del día
        
        Returns:
            Estadísticas con accesos por hora, top socios, etc.
        """
        return await self._request("GET", "accesos/estadisticas", timeout=30)
    
    # ==================== USUARIOS ====================
    
    async def get_usuarios(self) -> list:
        """Obtener lista de usuarios del sistema"""
        return await self._request("GET", "usuarios")

    # ==================== REPORTES ====================
    
    async def get_dashboard(self) -> Dict[str, Any]:
        """
        Obtener datos del dashboard principal con KPIs
        
        Returns:
            Dict con:
            - total_socios (activos, inactivos, suspendidos)
            - ingresos_mes
            - total_morosidad
            - accesos_hoy
            - gráficos y tendencias
        """
        return await self._request("GET", "reportes/dashboard", timeout=30)
    
    async def get_reporte_socios(self, **filters) -> Dict[str, Any]:
        """
        Obtener reporte de socios con filtros
        
        Args:
            **filters: estado, categoria_id, fecha_desde, fecha_hasta, etc.
        
        Returns:
            Reporte detallado de socios
        """
        return await self._request("GET", "reportes/socios", params=filters)
    
    async def get_reporte_financiero(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener reporte financiero
        
        Returns:
            Ingresos, egresos, balance por período
        """
        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        
        return await self._request("GET", "reportes/financiero", params=params)
    
    async def get_reporte_morosidad(self) -> Dict[str, Any]:
        """
        Obtener reporte de morosidad
        
        Returns:
            Lista de socios morosos con días de mora y montos adeudados
        """
        return await self._request("GET", "reportes/morosidad")
    
    async def get_reporte_accesos(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtener reporte de accesos
        
        Returns:
            Estadísticas de accesos por período
        """
        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        
        return await self._request("GET", "reportes/accesos", params=params)
    
    async def get_ingresos_historicos(self, meses: int = 6) -> Dict[str, Any]:
        """
        Obtener histórico de ingresos y egresos mensuales
        
        Args:
            meses: Cantidad de meses hacia atrás (default: 6)
        
        Returns:
            Dict con:
            - historico: Lista de meses con ingresos, egresos y balance
            - total_meses: Cantidad de meses retornados
            - fecha_consulta: Fecha de la consulta
        """
        return await self._request("GET", f"reportes/ingresos-historicos?meses={meses}")
    
    async def get_accesos_detallados(self, fecha: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener accesos detallados por hora del día
        
        Args:
            fecha: Fecha específica en formato YYYY-MM-DD (default: hoy)
        
        Returns:
            Dict con:
            - fecha: Fecha consultada
            - accesos_por_hora: Lista de 24 elementos (una por hora)
            - estadisticas: Total, permitidos, rechazados, hora pico
        """
        params = {"fecha": fecha} if fecha else {}
        return await self._request("GET", "reportes/accesos-detallados", params=params)

    # ==================== EXPORTACIÓN DE REPORTES ====================
    
    async def exportar_socios_excel(
        self,
        estado: Optional[str] = None,
        categoria_id: Optional[int] = None
    ) -> bytes:
        """
        Exportar lista de socios a Excel
        
        Args:
            estado: Filtrar por estado (ACTIVO, MOROSO, etc.)
            categoria_id: Filtrar por categoría
        
        Returns:
            bytes: Archivo Excel en bytes
        """
        params = {}
        if estado:
            params["estado"] = estado
        if categoria_id:
            params["categoria_id"] = categoria_id
        
        return await self._request(
            "GET",
            "reportes/exportar/socios/excel",
            response_type="bytes",
            timeout=60,
            params=params
        )
    
    async def exportar_pagos_excel(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        miembro_id: Optional[int] = None
    ) -> bytes:
        """
        Exportar lista de pagos a Excel
        
        Args:
            fecha_desde: Fecha inicio (ISO format)
            fecha_hasta: Fecha fin (ISO format)
            miembro_id: Filtrar por miembro específico
        
        Returns:
            bytes: Archivo Excel en bytes
        """
        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        if miembro_id:
            params["miembro_id"] = miembro_id
        
        return await self._request(
            "GET",
            "reportes/exportar/pagos/excel",
            response_type="bytes",
            timeout=60,
            params=params
        )
    
    async def exportar_morosidad_excel(self) -> bytes:
        """
        Exportar reporte de morosidad a Excel
        
        Returns:
            bytes: Archivo Excel en bytes
        """
        return await self._request(
            "GET",
            "reportes/exportar/morosidad/excel",
            response_type="bytes",
            timeout=60
        )
    
    async def exportar_accesos_excel(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> bytes:
        """
        Exportar reporte de accesos a Excel
        
        Args:
            fecha_inicio: Fecha inicio (ISO format)
            fecha_fin: Fecha fin (ISO format)
        
        Returns:
            bytes: Archivo Excel en bytes
        """
        params = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
        
        return await self._request(
            "GET",
            "reportes/exportar/accesos/excel",
            response_type="bytes",
            timeout=60,
            params=params
        )
    
    # ==================== NOTIFICACIONES ====================
    
    async def enviar_recordatorio_individual(
        self,
        miembro_id: int,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enviar recordatorio de cuota a un socio
        
        Args:
            miembro_id: ID del miembro
            email: Email destino (opcional, usa el del miembro si no se provee)
        
        Returns:
            Respuesta del servidor
        """
        data = {"miembro_id": miembro_id}
        if email:
            data["email"] = email
        
        return await self._request(
            "POST",
            "notificaciones/recordatorio",
            json=data,
            timeout=30
        )
    
    async def preview_morosos(
        self,
        solo_morosos: bool = True,
        dias_mora_minimo: int = 5
    ) -> Dict[str, Any]:
        """
        Vista previa de socios que recibirán recordatorios
        (útil antes de enviar masivos)
        
        Args:
            solo_morosos: Si True, solo muestra socios morosos
            dias_mora_minimo: Días mínimos de mora para incluir
        
        Returns:
            Lista de socios con:
            - datos de contacto
            - deuda actual
            - días de mora
            - si tiene email configurado
        """
        params = {
            "solo_morosos": solo_morosos,
            "dias_mora_minimo": dias_mora_minimo
        }
        return await self._request(
            "GET",
            "notificaciones/preview-morosos",
            params=params,
            timeout=30
        )
    
    async def enviar_recordatorios_masivos(
        self,
        solo_morosos: bool = True,
        dias_mora_minimo: int = 5
    ) -> Dict[str, Any]:
        """
        Enviar recordatorios masivos a socios con deuda
        
        Args:
            solo_morosos: Si True, solo envía a socios morosos
            dias_mora_minimo: Días mínimos de mora para enviar
        
        Returns:
            Estadísticas de envío:
            - total_enviados
            - total_fallidos
            - emails_enviados (lista con detalles)
        """
        data = {
            "solo_morosos": solo_morosos,
            "dias_mora_minimo": dias_mora_minimo,
            "incluir_email": True
        }
        
        return await self._request(
            "POST",
            "notificaciones/recordatorios-masivos",
            json=data,
            timeout=120
        )
    
    async def test_email_config(self) -> Dict[str, Any]:
        """
        Probar configuración de email (envía un test al admin)
        
        Returns:
            success: bool - Si el envío fue exitoso
            message: str - Mensaje descriptivo
        """
        return await self._request("GET", "notificaciones/test-email", timeout=30)


# Instancia global
api_client = APIClient()