"""
Schemas de auditoría (actividades)
backend/app/schemas/auditoria.py
"""
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.actividad import TipoActividad, NivelSeveridad


class ActividadListItem(BaseModel):
    """Item resumido de actividad para listados"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoActividad
    severidad: NivelSeveridad
    descripcion: str
    usuario_id: Optional[int] = None
    entidad_tipo: Optional[str] = None
    entidad_id: Optional[int] = None
    fecha_hora: datetime


class ActividadDetail(ActividadListItem):
    """Detalle de actividad con metadatos adicionales"""
    datos_adicionales: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
