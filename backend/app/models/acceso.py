"""
Modelo Acceso - Control de acceso con QR
backend/app/models/acceso.py
"""
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Enum as SQLEnum, Text, Boolean, Float
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class TipoAcceso(str, enum.Enum):
    """Tipos de acceso"""
    QR = "qr"                    # Escaneado de QR
    MANUAL = "manual"            # Ingreso manual por portero
    CREDENCIAL = "credencial"    # Tarjeta RFID (futuro)
    RECONOCIMIENTO = "reconocimiento"  # Facial (futuro)


class ResultadoAcceso(str, enum.Enum):
    """Resultado de la validación"""
    PERMITIDO = "permitido"      # Acceso autorizado
    RECHAZADO = "rechazado"      # Acceso denegado
    ADVERTENCIA = "advertencia"  # Permitido con advertencia


class Acceso(BaseModel):
    """
    Registro de accesos/ingresos
    Para control de entradas a instalaciones, eventos, etc.
    """
    __tablename__ = "accesos"
    
    # Relación con miembro
    miembro_id = Column(Integer, ForeignKey("miembros.id"), nullable=False, index=True)
    miembro = relationship("Miembro", back_populates="accesos")
    
    # Datos del acceso
    fecha_hora = Column(String(255), nullable=False, index=True)  # ISO timestamp
    tipo_acceso = Column(SQLEnum(TipoAcceso), nullable=False)
    resultado = Column(SQLEnum(ResultadoAcceso), nullable=False)
    
    # Ubicación/punto de acceso
    ubicacion = Column(String(100), nullable=True)  # "Entrada principal", "Cancha 1"
    dispositivo_id = Column(String(100), nullable=True)  # ID del dispositivo móvil
    
    # QR validado (si corresponde)
    qr_code_escaneado = Column(String(255), nullable=True)
    qr_validacion_exitosa = Column(Boolean, default=True)
    
    # Mensaje/motivo
    mensaje = Column(String(500), nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Usuario que registró (portero)
    registrado_por_id = Column(
        Integer, 
        ForeignKey("usuarios.id"), 
        nullable=True,
        index=True
    )
    registrado_por = relationship(
        "Usuario",
        back_populates="accesos_registrados",
        foreign_keys=[registrado_por_id]
    )
    
    # Geolocalización (opcional)
    latitud = Column(String(50), nullable=True)
    longitud = Column(String(50), nullable=True)
    
    # Datos del estado del miembro al momento del acceso
    estado_miembro_snapshot = Column(String(50), nullable=True)
    saldo_cuenta_snapshot = Column(Float, nullable=True)
    
    @property
    def fue_exitoso(self):
        """Verifica si el acceso fue permitido"""
        return self.resultado == ResultadoAcceso.PERMITIDO
    
    @property
    def requiere_atencion(self):
        """Verifica si requiere atención (advertencia o rechazo)"""
        return self.resultado in [
            ResultadoAcceso.RECHAZADO,
            ResultadoAcceso.ADVERTENCIA
        ]
    
    def __repr__(self):
        return (
            f"<Acceso {self.fecha_hora}: "
            f"Miembro #{self.miembro_id} - {self.resultado.value}>"
        )


class EventoAcceso(BaseModel):
    """
    Eventos especiales (opcional, para futuro)
    Ej: Partidos, torneos, reuniones
    """
    __tablename__ = "eventos_acceso"
    
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    fecha_inicio = Column(String(255), nullable=False)  # ISO timestamp
    fecha_fin = Column(String(255), nullable=True)
    
    ubicacion = Column(String(255), nullable=True)
    
    # Control de acceso específico
    requiere_validacion_especial = Column(Boolean, default=False)
    solo_categoria_especifica = Column(String(100), nullable=True)
    
    # Capacidad
    capacidad_maxima = Column(Integer, nullable=True)
    
    # Relación con accesos
    accesos = relationship("AccesoEvento", back_populates="evento")
    
    def __repr__(self):
        return f"<EventoAcceso {self.nombre}>"


class AccesoEvento(BaseModel):
    """
    Relación entre accesos y eventos
    Para trackear asistencia a eventos específicos
    """
    __tablename__ = "accesos_eventos"
    
    acceso_id = Column(Integer, ForeignKey("accesos.id"), nullable=False)
    acceso = relationship("Acceso")
    
    evento_id = Column(Integer, ForeignKey("eventos_acceso.id"), nullable=False)
    evento = relationship("EventoAcceso", back_populates="accesos")
    
    def __repr__(self):
        return f"<AccesoEvento: Acceso#{self.acceso_id} en Evento#{self.evento_id}>"