"""
Router de gestión de pagos y movimientos
backend/app/routers/pagos.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from datetime import date, datetime
from typing import List, Optional
from calendar import monthrange
import logging

from app.database import get_db
from app.schemas.pago import (
    PagoCreate,
    PagoUpdate,
    PagoResponse,
    PagoListItem,
    RegistrarPagoRapido,
    AnularPagoRequest,
    MovimientoCajaCreate,
    MovimientoCajaResponse,
    ResumenFinanciero
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.models.pago import Pago, MovimientoCaja, EstadoPago, TipoPago, MetodoPago
from app.models.miembro import Miembro, EstadoMiembro
from app.models.usuario import Usuario
from app.utils.dependencies import get_current_user, require_operador, PaginationParams

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== PAGOS ====================

@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_pago(
    pago_data: PagoCreate,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Registrar un pago completo con todos los detalles
    """
    # Verificar que el miembro exista
    miembro = db.query(Miembro).filter(Miembro.id == pago_data.miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Crear pago
    nuevo_pago = Pago(
        miembro_id=pago_data.miembro_id,
        tipo=pago_data.tipo,
        concepto=pago_data.concepto,
        descripcion=pago_data.descripcion,
        monto=pago_data.monto,
        descuento=pago_data.descuento,
        recargo=pago_data.recargo,
        metodo_pago=pago_data.metodo_pago,
        fecha_pago=pago_data.fecha_pago,
        fecha_vencimiento=pago_data.fecha_vencimiento,
        fecha_periodo=pago_data.fecha_periodo,
        observaciones=pago_data.observaciones,
        estado=EstadoPago.APROBADO,
        registrado_por_id=current_user.id
    )
    
    # Calcular monto final
    nuevo_pago.calcular_monto_final()
    
    db.add(nuevo_pago)
    db.flush()  # Para obtener el ID antes del commit
    
    # Generar número de comprobante
    nuevo_pago.numero_comprobante = nuevo_pago.generar_numero_comprobante()
    
    # Actualizar saldo del miembro
    miembro.saldo_cuenta += nuevo_pago.monto_final
    
    # Si es pago de cuota, actualizar fecha de última cuota
    if pago_data.tipo == TipoPago.CUOTA:
        miembro.ultima_cuota_pagada = pago_data.fecha_periodo or date.today()
        
        # Calcular próximo vencimiento (asumiendo mensual)
        if miembro.ultima_cuota_pagada:
            mes = miembro.ultima_cuota_pagada.month
            anio = miembro.ultima_cuota_pagada.year
            
            # Próximo mes
            mes += 1
            if mes > 12:
                mes = 1
                anio += 1
            
            # Día de vencimiento (ej: día 10 de cada mes)
            dia_vencimiento = 10
            ultimo_dia = monthrange(anio, mes)[1]
            dia = min(dia_vencimiento, ultimo_dia)
            
            miembro.proximo_vencimiento = date(anio, mes, dia)
    
    # Si el saldo se vuelve positivo o >= 0, cambiar estado a activo
    if miembro.saldo_cuenta >= 0 and miembro.estado == EstadoMiembro.MOROSO:
        miembro.estado = EstadoMiembro.ACTIVO
    
    # Registrar en movimiento de caja
    movimiento = MovimientoCaja(
        tipo="ingreso",
        concepto=nuevo_pago.concepto,
        descripcion=nuevo_pago.descripcion,
        monto=nuevo_pago.monto_final,
        categoria_contable="Cuotas y Pagos",
        fecha_movimiento=nuevo_pago.fecha_pago,
        numero_comprobante=nuevo_pago.numero_comprobante,
        pago_id=nuevo_pago.id,
        registrado_por_id=current_user.id
    )
    db.add(movimiento)
    
    db.commit()
    db.refresh(nuevo_pago)
    
    logger.info(
        f"[MONEY] Pago registrado: {nuevo_pago.numero_comprobante} - "
        f"Miembro: {miembro.numero_miembro} - ${nuevo_pago.monto_final}"
    )
    
    return nuevo_pago


@router.post("/rapido", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_pago_rapido(
    pago_data: RegistrarPagoRapido,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Registrar pago rápido de cuota mensual
    
    Simplificado para agilizar el cobro en ventanilla.
    """
    # Verificar miembro
    miembro = db.query(Miembro).filter(Miembro.id == pago_data.miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Calcular descuento si aplica
    monto = pago_data.monto
    descuento = 0.0
    
    if pago_data.aplicar_descuento:
        descuento = monto * (pago_data.porcentaje_descuento / 100)
    
    # Fecha del período
    fecha_periodo = date(pago_data.anio_periodo, pago_data.mes_periodo, 1)
    
    # Concepto automático
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    concepto = f"Cuota {meses[pago_data.mes_periodo - 1]} {pago_data.anio_periodo}"
    
    # Crear pago
    nuevo_pago = Pago(
        miembro_id=pago_data.miembro_id,
        tipo=TipoPago.CUOTA,
        concepto=concepto,
        monto=monto,
        descuento=descuento,
        recargo=0.0,
        metodo_pago=pago_data.metodo_pago,
        fecha_pago=date.today(),
        fecha_periodo=fecha_periodo,
        observaciones=pago_data.observaciones,
        estado=EstadoPago.APROBADO,
        registrado_por_id=current_user.id
    )
    
    nuevo_pago.calcular_monto_final()
    
    db.add(nuevo_pago)
    db.flush()
    
    nuevo_pago.numero_comprobante = nuevo_pago.generar_numero_comprobante()
    
    # Actualizar miembro
    miembro.saldo_cuenta += nuevo_pago.monto_final
    miembro.ultima_cuota_pagada = fecha_periodo
    
    if miembro.saldo_cuenta >= 0 and miembro.estado == EstadoMiembro.MOROSO:
        miembro.estado = EstadoMiembro.ACTIVO
    
    # Movimiento de caja
    movimiento = MovimientoCaja(
        tipo="ingreso",
        concepto=concepto,
        monto=nuevo_pago.monto_final,
        categoria_contable="Cuotas",
        fecha_movimiento=date.today(),
        numero_comprobante=nuevo_pago.numero_comprobante,
        pago_id=nuevo_pago.id,
        registrado_por_id=current_user.id
    )
    db.add(movimiento)
    
    db.commit()
    db.refresh(nuevo_pago)
    
    logger.info(f" Pago rápido: {nuevo_pago.numero_comprobante}")
    
    return nuevo_pago


@router.get("", response_model=PaginatedResponse[PagoListItem])
async def listar_pagos(
    miembro_id: Optional[int] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    metodo_pago: Optional[MetodoPago] = Query(None),
    estado: Optional[EstadoPago] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar pagos con filtros y paginación
    """
    query = db.query(Pago)
    
    # Filtros
    if miembro_id:
        query = query.filter(Pago.miembro_id == miembro_id)
    
    if fecha_inicio:
        query = query.filter(Pago.fecha_pago >= fecha_inicio)
    
    if fecha_fin:
        query = query.filter(Pago.fecha_pago <= fecha_fin)
    
    if metodo_pago:
        query = query.filter(Pago.metodo_pago == metodo_pago)
    
    if estado:
        query = query.filter(Pago.estado == estado)
    
    # Total
    total = query.count()
    
    # Paginación
    pagos = query.order_by(Pago.fecha_pago.desc()).offset(pagination.skip).limit(pagination.limit).all()
    
    # Convertir a lista
    items = []
    for pago in pagos:
        miembro = db.query(Miembro).filter(Miembro.id == pago.miembro_id).first()
        items.append(PagoListItem(
            id=pago.id,
            numero_comprobante=pago.numero_comprobante,
            fecha_pago=pago.fecha_pago,
            concepto=pago.concepto,
            monto_final=pago.monto_final,
            metodo_pago=pago.metodo_pago,
            estado=pago.estado,
            miembro_id=pago.miembro_id,
            nombre_miembro=miembro.nombre_completo if miembro else None
        ))
    
    return PaginatedResponse(
        items=items,
        pagination=pagination.get_metadata(total)
    )


# ==================== MOVIMIENTOS DE CAJA ====================

@router.post("/movimientos", response_model=MovimientoCajaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_movimiento(
    movimiento_data: MovimientoCajaCreate,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Registrar movimiento de caja manual (ingreso o egreso)
    
    Para gastos operativos, compras, etc.
    """
    nuevo_movimiento = MovimientoCaja(
        **movimiento_data.model_dump(),
        registrado_por_id=current_user.id
    )
    
    db.add(nuevo_movimiento)
    db.commit()
    db.refresh(nuevo_movimiento)
    
    logger.info(
        f" Movimiento registrado: {nuevo_movimiento.tipo.upper()} - "
        f"${nuevo_movimiento.monto} - {nuevo_movimiento.concepto}"
    )
    
    return nuevo_movimiento


@router.get("/movimientos", response_model=List[MovimientoCajaResponse])
async def listar_movimientos(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    tipo: Optional[str] = Query(None, pattern="^(ingreso|egreso)$"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listar movimientos de caja con filtros
    """
    query = db.query(MovimientoCaja)
    
    if fecha_inicio:
        query = query.filter(MovimientoCaja.fecha_movimiento >= fecha_inicio)
    
    if fecha_fin:
        query = query.filter(MovimientoCaja.fecha_movimiento <= fecha_fin)
    
    if tipo:
        query = query.filter(MovimientoCaja.tipo == tipo)
    
    movimientos = query.order_by(MovimientoCaja.fecha_movimiento.desc()).all()
    
    return movimientos


# ==================== RESUMEN FINANCIERO ====================

@router.get("/resumen/financiero", response_model=ResumenFinanciero)
async def obtener_resumen_financiero(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2020, le=2100),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener resumen financiero del mes
    
    Si no se especifica mes/año, usa el mes actual.
    """
    # Determinar período
    if not mes or not anio:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    # Calcular mes anterior
    mes_anterior = mes - 1
    anio_anterior = anio
    if mes_anterior < 1:
        mes_anterior = 12
        anio_anterior -= 1
    
    # Total ingresos del mes
    total_ingresos = db.query(func.sum(MovimientoCaja.monto)).filter(
        and_(
            MovimientoCaja.tipo == "ingreso",
            extract('month', MovimientoCaja.fecha_movimiento) == mes,
            extract('year', MovimientoCaja.fecha_movimiento) == anio
        )
    ).scalar() or 0.0
    
    # Total egresos del mes
    total_egresos = db.query(func.sum(MovimientoCaja.monto)).filter(
        and_(
            MovimientoCaja.tipo == "egreso",
            extract('month', MovimientoCaja.fecha_movimiento) == mes,
            extract('year', MovimientoCaja.fecha_movimiento) == anio
        )
    ).scalar() or 0.0
    
    # Ingresos mes anterior
    ingresos_mes_anterior = db.query(func.sum(MovimientoCaja.monto)).filter(
        and_(
            MovimientoCaja.tipo == "ingreso",
            extract('month', MovimientoCaja.fecha_movimiento) == mes_anterior,
            extract('year', MovimientoCaja.fecha_movimiento) == anio_anterior
        )
    ).scalar() or 0.0
    
    # Cantidad de pagos del mes
    cantidad_pagos = db.query(func.count(Pago.id)).filter(
        and_(
            extract('month', Pago.fecha_pago) == mes,
            extract('year', Pago.fecha_pago) == anio,
            Pago.estado == EstadoPago.APROBADO
        )
    ).scalar() or 0
    
    # Miembros al día
    cantidad_al_dia = db.query(func.count(Miembro.id)).filter(
        Miembro.estado == EstadoMiembro.ACTIVO,
        Miembro.saldo_cuenta >= 0
    ).scalar() or 0
    
    # Miembros morosos
    cantidad_morosos = db.query(func.count(Miembro.id)).filter(
        Miembro.estado == EstadoMiembro.MOROSO
    ).scalar() or 0
    
    # Deuda total
    deuda_total = db.query(func.sum(Miembro.saldo_cuenta)).filter(
        Miembro.saldo_cuenta < 0
    ).scalar() or 0.0
    deuda_total = abs(deuda_total)
    
    # Saldo
    saldo = total_ingresos - total_egresos
    
    return ResumenFinanciero(
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        saldo=saldo,
        cantidad_pagos=cantidad_pagos,
        cantidad_miembros_al_dia=cantidad_al_dia,
        cantidad_miembros_morosos=cantidad_morosos,
        deuda_total=deuda_total,
        ingresos_mes_actual=total_ingresos,
        ingresos_mes_anterior=ingresos_mes_anterior,
        periodo=f"{anio}-{mes:02d}"
    )


@router.get("/{pago_id}", response_model=PagoResponse)
async def obtener_pago(
    pago_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener detalles de un pago específico
    """
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    return pago


@router.post("/{pago_id}/anular", response_model=MessageResponse)
async def anular_pago(
    pago_id: int,
    anular_data: AnularPagoRequest,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Anular un pago (solo si no está ya anulado)
    
    Revierte el saldo del miembro y marca el pago como cancelado.
    """
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    if pago.estado == EstadoPago.CANCELADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago ya está anulado"
        )
    
    # Obtener miembro
    miembro = db.query(Miembro).filter(Miembro.id == pago.miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Revertir saldo
    miembro.saldo_cuenta -= pago.monto_final
    
    # Si el saldo se vuelve negativo, marcar como moroso
    if miembro.saldo_cuenta < 0:
        miembro.estado = EstadoMiembro.MOROSO
    
    # Anular pago
    pago.estado = EstadoPago.CANCELADO
    pago.observaciones = f"{pago.observaciones or ''}\n[ANULADO] {anular_data.motivo}"
    
    # Registrar movimiento de egreso (devolución)
    movimiento = MovimientoCaja(
        tipo="egreso",
        concepto=f"ANULACIÓN - {pago.concepto}",
        descripcion=anular_data.motivo,
        monto=pago.monto_final,
        categoria_contable="Devoluciones",
        fecha_movimiento=date.today(),
        numero_comprobante=pago.numero_comprobante,
        pago_id=pago.id,
        registrado_por_id=current_user.id
    )
    db.add(movimiento)
    
    db.commit()
    
    logger.warning(
        f"[WARN] Pago anulado: {pago.numero_comprobante} - "
        f"Motivo: {anular_data.motivo}"
    )
    
    return MessageResponse(
        message="Pago anulado correctamente",
        detail=f"Se revirtió ${pago.monto_final} del saldo del miembro"
    )
