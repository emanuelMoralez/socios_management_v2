"""
Router de gestión de miembros/socios
backend/app/routers/miembros.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import date, datetime
from typing import List, Optional
import logging
import base64

from app.database import get_db
from app.services.audit_service import AuditService
from app.models.actividad import TipoActividad
from app.schemas.miembro import (
    MiembroCreate,
    MiembroUpdate,
    MiembroResponse,
    MiembroListItem,
    GenerarQRRequest,
    QRResponse,
    CambiarEstadoRequest,
    DarDeBajaRequest,
    EstadoFinanciero,
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse
)
from app.schemas.common import PaginatedResponse, MessageResponse, IDResponse
from app.models.miembro import Miembro, Categoria, EstadoMiembro
from app.models.usuario import Usuario
from app.services.qr_service import QRService
from app.utils.dependencies import (
    get_current_user,
    require_operador,
    PaginationParams
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== CATEGORÍAS ====================

@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    categoria_data: CategoriaCreate,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Crear nueva categoría de miembro
    
    Ej: Titular, Adherente, Cadete (clubes)
    Ej: Residencial, Comercial, Industrial (cooperativas)
    """
    # Verificar que no exista
    existe = db.query(Categoria).filter(
        Categoria.nombre == categoria_data.nombre
    ).first()
    
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una categoría con el nombre '{categoria_data.nombre}'"
        )
    
    nueva_categoria = Categoria(**categoria_data.model_dump())
    
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)
    
    logger.info(f"[OK] Categoría creada: {nueva_categoria.nombre}")
    
    return nueva_categoria


