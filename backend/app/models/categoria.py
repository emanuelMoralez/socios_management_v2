"""
Modelo Categoria - Categorías de miembros
backend/app/models/categoria.py
"""
from sqlalchemy import Column, String, Float, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Categoria(BaseModel):
    """
    Categorías de miembros (genérico)
    Ej clubes: Titular, Adherente, Cadete
    Ej cooperativas: Residencial, Comercial, Industrial
    """
    __tablename__ = "categorias"
    
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Configuración financiera
    cuota_base = Column(Float, default=0.0, nullable=False)
    tiene_cuota_fija = Column(Boolean, default=True, nullable=False)
    
    # Beneficios/características (JSON-like)
    caracteristicas = Column(Text, nullable=True)
    
    # Tipo de módulo
    modulo_tipo = Column(String(50), default="generico", nullable=False)
    
    # Relaciones
    miembros = relationship("Miembro", back_populates="categoria")
    
    def __repr__(self):
        return f"<Categoria {self.nombre}>"