"""
Schemas para control de acceso con QR
backend/app/schemas/acceso.py
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.models.acceso import TipoAcceso, ResultadoAcceso
from app.schemas.common import TimestampMixin


# ==================== VALIDACIÓN QR ====================
class ValidarQRRequest(BaseModel):
    """
    Request para validar acceso mediante QR
    ESTE ES EL ENDPOINT PRINCIPAL PARA LA APP MÓVIL
    """
    qr_code: str = Field(
        ...,
        min_length=10,
        description="Código QR escaneado"
    )
    ubicacion: Optional[str] = Field(
        None,
        max_length=100,
        description="Ubicación del punto de acceso (ej: 'Entrada principal')"
    )
    dispositivo_id: Optional[str] = Field(
        None,
        max_length=100,
        description="ID del dispositivo que registra (UUID del móvil)"
    )
    latitud: Optional[str] = Field(None, max_length=50)
    longitud: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = None


# ==================== RESPUESTA VALIDACIÓN ====================
class ValidarQRResponse(BaseModel):
    """
    Respuesta de validación de acceso
    ESTA RESPUESTA LA CONSUME LA APP MÓVIL
    """
    # Resultado
    acceso_permitido: bool = Field(
        ...,
        description="True si puede acceder, False si no"
    )
    resultado: ResultadoAcceso
    nivel_alerta: str = Field(
        ...,
        description="success | warning | error"
    )
    mensaje: str = Field(
        ...,
        description="Mensaje para mostrar al portero"
    )
    
    # Datos del miembro
    miembro: dict = Field(
        ...,
        description="Información del miembro (id, nombre, foto, estado, etc.)"
    )
    
    # Metadata
    acceso_id: int = Field(..., description="ID del registro de acceso")
    timestamp: str = Field(..., description="Timestamp ISO de la validación")
    
    # Información adicional (opcional)
    deuda: Optional[float] = Field(None, description="Monto de deuda si aplica")
    dias_mora: Optional[int] = Field(None, description="Días de mora si aplica")
    
    class Config:
        json_schema_extra = {
            "example": {
                "acceso_permitido": True,
                "resultado": "permitido",
                "nivel_alerta": "success",
                "mensaje": "Acceso autorizado - Bienvenido",
                "miembro": {
                    "id": 123,
                    "numero_miembro": "M-00123",
                    "nombre_completo": "Pérez, Juan",
                    "foto_url": "https://...",
                    "categoria": "Titular",
                    "estado": "activo",
                    "saldo_cuenta": 0.0
                },
                "acceso_id": 456,
                "timestamp": "2025-01-15T10:30:00Z",
                "deuda": None,
                "dias_mora": 0
            }
        }


# ==================== ACCESO MANUAL ====================
class RegistrarAccesoManual(BaseModel):
    """Request para registrar acceso manual (sin QR)"""
    miembro_id: int
    ubicacion: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = None
    forzar_acceso: bool = Field(
        default=False,
        description="True para permitir acceso aunque esté moroso (con autorización)"
    )


# ==================== RESPONSE ====================
class AccesoResponse(TimestampMixin):
    """Schema para respuesta de acceso registrado"""
    id: int
    miembro_id: int
    fecha_hora: str  # ISO timestamp
    tipo_acceso: TipoAcceso
    resultado: ResultadoAcceso
    ubicacion: Optional[str]
    dispositivo_id: Optional[str]
    mensaje: Optional[str]
    observaciones: Optional[str]
    registrado_por_id: Optional[int]
    
    # Snapshot del estado
    estado_miembro_snapshot: Optional[str]
    saldo_cuenta_snapshot: Optional[float]
    
    # Datos del miembro (nested)
    miembro: Optional[dict] = None
    
    class Config:
        from_attributes = True


class AccesoListItem(BaseModel):
    """Schema para lista de accesos (simplificado)"""
    id: int
    fecha_hora: str
    tipo_acceso: TipoAcceso
    resultado: ResultadoAcceso
    ubicacion: Optional[str]
    miembro_id: int
    nombre_miembro: Optional[str] = None
    numero_miembro: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== HISTORIAL ====================
class HistorialAccesosMiembro(BaseModel):
    """Historial de accesos de un miembro específico"""
    miembro_id: int
    numero_miembro: str
    nombre_completo: str
    total_accesos: int
    ultimo_acceso: Optional[str] = None
    accesos_mes_actual: int
    accesos: list[AccesoListItem]


class FiltroHistorialAccesos(BaseModel):
    """Filtros para consultar historial de accesos"""
    miembro_id: Optional[int] = None
    fecha_inicio: Optional[str] = None  # ISO date
    fecha_fin: Optional[str] = None
    resultado: Optional[ResultadoAcceso] = None
    ubicacion: Optional[str] = None
    tipo_acceso: Optional[TipoAcceso] = None


# ==================== ESTADÍSTICAS ====================
class EstadisticasAcceso(BaseModel):
    """Estadísticas de accesos"""
    total_accesos: int
    accesos_permitidos: int
    accesos_rechazados: int
    accesos_advertencia: int
    tasa_exito: float = Field(..., description="Porcentaje de accesos exitosos")
    promedio_diario: float
    hora_pico: Optional[str] = None
    ubicacion_mas_usada: Optional[str] = None


class AccesosPorDia(BaseModel):
    """Accesos agrupados por día"""
    fecha: str
    total: int
    permitidos: int
    rechazados: int


class ResumenAccesos(BaseModel):
    """Resumen de accesos para dashboard"""
    hoy: int
    semana: int
    mes: int
    rechazos_hoy: int
    ultimos_accesos: list[AccesoListItem]


# ==================== EVENTOS ====================
class EventoAccesoBase(BaseModel):
    """Schema base de EventoAcceso"""
    nombre: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None
    fecha_inicio: str  # ISO timestamp
    fecha_fin: Optional[str] = None
    ubicacion: Optional[str] = Field(None, max_length=255)
    capacidad_maxima: Optional[int] = Field(None, gt=0)
    requiere_validacion_especial: bool = False
    solo_categoria_especifica: Optional[str] = None


class EventoAccesoCreate(EventoAccesoBase):
    """Schema para crear evento"""
    pass


class EventoAccesoUpdate(BaseModel):
    """Schema para actualizar evento"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    descripcion: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    ubicacion: Optional[str] = None
    capacidad_maxima: Optional[int] = None
    requiere_validacion_especial: Optional[bool] = None


