"""
Router de Auditoría - Consulta de actividades
backend/app/routers/auditoria.py
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.actividad import Actividad, TipoActividad, NivelSeveridad
from app.schemas.auditoria import ActividadListItem, ActividadDetail
from app.schemas.common import PaginatedResponse
from app.utils.dependencies import PaginationParams, require_admin
from app.models.usuario import Usuario

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ActividadListItem])
async def listar_actividades(
    tipo: Optional[TipoActividad] = Query(None, description="Filtrar por tipo de actividad"),
    severidad: Optional[NivelSeveridad] = Query(None, description="Filtrar por severidad"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario ejecutor"),
    entidad_tipo: Optional[str] = Query(None, description="Filtrar por entidad afectada (miembro, pago, acceso)"),
    entidad_id: Optional[int] = Query(None, description="Filtrar por ID de la entidad afectada"),
    fecha_desde: Optional[datetime] = Query(None, description="Filtrar desde fecha/hora (ISO)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Filtrar hasta fecha/hora (ISO)"),
    q: Optional[str] = Query(None, description="Búsqueda en descripción"),
    pagination: PaginationParams = Depends(),
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Listar actividades de auditoría con filtros y paginación
    """
    query = db.query(Actividad)

    if tipo:
        query = query.filter(Actividad.tipo == tipo)
    if severidad:
        query = query.filter(Actividad.severidad == severidad)
    if usuario_id:
        query = query.filter(Actividad.usuario_id == usuario_id)
    if entidad_tipo:
        query = query.filter(Actividad.entidad_tipo == entidad_tipo)
    if entidad_id:
        query = query.filter(Actividad.entidad_id == entidad_id)
    if fecha_desde:
        query = query.filter(Actividad.fecha_hora >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Actividad.fecha_hora <= fecha_hasta)
    if q:
        like = f"%{q}%"
        query = query.filter(Actividad.descripcion.ilike(like))

    total = query.count()
    items = (
        query
        .order_by(Actividad.fecha_hora.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    return {
        "items": items,
        "pagination": pagination.get_metadata(total)
    }


@router.get("/{actividad_id}", response_model=ActividadDetail)
async def obtener_actividad(
    actividad_id: int,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle de una actividad de auditoría por ID
    """
    actividad = db.query(Actividad).filter(Actividad.id == actividad_id).first()
    if not actividad:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada")

    return actividad
