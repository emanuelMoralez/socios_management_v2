"""
Modelos base y mixins para SQLAlchemy
backend/app/models/base.py
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Boolean
from sqlalchemy.sql import func
from app.database import Base


class TimestampMixin:
    """Mixin para agregar timestamps automáticos"""
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        nullable=True
    )


class SoftDeleteMixin:
    """Mixin para soft delete (borrado lógico)"""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def soft_delete(self):
        """Marca el registro como eliminado"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restaura un registro eliminado"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin para auditoría (quién creó/modificó)"""
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)


class BaseModel(Base, TimestampMixin):
    """Modelo base abstracto con timestamps"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"