@router.get("/categorias", response_model=List[CategoriaResponse])
async def listar_categorias(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar todas las categorías
    """
    categorias = db.query(Categoria).all()
    return categorias


@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
async def actualizar_categoria(
    categoria_id: int,
    categoria_data: CategoriaUpdate,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Actualizar categoría
    """
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    update_data = categoria_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(categoria, field, value)
    
    db.commit()
    db.refresh(categoria)
    
    logger.info(f"[EDIT] Categoría actualizada: {categoria.nombre}")
    
    return categoria


@router.delete("/categorias/{categoria_id}", response_model=MessageResponse)
async def eliminar_categoria(
    categoria_id: int,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Eliminar categoría
    
    Solo se puede eliminar si no tiene miembros asociados.
    """
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    # Verificar que no tenga miembros
    tiene_miembros = db.query(Miembro).filter(
        Miembro.categoria_id == categoria_id
    ).count()
    
    if tiene_miembros > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la categoría porque tiene {tiene_miembros} miembro(s) asociado(s)"
        )
    
    db.delete(categoria)
    db.commit()
    
    logger.info(f"[DELETE] Categoría eliminada: {categoria.nombre}")
    
    return MessageResponse(
        message="Categoría eliminada correctamente"
    )



# ==================== MIEMBROS ====================

@router.post("", response_model=MiembroResponse, status_code=status.HTTP_201_CREATED)
async def crear_miembro(
    miembro_data: MiembroCreate,
    request: Request,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo miembro/socio
    
    Genera automáticamente:
    - Número de miembro único
    - Código QR inmutable
    - Hash de seguridad
    """
    # Verificar que no exista el documento
    existe = db.query(Miembro).filter(
        Miembro.numero_documento == miembro_data.numero_documento
    ).first()
    
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un miembro con el documento {miembro_data.numero_documento}"
        )
    
    # Generar número de miembro único
    ultimo = db.query(Miembro).order_by(Miembro.id.desc()).first()
    siguiente_numero = (ultimo.id + 1) if ultimo else 1
    numero_miembro = f"{settings.NUMERO_MIEMBRO_PREFIX}-{siguiente_numero:0{settings.NUMERO_MIEMBRO_LENGTH}d}"
    
    # Crear miembro (sin QR todavía)
    nuevo_miembro = Miembro(
        numero_miembro=numero_miembro,
        tipo_documento=miembro_data.tipo_documento,
        numero_documento=miembro_data.numero_documento,
        nombre=miembro_data.nombre,
        apellido=miembro_data.apellido,
        fecha_nacimiento=miembro_data.fecha_nacimiento,
        email=miembro_data.email,
        telefono=miembro_data.telefono,
        celular=miembro_data.celular,
        direccion=miembro_data.direccion,
        localidad=miembro_data.localidad,
        provincia=miembro_data.provincia,
        codigo_postal=miembro_data.codigo_postal,
        categoria_id=miembro_data.categoria_id,
        observaciones=miembro_data.observaciones,
        modulo_tipo=miembro_data.modulo_tipo,
        fecha_alta=miembro_data.fecha_alta or date.today(),
        estado=EstadoMiembro.ACTIVO,
        # QR temporal (se actualizará después)
        qr_code="TEMP",
        qr_hash="TEMP",
        qr_generated_at=datetime.utcnow().isoformat()
    )
    
    db.add(nuevo_miembro)
    db.commit()
    db.refresh(nuevo_miembro)
    
    # Generar QR con el ID real
    qr_data = QRService.generar_qr_miembro(
        miembro_id=nuevo_miembro.id,
        numero_documento=nuevo_miembro.numero_documento,
        numero_miembro=numero_miembro,
        nombre_completo=nuevo_miembro.nombre_completo,
        personalizar=True
    )
    
    # Actualizar con datos reales del QR
    nuevo_miembro.qr_code = qr_data["qr_code"]
    nuevo_miembro.qr_hash = qr_data["qr_hash"]
    nuevo_miembro.qr_generated_at = qr_data["timestamp"]
    
    db.commit()
    db.refresh(nuevo_miembro)
    
    # Registrar actividad de auditoría
    AuditService.registrar_miembro_creado(
        db=db,
        usuario_id=current_user.id,
        miembro_id=nuevo_miembro.id,
        miembro_nombre=f"{numero_miembro} - {nuevo_miembro.nombre_completo}",
        request=request
    )
    
    logger.info(f"[OK] Miembro creado: {numero_miembro} - {nuevo_miembro.nombre_completo}")
    
    return nuevo_miembro


@router.get("", response_model=PaginatedResponse[MiembroListItem])
async def listar_miembros(
    q: Optional[str] = Query(None, description="Búsqueda por nombre, apellido o documento"),
    estado: Optional[EstadoMiembro] = Query(None),
    categoria_id: Optional[int] = Query(None),
    solo_activos: bool = Query(True),
    pagination: PaginationParams = Depends(),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar miembros con filtros y paginación
    
    Filtros:
    - q: Búsqueda por nombre, apellido o documento
    - estado: Filtrar por estado
    - categoria_id: Filtrar por categoría
    - solo_activos: Si es True, solo muestra no eliminados
    """
    query = db.query(Miembro)
    
    # Filtro de eliminados
    if solo_activos:
        query = query.filter(Miembro.is_deleted == False)
    
    # Búsqueda general
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Miembro.nombre.ilike(search_term),
                Miembro.apellido.ilike(search_term),
                Miembro.numero_documento.ilike(search_term),
                Miembro.numero_miembro.ilike(search_term)
            )
        )
    
    # Filtro por estado
    if estado:
        query = query.filter(Miembro.estado == estado)
    
    # Filtro por categoría
    if categoria_id:
        query = query.filter(Miembro.categoria_id == categoria_id)
    
    # Total de registros
    total = query.count()
    
    # Paginación
    miembros = query.order_by(Miembro.id.desc()).offset(pagination.skip).limit(pagination.limit).all()
    
    # Convertir a lista simplificada
    items = [
        MiembroListItem(
            id=m.id,
            numero_miembro=m.numero_miembro,
            numero_documento=m.numero_documento,
            nombre_completo=m.nombre_completo,
            email=m.email,
            telefono=m.telefono,
            estado=m.estado,
            saldo_cuenta=m.saldo_cuenta,
            categoria=m.categoria,
            fecha_alta=m.fecha_alta
        )
        for m in miembros
    ]
    
    return PaginatedResponse(
        items=items,
        pagination=pagination.get_metadata(total)
    )


@router.get("/{miembro_id}", response_model=MiembroResponse)
async def obtener_miembro(
    miembro_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles completos de un miembro
    """
    miembro = db.query(Miembro).filter(
        Miembro.id == miembro_id,
        Miembro.is_deleted == False
    ).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    return miembro


@router.put("/{miembro_id}", response_model=MiembroResponse)
async def actualizar_miembro(
    miembro_id: int,
    miembro_data: MiembroUpdate,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Actualizar datos de un miembro
    
    No se puede modificar: número de miembro, documento, QR
    """
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Actualizar solo campos proporcionados
    update_data = miembro_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(miembro, field, value)
    
    db.commit()
    db.refresh(miembro)
    
    logger.info(f"[EDIT] Miembro actualizado: {miembro.numero_miembro}")
    
    return miembro


@router.delete("/{miembro_id}", response_model=MessageResponse)
async def eliminar_miembro(
    miembro_id: int,
    request: Request,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Eliminar miembro (soft delete)
    
    No se elimina físicamente, solo se marca como eliminado.
    """
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Soft delete
    numero_miembro_guardado = miembro.numero_miembro
    nombre_completo_guardado = miembro.nombre_completo
    
    miembro.soft_delete()
    miembro.estado = EstadoMiembro.BAJA
    miembro.fecha_baja = date.today()
    
    db.commit()
    
    # Registrar actividad de auditoría
    AuditService.registrar(
        db=db,
        tipo=TipoActividad.MIEMBRO_ELIMINADO,
        descripcion=f"Miembro {numero_miembro_guardado} - {nombre_completo_guardado} dado de baja (soft delete)",
        usuario_id=current_user.id,
        entidad_tipo="miembro",
        entidad_id=miembro_id,
        datos_adicionales={
            "numero_miembro": numero_miembro_guardado,
            "nombre_completo": nombre_completo_guardado,
            "fecha_baja": date.today().isoformat()
        },
        request=request
    )
    
    logger.info(f"[DELETE] Miembro eliminado: {numero_miembro_guardado}")
    
    return MessageResponse(
        message="Miembro eliminado correctamente",
        detail=f"Miembro {numero_miembro_guardado} dado de baja"
    )


@router.post("/{miembro_id}/cambiar-estado", response_model=MiembroResponse)
async def cambiar_estado_miembro(
    miembro_id: int,
    cambio: CambiarEstadoRequest,
    request: Request,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Cambiar estado de un miembro (activo, moroso, suspendido, baja)
    """
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    estado_anterior = miembro.estado
    miembro.estado = cambio.nuevo_estado
    
    # Si se da de baja, registrar fecha
    if cambio.nuevo_estado == EstadoMiembro.BAJA:
        miembro.fecha_baja = date.today()
    
    # Agregar motivo a observaciones si existe
    if cambio.motivo:
        obs = f"[{datetime.now().strftime('%Y-%m-%d')}] Cambio de estado: {estado_anterior.value} → {cambio.nuevo_estado.value}. Motivo: {cambio.motivo}"
        miembro.observaciones = f"{miembro.observaciones}\n{obs}" if miembro.observaciones else obs
    
    db.commit()
    db.refresh(miembro)
    
    # Registrar actividad de auditoría
    AuditService.registrar(
        db=db,
        tipo=TipoActividad.MIEMBRO_EDITADO,
        descripcion=f"Cambio de estado: {estado_anterior.value} → {cambio.nuevo_estado.value} - {miembro.numero_miembro}",
        usuario_id=current_user.id,
        entidad_tipo="miembro",
        entidad_id=miembro.id,
        datos_adicionales={
            "numero_miembro": miembro.numero_miembro,
            "nombre_completo": miembro.nombre_completo,
            "estado_anterior": estado_anterior.value,
            "estado_nuevo": cambio.nuevo_estado.value,
            "motivo": cambio.motivo
        },
        request=request
    )
    
    logger.info(
        f"[REFRESH] Estado cambiado - Miembro: {miembro.numero_miembro} - "
        f"{estado_anterior.value} → {cambio.nuevo_estado.value}"
    )
    
    return miembro


@router.get("/{miembro_id}/qr-image")
async def descargar_qr_imagen(
    miembro_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Descargar imagen QR del miembro en formato PNG
    
    Útil para imprimir credenciales
    """
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Regenerar imagen QR
    qr_data = QRService.generar_qr_miembro(
        miembro_id=miembro.id,
        numero_documento=miembro.numero_documento,
        numero_miembro=miembro.numero_miembro,
        nombre_completo=miembro.nombre_completo,
        timestamp=miembro.qr_generated_at,
        personalizar=True
    )
    
    # Retornar imagen PNG
    return Response(
        content=qr_data["image_bytes"],
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=qr_{miembro.numero_miembro}.png"
        }
    )


@router.get("/{miembro_id}/estado-financiero", response_model=EstadoFinanciero)
async def obtener_estado_financiero(
    miembro_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estado financiero detallado de un miembro
    """
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    return EstadoFinanciero(
        miembro_id=miembro.id,
        numero_miembro=miembro.numero_miembro,
        nombre_completo=miembro.nombre_completo,
        saldo_cuenta=miembro.saldo_cuenta,
        deuda=miembro.calcular_deuda(),
        ultima_cuota_pagada=miembro.ultima_cuota_pagada,
        proximo_vencimiento=miembro.proximo_vencimiento,
        dias_mora=miembro.dias_mora,
        estado=miembro.estado,
        esta_al_dia=miembro.esta_al_dia
    )