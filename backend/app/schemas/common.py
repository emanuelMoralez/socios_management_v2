"""
Schemas comunes y respuestas genéricas
backend/app/schemas/common.py
"""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime


# ==================== RESPUESTAS GENÉRICAS ====================
class MessageResponse(BaseModel):
    """Respuesta simple con mensaje"""
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Respuesta de éxito genérica"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ==================== PAGINACIÓN ====================
T = TypeVar('T')

class PaginationMeta(BaseModel):
    """Metadata de paginación"""
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Registros por página")
    total: int = Field(..., description="Total de registros")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="¿Hay página siguiente?")
    has_prev: bool = Field(..., description="¿Hay página anterior?")


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica"""
    items: List[T]
    pagination: PaginationMeta
    
    class Config:
        from_attributes = True


# ==================== FILTROS Y ORDENAMIENTO ====================
class OrderBy(BaseModel):
    """Parámetros de ordenamiento"""
    field: str
    direction: str = Field(default="asc", pattern="^(asc|desc)$")


class DateRangeFilter(BaseModel):
    """Filtro por rango de fechas"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ==================== TIMESTAMPS ====================
class TimestampMixin(BaseModel):
    """Mixin para modelos con timestamps"""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== ID GENÉRICO ====================
class IDResponse(BaseModel):
    """Respuesta simple con ID"""
    id: int
    message: str = "Operación exitosa"