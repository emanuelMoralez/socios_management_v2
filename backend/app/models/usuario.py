"""
Modelo Usuario - Sistema de autenticación
backend/app/models/usuario.py
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class RolUsuario(str, enum.Enum):
    """Roles del sistema"""
    SUPER_ADMIN = "super_admin"      # Acceso total
    ADMINISTRADOR = "administrador"  # Gestión completa
    OPERADOR = "operador"            # Registro de datos
    PORTERO = "portero"              # Solo control de acceso
    CONSULTA = "consulta"            # Solo lectura


class Usuario(BaseModel, SoftDeleteMixin):
    """
    Usuario del sistema (no confundir con Miembro/Socio)
    Este modelo es para los operadores del sistema
    """
    __tablename__ = "usuarios"
    
    # Datos de acceso
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Información personal
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    
    # Rol y permisos
    rol = Column(
        SQLEnum(RolUsuario),
        default=RolUsuario.OPERADOR,
        nullable=False
    )
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Último acceso
    last_login = Column(String(255), nullable=True)  # Timestamp ISO
    
    # Relaciones
    accesos_registrados = relationship(
        "Acceso",
        back_populates="registrado_por",
        foreign_keys="Acceso.registrado_por_id"
    )
    
    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"
    
    @property
    def puede_registrar_accesos(self):
        """Verifica si puede registrar accesos"""
        return self.rol in [
            RolUsuario.SUPER_ADMIN,
            RolUsuario.ADMINISTRADOR,
            RolUsuario.OPERADOR,
            RolUsuario.PORTERO
        ]
    
    @property
    def puede_modificar_miembros(self):
        """Verifica si puede modificar miembros"""
        return self.rol in [
            RolUsuario.SUPER_ADMIN,
            RolUsuario.ADMINISTRADOR,
            RolUsuario.OPERADOR
        ]
    
    @property
    def puede_ver_reportes(self):
        """Verifica si puede ver reportes"""
        return self.rol in [
            RolUsuario.SUPER_ADMIN,
            RolUsuario.ADMINISTRADOR
        ]
    
    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol.value})>"