class EventoAccesoResponse(EventoAccesoBase, TimestampMixin):
    """Schema para respuesta de evento"""
    id: int
    total_asistentes: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ==================== ALERTAS ====================
class AlertaAcceso(BaseModel):
    """Alerta de acceso (para notificaciones)"""
    tipo: str = Field(..., description="rechazado | advertencia | sospechoso")
    mensaje: str
    miembro_id: int
    nombre_miembro: str
    numero_miembro: str
    timestamp: str
    ubicacion: Optional[str] = None
    motivo: str


# ==================== CONFIGURACIÓN DE ACCESO ====================
class ConfiguracionAcceso(BaseModel):
    """Configuración de reglas de acceso"""
    permitir_morosos: bool = False
    deuda_maxima_permitida: float = Field(default=0, ge=0)
    dias_gracia: int = Field(default=5, ge=0)
    validar_horarios: bool = False
    horario_inicio: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    horario_fin: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    ubicaciones_habilitadas: Optional[list[str]] = None
    requiere_foto_obligatoria: bool = False


# ==================== EXPORTAR ACCESOS ====================
class ExportarAccesosRequest(BaseModel):
    """Request para exportar historial de accesos"""
    fecha_inicio: str
    fecha_fin: str
    formato: str = Field(default="excel", pattern="^(excel|pdf|csv)$")
    miembro_id: Optional[int] = None
    ubicacion: Optional[str] = None
    solo_rechazados: bool = False


# ==================== ESTADÍSTICAS DE ACCESO ====================
class EstadisticasAcceso(BaseModel):
    """Estadísticas de accesos del día"""
    total_hoy: int
    entradas_hoy: int
    salidas_hoy: int
    rechazos_hoy: int
    advertencias_hoy: int
    promedio_por_hora: float
    accesos_por_hora: List[dict]
    ultimo_acceso: Optional[dict]
    fecha: str
    
    class Config:
        from_attributes = True