"""
Modelo Miembro - Núcleo genérico (Socio/Asociado)
backend/app/models/miembro.py
"""
from sqlalchemy import (
    Column, Integer, String, Date, Enum as SQLEnum,
    Float, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.models.base import BaseModel, SoftDeleteMixin
from app.models.categoria import Categoria


class EstadoMiembro(str, enum.Enum):
    """Estados posibles de un miembro"""
    ACTIVO = "activo"           # Al día con pagos
    MOROSO = "moroso"           # Cuotas impagas
    SUSPENDIDO = "suspendido"   # Suspendido temporalmente
    BAJA = "baja"               # Dado de baja definitiva


class TipoDocumento(str, enum.Enum):
    """Tipos de documento"""
    DNI = "dni"
    PASAPORTE = "pasaporte"
    CUIL = "cuil"
    CUIT = "cuit"
    OTRO = "otro"


class Miembro(BaseModel, SoftDeleteMixin):
    """
    Modelo genérico de Miembro (Socio/Asociado)
    Base para módulos específicos (clubes, cooperativas)
    """
    __tablename__ = "miembros"
    
    # Identificación única
    numero_miembro = Column(
        String(20), 
        unique=True, 
        nullable=False, 
        index=True
    )  # Ej: "S-00001" o "A-00001"
    
    # Documento
    tipo_documento = Column(
        SQLEnum(TipoDocumento),
        default=TipoDocumento.DNI,
        nullable=False
    )
    numero_documento = Column(String(20), unique=True, nullable=False, index=True)
    
    # Datos personales
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    
    # Contacto
    email = Column(String(255), nullable=True, index=True)
    telefono = Column(String(20), nullable=True)
    celular = Column(String(20), nullable=True)
    
    # Domicilio
    direccion = Column(String(255), nullable=True)
    localidad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    
    # Datos de membresía
    fecha_alta = Column(Date, default=date.today, nullable=False)
    fecha_baja = Column(Date, nullable=True)
    
    # Estado
    estado = Column(
        SQLEnum(EstadoMiembro),
        default=EstadoMiembro.ACTIVO,
        nullable=False,
        index=True
    )
    
    # QR único e inmutable
    qr_code = Column(String(255), unique=True, nullable=False, index=True)
    qr_hash = Column(String(64), unique=True, nullable=False)  # SHA256
    qr_generated_at = Column(String(255), nullable=False)  # ISO timestamp
    
    # Categoría (relación genérica)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    categoria = relationship("Categoria", back_populates="miembros")
    
    # Saldo y finanzas
    saldo_cuenta = Column(Float, default=0.0, nullable=False)
    ultima_cuota_pagada = Column(Date, nullable=True)
    proximo_vencimiento = Column(Date, nullable=True)
    
    # Foto
    foto_url = Column(String(500), nullable=True)
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    # Tipo de módulo (para extensibilidad futura)
    modulo_tipo = Column(
        String(50), 
        default="generico",
        nullable=False
    )  # "club", "cooperativa", etc.
    
    # Metadatos adicionales (JSON-like, extensible)
    metadatos = Column(Text, nullable=True)  # Guardar como JSON string
    
    # Relaciones
    pagos = relationship("Pago", back_populates="miembro")
    accesos = relationship("Acceso", back_populates="miembro")
    
    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"
    
    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        return (
            today.year - self.fecha_nacimiento.year -
            ((today.month, today.day) < 
             (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        )
    
    @property
    def esta_al_dia(self):
        """Verifica si está al día con pagos"""
        return self.estado == EstadoMiembro.ACTIVO and self.saldo_cuenta >= 0
    
    @property
    def puede_acceder(self):
        """Verifica si puede acceder a instalaciones"""
        return self.estado in [EstadoMiembro.ACTIVO]
    
    @property
    def dias_mora(self):
        """Calcula días de mora si corresponde"""
        if not self.proximo_vencimiento:
            return 0
        
        if self.proximo_vencimiento >= date.today():
            return 0
        
        delta = date.today() - self.proximo_vencimiento
        return delta.days
    
    def calcular_deuda(self):
        """Calcula deuda total (valor absoluto si es negativo)"""
        return abs(self.saldo_cuenta) if self.saldo_cuenta < 0 else 0
    
    def __repr__(self):
        return (
            f"<Miembro {self.numero_miembro}: "
            f"{self.nombre_completo} - {self.estado.value}>"
        )