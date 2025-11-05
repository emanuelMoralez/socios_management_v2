"""
Modelo de Actividad/Auditoría del Sistema
backend/app/models/actividad.py
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TipoActividad(str, enum.Enum):
    """Tipos de actividad auditables"""
    # Miembros
    MIEMBRO_CREADO = "miembro_creado"
    MIEMBRO_EDITADO = "miembro_editado"
    MIEMBRO_ELIMINADO = "miembro_eliminado"
    MIEMBRO_SUSPENDIDO = "miembro_suspendido"
    MIEMBRO_REACTIVADO = "miembro_reactivado"
    
    # Pagos
    PAGO_REGISTRADO = "pago_registrado"
    PAGO_ANULADO = "pago_anulado"
    
    # Accesos
    ACCESO_PERMITIDO = "acceso_permitido"
    ACCESO_DENEGADO = "acceso_denegado"
    
    # Sistema
    LOGIN_EXITOSO = "login_exitoso"
    LOGIN_FALLIDO = "login_fallido"
    LOGOUT = "logout"
    
    # Configuración
    CATEGORIA_CREADA = "categoria_creada"
    CATEGORIA_EDITADA = "categoria_editada"
    
    # Reportes
    REPORTE_GENERADO = "reporte_generado"
    REPORTE_EXPORTADO = "reporte_exportado"
    
    # Notificaciones
    EMAIL_ENVIADO = "email_enviado"
    RECORDATORIO_MASIVO = "recordatorio_masivo"


class NivelSeveridad(str, enum.Enum):
    """Nivel de importancia de la actividad"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Actividad(Base):
    """
    Registro de auditoría de todas las actividades del sistema
    
    Permite rastrear:
    - Quién hizo qué acción
    - Cuándo se realizó
    - Desde qué IP/dispositivo
    - Datos adicionales en formato JSON
    """
    __tablename__ = "actividades"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tipo de actividad
    tipo = Column(
        SQLEnum(TipoActividad),
        nullable=False,
        index=True
    )
    
    # Severidad
    severidad = Column(
        SQLEnum(NivelSeveridad),
        default=NivelSeveridad.INFO,
        nullable=False
    )
    
    # Usuario que ejecutó la acción
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Descripción legible de la acción
    descripcion = Column(String(500), nullable=False)
    
    # Entidad afectada (ID genérico)
    entidad_tipo = Column(String(50), nullable=True, index=True)  # "miembro", "pago", etc.
    entidad_id = Column(Integer, nullable=True, index=True)
    
    # Datos adicionales en JSON
    datos_adicionales = Column(JSON, nullable=True)
    # Ejemplo: {"miembro_nombre": "Juan Pérez", "monto": 1500, "metodo": "efectivo"}
    
    # Metadatos de la petición
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    fecha_hora = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relación con usuario
    usuario = relationship("Usuario", back_populates="actividades")
    
    def __repr__(self):
        return (
            f"<Actividad(id={self.id}, tipo={self.tipo}, "
            f"usuario_id={self.usuario_id}, fecha={self.fecha_hora})>"
        )
    
    @classmethod
    def crear(
        cls,
        tipo: TipoActividad,
        descripcion: str,
        usuario_id: int = None,
        entidad_tipo: str = None,
        entidad_id: int = None,
        datos_adicionales: dict = None,
        severidad: NivelSeveridad = NivelSeveridad.INFO,
        ip_address: str = None,
        user_agent: str = None
    ):
        """
        Factory method para crear actividades
        
        Uso:
            actividad = Actividad.crear(
                tipo=TipoActividad.PAGO_REGISTRADO,
                descripcion="Pago registrado por Juan Pérez",
                usuario_id=1,
                entidad_tipo="pago",
                entidad_id=123,
                datos_adicionales={
                    "monto": 1500,
                    "miembro": "Juan Pérez",
                    "metodo": "efectivo"
                }
            )
            db.add(actividad)
            db.commit()
        """
        return cls(
            tipo=tipo,
            descripcion=descripcion,
            usuario_id=usuario_id,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            datos_adicionales=datos_adicionales,
            severidad=severidad,
            ip_address=ip_address,
            user_agent=user_agent
        )


# Actualizar Usuario para incluir relación
"""
Agregar en backend/app/models/usuario.py:

from sqlalchemy.orm import relationship

class Usuario(Base):
    # ... campos existentes ...
    
    # Relación con actividades
    actividades = relationship(
        "Actividad",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
"""