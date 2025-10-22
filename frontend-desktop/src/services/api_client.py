"""
Cliente HTTP para comunicación con la API
frontend-desktop/src/services/api_client.py
"""
import httpx
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/api")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))


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
    
    # ==================== AUTENTICACIÓN ====================
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login y obtener tokens"""
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
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Obtener usuario actual"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/auth/me",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
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
        params = {
            "page": page,
            "page_size": page_size
        }
        if q:
            params["q"] = q
        if estado:
            params["estado"] = estado
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/miembros",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_miembro(self, miembro_id: int) -> Dict[str, Any]:
        """Obtener detalles de un miembro"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/miembros/{miembro_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_miembro(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo miembro"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/miembros",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def update_miembro(self, miembro_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar miembro"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                f"{self.base_url}/miembros/{miembro_id}",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_miembro(self, miembro_id: int) -> Dict[str, Any]:
        """Eliminar miembro"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/miembros/{miembro_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_miembro_qr(self, miembro_id: int) -> bytes:
        """Descargar imagen QR del miembro"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/miembros/{miembro_id}/qr-image",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.content
    
    # ==================== CATEGORÍAS ====================
    
    async def get_categorias(self) -> list:
        """Obtener todas las categorías"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/miembros/categorias",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_categoria(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear categoría"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/miembros/categorias",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
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
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/pagos",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_pago(self, pago_id: int) -> Dict[str, Any]:
        """Obtener detalles de un pago"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/pagos/{pago_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def create_pago(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar pago"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/pagos",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def create_pago_rapido(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar pago rápido"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/pagos/rapido",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def anular_pago(self, pago_id: int, motivo: str) -> Dict[str, Any]:
        """Anular un pago"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/pagos/{pago_id}/anular",
                headers=self._get_headers(),
                json={"pago_id": pago_id, "motivo": motivo}
            )
            response.raise_for_status()
            return response.json()
    
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
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/pagos/resumen/financiero",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
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
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/pagos/movimientos",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def registrar_movimiento_caja(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registrar movimiento de caja"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/pagos/movimientos",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    # ==================== ACCESOS ====================
    
    async def get_accesos(
        self,
        page: int = 1,
        page_size: int = 20,
        miembro_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener historial de accesos"""
        params = {"page": page, "page_size": page_size}
        if miembro_id:
            params["miembro_id"] = miembro_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/accesos/historial",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_resumen_accesos(self) -> Dict[str, Any]:
        """Obtener resumen de accesos"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/accesos/resumen",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def validar_acceso_qr(
        self,
        qr_code: str,
        ubicacion: Optional[str] = None,
        dispositivo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validar acceso mediante código QR"""
        data = {
            "qr_code": qr_code,
        }
        if ubicacion:
            data["ubicacion"] = ubicacion
        if dispositivo_id:
            data["dispositivo_id"] = dispositivo_id
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/accesos/validar-qr",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_estadisticas_accesos(self) -> Dict[str, Any]:
        """Obtener estadísticas de accesos del día"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/accesos/estadisticas",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    # ==================== USUARIOS ====================
    
    async def get_usuarios(self) -> list:
        """Obtener lista de usuarios del sistema"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/usuarios",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    # ==================== REPORTES ====================
    
    async def get_reporte_socios(self, **filters) -> Dict[str, Any]:
        """Obtener reporte de socios"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/reportes/socios",
                headers=self._get_headers(),
                params=filters
            )
            response.raise_for_status()
            return response.json()
    
    async def get_reporte_financiero(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener reporte financiero"""
        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/reportes/financiero",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_reporte_morosidad(self) -> Dict[str, Any]:
        """Obtener reporte de morosidad"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/reportes/morosidad",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def get_reporte_accesos(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener reporte de accesos"""
        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/reportes/accesos",
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()


# Instancia global
api_client = APIClient()