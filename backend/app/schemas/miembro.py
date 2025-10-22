"""
Schemas para modelo Miembro (Socio/Asociado)
backend/app/schemas/miembro.py
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime

from app.models.miembro import EstadoMiembro, TipoDocumento
from app.schemas.common import TimestampMixin


# ==================== CATEGORÍA ====================
class CategoriaBase(BaseModel):
    """Schema base de Categoría"""
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    cuota_base: float = Field(default=0.0, ge=0)
    tiene_cuota_fija: bool = True
    caracteristicas: Optional[str] = None
    modulo_tipo: str = "generico"


class CategoriaCreate(CategoriaBase):
    """Schema para crear categoría"""
    pass


class CategoriaUpdate(BaseModel):
    """Schema para actualizar categoría"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    cuota_base: Optional[float] = Field(None, ge=0)
    tiene_cuota_fija: Optional[bool] = None
    caracteristicas: Optional[str] = None


class CategoriaResponse(CategoriaBase, TimestampMixin):
    """Schema para respuesta de categoría"""
    id: int
    
    class Config:
        from_attributes = True


# ==================== MIEMBRO BASE ====================
class MiembroBase(BaseModel):
    """Schema base de Miembro"""
    tipo_documento: TipoDocumento = TipoDocumento.DNI
    numero_documento: str = Field(..., min_length=5, max_length=20)
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    fecha_nacimiento: Optional[date] = None
    
    # Contacto
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    
    # Domicilio
    direccion: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    
    # Categoría
    categoria_id: Optional[int] = None
    
    # Observaciones
    observaciones: Optional[str] = None
    
    # Tipo de módulo
    modulo_tipo: str = "generico"


# ==================== CREATE ====================
class MiembroCreate(MiembroBase):
    """Schema para crear miembro"""
    fecha_alta: Optional[date] = None
    
    @validator('numero_documento')
    def validar_documento(cls, v):
        # Remover espacios y guiones
        v = v.replace(' ', '').replace('-', '')
        if not v.isdigit():
            raise ValueError('El número de documento debe contener solo dígitos')
        return v


# ==================== UPDATE ====================
class MiembroUpdate(BaseModel):
    """Schema para actualizar miembro"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    fecha_nacimiento: Optional[date] = None
    
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    
    direccion: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    
    categoria_id: Optional[int] = None
    estado: Optional[EstadoMiembro] = None
    observaciones: Optional[str] = None
    foto_url: Optional[str] = None


# ==================== RESPONSE ====================
class MiembroResponse(MiembroBase, TimestampMixin):
    """Schema para respuesta de miembro"""
    id: int
    numero_miembro: str
    fecha_alta: date
    fecha_baja: Optional[date] = None
    estado: EstadoMiembro
    
    # QR
    qr_code: str
    qr_hash: str
    qr_generated_at: str
    
    # Finanzas
    saldo_cuenta: float
    ultima_cuota_pagada: Optional[date] = None
    proximo_vencimiento: Optional[date] = None
    
    # Foto
    foto_url: Optional[str] = None
    
    # Categoría (relación)
    categoria: Optional[CategoriaResponse] = None
    
    # Propiedades calculadas
    nombre_completo: str
    edad: Optional[int] = None
    esta_al_dia: bool
    puede_acceder: bool
    dias_mora: int
    
    class Config:
        from_attributes = True


class MiembroListItem(BaseModel):
    """Schema para lista de miembros (simplificado)"""
    id: int
    numero_miembro: str
    numero_documento: str
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    estado: EstadoMiembro
    saldo_cuenta: float
    categoria: Optional[CategoriaResponse] = None
    fecha_alta: date
    
    class Config:
        from_attributes = True


# ==================== QR ====================
class GenerarQRRequest(BaseModel):
    """Request para generar QR de un miembro"""
    miembro_id: int
    personalizar: bool = True


class QRResponse(BaseModel):
    """Respuesta con datos del QR"""
    qr_code: str
    qr_hash: str
    image_base64: str  # Imagen en base64
    miembro: MiembroListItem


# ==================== BÚSQUEDA ====================
class MiembroSearchParams(BaseModel):
    """Parámetros de búsqueda de miembros"""
    q: Optional[str] = None  # Búsqueda general
    estado: Optional[EstadoMiembro] = None
    categoria_id: Optional[int] = None
    tiene_deuda: Optional[bool] = None
    solo_activos: bool = True


# ==================== ESTADO FINANCIERO ====================
class EstadoFinanciero(BaseModel):
    """Estado financiero de un miembro"""
    miembro_id: int
    numero_miembro: str
    nombre_completo: str
    saldo_cuenta: float
    deuda: float
    ultima_cuota_pagada: Optional[date] = None
    proximo_vencimiento: Optional[date] = None
    dias_mora: int
    estado: EstadoMiembro
    esta_al_dia: bool


# ==================== CAMBIO DE ESTADO ====================
class CambiarEstadoRequest(BaseModel):
    """Request para cambiar estado de miembro"""
    miembro_id: int
    nuevo_estado: EstadoMiembro
    motivo: Optional[str] = None


# ==================== DAR DE BAJA ====================
class DarDeBajaRequest(BaseModel):
    """Request para dar de baja un miembro"""
    miembro_id: int
    motivo: str = Field(..., min_length=10)
    fecha_baja: Optional[date] = None