"""
Importación centralizada de todos los modelos
backend/app/models/__init__.py

IMPORTANTE: Este archivo debe importar TODOS los modelos
para que Alembic pueda detectarlos en las migraciones.
"""
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin
from app.models.usuario import Usuario, RolUsuario
from app.models.categoria import Categoria
from app.models.miembro import (
    Miembro,
    EstadoMiembro,
    TipoDocumento
)
from app.models.pago import (
    Pago,
    MovimientoCaja,
    TipoPago,
    MetodoPago,
    EstadoPago
)
from app.models.acceso import (
    Acceso,
    EventoAcceso,
    AccesoEvento,
    TipoAcceso,
    ResultadoAcceso
)

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    
    # Usuario
    "Usuario",
    "RolUsuario",
    
    # Miembro
    "Miembro",
    "Categoria",
    "EstadoMiembro",
    "TipoDocumento",
    
    # Pago
    "Pago",
    "MovimientoCaja",
    "TipoPago",
    "MetodoPago",
    "EstadoPago",
    
    # Acceso
    "Acceso",
    "EventoAcceso",
    "AccesoEvento",
    "TipoAcceso",
    "ResultadoAcceso",
]