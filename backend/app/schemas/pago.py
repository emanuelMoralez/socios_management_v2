"""
Schemas para modelo Pago y MovimientoCaja
backend/app/schemas/pago.py
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import date
from decimal import Decimal

from app.models.pago import TipoPago, MetodoPago, EstadoPago
from app.schemas.common import TimestampMixin

# Importación circular evitada con TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schemas.miembro import MiembroListItem


# ==================== PAGO BASE ====================
class PagoBase(BaseModel):
    """Schema base de Pago"""
    miembro_id: int
    tipo: TipoPago
    concepto: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None
    
    monto: float = Field(..., gt=0)
    descuento: float = Field(default=0.0, ge=0)
    recargo: float = Field(default=0.0, ge=0)
    
    metodo_pago: MetodoPago
    fecha_pago: date = Field(default_factory=date.today)
    fecha_vencimiento: Optional[date] = None
    fecha_periodo: Optional[date] = None
    
    observaciones: Optional[str] = None


# ==================== CREATE ====================
class PagoCreate(PagoBase):
    """Schema para crear pago"""
    
    @field_validator('monto', 'descuento', 'recargo')
    @classmethod
    def validar_montos(cls, v):
        if v < 0:
            raise ValueError('Los montos no pueden ser negativos')
        return round(v, 2)


# ==================== UPDATE ====================
class PagoUpdate(BaseModel):
    """Schema para actualizar pago"""
    concepto: Optional[str] = Field(None, min_length=3, max_length=255)
    descripcion: Optional[str] = None
    descuento: Optional[float] = Field(None, ge=0)
    recargo: Optional[float] = Field(None, ge=0)
    estado: Optional[EstadoPago] = None
    observaciones: Optional[str] = None


# ==================== RESPONSE ====================
class PagoResponse(PagoBase, TimestampMixin):
    """Schema para respuesta de pago"""
    id: int
    monto_final: float
    estado: EstadoPago
    numero_comprobante: Optional[str] = None
    comprobante_url: Optional[str] = None
    referencia_externa: Optional[str] = None
    registrado_por_id: Optional[int] = None
    
    # Datos del miembro (nested) - tipado correctamente para evitar errores de serialización
    miembro: Optional["MiembroListItem"] = None
    
    model_config = ConfigDict(from_attributes=True)


class PagoListItem(BaseModel):
    """Schema para lista de pagos (simplificado)"""
    id: int
    numero_comprobante: Optional[str] = None
    fecha_pago: date
    concepto: str
    monto_final: float
    metodo_pago: MetodoPago
    estado: EstadoPago
    miembro_id: int
    nombre_miembro: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== REGISTRAR PAGO RÁPIDO ====================
class RegistrarPagoRapido(BaseModel):
    """Schema para registrar pago rápido (cuota mensual)"""
    miembro_id: int
    monto: float = Field(..., gt=0)
    metodo_pago: MetodoPago = MetodoPago.EFECTIVO
    mes_periodo: int = Field(..., ge=1, le=12)
    anio_periodo: int = Field(..., ge=2020, le=2100)
    aplicar_descuento: bool = False
    porcentaje_descuento: float = Field(default=0, ge=0, le=100)
    observaciones: Optional[str] = None


# ==================== ANULAR PAGO ====================
class AnularPagoRequest(BaseModel):
    """Request para anular un pago"""
    motivo: str = Field(..., min_length=10)


# ==================== MOVIMIENTO CAJA ====================
class MovimientoCajaBase(BaseModel):
    """Schema base de MovimientoCaja"""
    tipo: str = Field(..., pattern="^(ingreso|egreso)$")
    concepto: str = Field(..., min_length=3, max_length=255)
    descripcion: Optional[str] = None
    monto: float = Field(..., gt=0)
    categoria_contable: Optional[str] = Field(None, max_length=100)
    fecha_movimiento: date = Field(default_factory=date.today)
    numero_comprobante: Optional[str] = None
    pago_id: Optional[int] = None


class MovimientoCajaCreate(MovimientoCajaBase):
    """Schema para crear movimiento de caja"""
    pass


class MovimientoCajaResponse(MovimientoCajaBase, TimestampMixin):
    """Schema para respuesta de movimiento"""
    id: int
    comprobante_url: Optional[str] = None
    registrado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== RESUMEN FINANCIERO ====================
class ResumenFinanciero(BaseModel):
    """Resumen financiero general"""
    total_ingresos: float
    total_egresos: float
    saldo: float
    cantidad_pagos: int
    cantidad_miembros_al_dia: int
    cantidad_miembros_morosos: int
    deuda_total: float
    ingresos_mes_actual: float
    ingresos_mes_anterior: float
    periodo: str  # "2025-01"


# ==================== ESTADÍSTICAS ====================
class EstadisticasPago(BaseModel):
    """Estadísticas de pagos"""
    metodo_mas_usado: MetodoPago
    promedio_monto: float
    total_recaudado: float
    pagos_por_mes: dict  # {"2025-01": 150000, "2025-02": 180000}


# ==================== EXPORTAR ====================
class ExportarPagosRequest(BaseModel):
    """Request para exportar pagos"""
    fecha_inicio: date
    fecha_fin: date
    formato: str = Field(default="excel", pattern="^(excel|pdf|csv)$")
    incluir_anulados: bool = False
    miembro_id: Optional[int] = None


# ==================== COMPROBANTE ====================
class GenerarComprobanteRequest(BaseModel):
    """Request para generar comprobante"""
    pago_id: int
    enviar_email: bool = False
    email_destino: Optional[str] = None


# Resolver forward references después de todas las definiciones
from app.schemas.miembro import MiembroListItem
PagoResponse.model_rebuild()