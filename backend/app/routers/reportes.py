"""
Router de Reportes y Estadísticas
backend/app/routers/reportes.py
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from app.database import get_db
from app.models.miembro import Miembro, Categoria, EstadoMiembro
from app.models.pago import Pago, MovimientoCaja, EstadoPago
from app.models.acceso import Acceso, ResultadoAcceso
from app.models.usuario import Usuario
from app.utils.dependencies import get_current_user
from app.schemas.common import MessageResponse
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== REPORTE DE SOCIOS ====================

@router.get("/socios")
async def obtener_reporte_socios(
    estado: Optional[EstadoMiembro] = Query(None),
    categoria_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reporte general de socios
    
    Incluye:
    - Total de socios
    - Distribución por estado
    - Distribución por categoría
    - Estadísticas generales
    """
    # Query base
    query = db.query(Miembro).filter(Miembro.is_deleted == False)
    
    # Aplicar filtros opcionales
    if estado:
        query = query.filter(Miembro.estado == estado)
    if categoria_id:
        query = query.filter(Miembro.categoria_id == categoria_id)
    
    # Total de socios
    total = query.count()
    
    # Por estado
    activos = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.ACTIVO
    ).scalar() or 0
    
    morosos = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.MOROSO
    ).scalar() or 0
    
    suspendidos = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.SUSPENDIDO
    ).scalar() or 0
    
    bajas = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.BAJA
    ).scalar() or 0
    
    # Por categoría
    categorias = db.query(
        Categoria.nombre,
        func.count(Miembro.id).label('cantidad')
    ).join(
        Miembro, Miembro.categoria_id == Categoria.id
    ).filter(
        Miembro.is_deleted == False
    ).group_by(
        Categoria.nombre
    ).all()
    
    por_categoria = [
        {"nombre": cat.nombre, "cantidad": cat.cantidad}
        for cat in categorias
    ]
    
    # Altas recientes (último mes)
    hace_un_mes = date.today() - timedelta(days=30)
    altas_recientes = db.query(func.count(Miembro.id)).filter(
        Miembro.fecha_alta >= hace_un_mes,
        Miembro.is_deleted == False
    ).scalar() or 0
    
    # Bajas recientes (último mes)
    bajas_recientes = db.query(func.count(Miembro.id)).filter(
        Miembro.fecha_baja >= hace_un_mes,
        Miembro.is_deleted == False
    ).scalar() or 0
    
    # Promedio de edad (si tienes fecha_nacimiento)
    edades = db.query(Miembro.fecha_nacimiento).filter(
        Miembro.fecha_nacimiento.isnot(None),
        Miembro.is_deleted == False
    ).all()
    
    if edades:
        hoy = date.today()
        edad_promedio = sum(
            (hoy - e.fecha_nacimiento).days // 365
            for e in edades
        ) / len(edades)
    else:
        edad_promedio = 0
    
    return {
        "total": total,
        "activos": activos,
        "morosos": morosos,
        "suspendidos": suspendidos,
        "bajas": bajas,
        "por_categoria": por_categoria,
        "altas_recientes": altas_recientes,
        "bajas_recientes": bajas_recientes,
        "edad_promedio": round(edad_promedio, 1),
        "fecha_reporte": date.today().isoformat()
    }


# ==================== REPORTE FINANCIERO ====================

@router.get("/financiero")
async def obtener_reporte_financiero(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reporte financiero detallado
    
    Incluye:
    - Ingresos y egresos del período
    - Balance
    - Ingresos por concepto
    - Comparativa con período anterior
    """
    # Determinar período
    if not fecha_desde or not fecha_hasta:
        # Por defecto: último mes
        fecha_hasta_obj = date.today()
        fecha_desde_obj = fecha_hasta_obj - timedelta(days=30)
    else:
        fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
        fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
    
    # Total ingresos
    total_ingresos = db.query(func.sum(MovimientoCaja.monto)).filter(
        MovimientoCaja.tipo == "ingreso",
        MovimientoCaja.fecha_movimiento >= fecha_desde_obj,
        MovimientoCaja.fecha_movimiento <= fecha_hasta_obj
    ).scalar() or 0.0
    
    # Total egresos
    total_egresos = db.query(func.sum(MovimientoCaja.monto)).filter(
        MovimientoCaja.tipo == "egreso",
        MovimientoCaja.fecha_movimiento >= fecha_desde_obj,
        MovimientoCaja.fecha_movimiento <= fecha_hasta_obj
    ).scalar() or 0.0
    
    # Balance
    balance = total_ingresos - total_egresos
    
    # Ingresos por concepto
    ingresos_detalle = db.query(
        MovimientoCaja.concepto,
        func.count(MovimientoCaja.id).label('cantidad'),
        func.sum(MovimientoCaja.monto).label('total')
    ).filter(
        MovimientoCaja.tipo == "ingreso",
        MovimientoCaja.fecha_movimiento >= fecha_desde_obj,
        MovimientoCaja.fecha_movimiento <= fecha_hasta_obj
    ).group_by(
        MovimientoCaja.concepto
    ).all()
    
    ingresos_detalle_list = [
        {
            "concepto": ing.concepto,
            "cantidad": ing.cantidad,
            "total": float(ing.total)
        }
        for ing in ingresos_detalle
    ]
    
    # Egresos por categoría
    egresos_detalle = db.query(
        MovimientoCaja.categoria_contable,
        func.count(MovimientoCaja.id).label('cantidad'),
        func.sum(MovimientoCaja.monto).label('total')
    ).filter(
        MovimientoCaja.tipo == "egreso",
        MovimientoCaja.fecha_movimiento >= fecha_desde_obj,
        MovimientoCaja.fecha_movimiento <= fecha_hasta_obj
    ).group_by(
        MovimientoCaja.categoria_contable
    ).all()
    
    egresos_detalle_list = [
        {
            "categoria": egr.categoria_contable or "Sin categoría",
            "cantidad": egr.cantidad,
            "total": float(egr.total)
        }
        for egr in egresos_detalle
    ]
    
    # Cantidad de transacciones
    cantidad_transacciones = db.query(func.count(MovimientoCaja.id)).filter(
        MovimientoCaja.fecha_movimiento >= fecha_desde_obj,
        MovimientoCaja.fecha_movimiento <= fecha_hasta_obj
    ).scalar() or 0
    
    # Promedio de ingreso
    promedio_ingreso = total_ingresos / len(ingresos_detalle) if ingresos_detalle else 0
    
    return {
        "total_ingresos": float(total_ingresos),
        "total_egresos": float(total_egresos),
        "balance": float(balance),
        "ingresos_detalle": ingresos_detalle_list,
        "egresos_detalle": egresos_detalle_list,
        "cantidad_transacciones": cantidad_transacciones,
        "promedio_ingreso": float(promedio_ingreso),
        "fecha_desde": fecha_desde_obj.isoformat(),
        "fecha_hasta": fecha_hasta_obj.isoformat(),
        "periodo_dias": (fecha_hasta_obj - fecha_desde_obj).days
    }


# ==================== REPORTE DE MOROSIDAD ====================

@router.get("/morosidad")
async def obtener_reporte_morosidad(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reporte de morosidad
    
    Lista de socios con deudas, ordenados por monto de deuda.
    """
    # Socios morosos (saldo negativo)
    morosos = db.query(Miembro).filter(
        Miembro.is_deleted == False,
        Miembro.saldo_cuenta < 0
    ).order_by(
        Miembro.saldo_cuenta.asc()  # Los más endeudados primero
    ).all()
    
    morosos_list = []
    total_deuda = 0.0
    
    for miembro in morosos:
        deuda = abs(miembro.saldo_cuenta)
        total_deuda += deuda
        
        # Calcular días de mora
        dias_mora = 0
        if miembro.proximo_vencimiento:
            if miembro.proximo_vencimiento < date.today():
                dias_mora = (date.today() - miembro.proximo_vencimiento).days
        
        morosos_list.append({
            "id": miembro.id,
            "numero_miembro": miembro.numero_miembro,
            "nombre_completo": miembro.nombre_completo,
            "email": miembro.email,
            "telefono": miembro.telefono or miembro.celular,
            "deuda": float(deuda),
            "dias_mora": dias_mora,
            "ultima_cuota_pagada": miembro.ultima_cuota_pagada.isoformat() if miembro.ultima_cuota_pagada else None,
            "categoria": miembro.categoria.nombre if miembro.categoria else None,
            "estado": miembro.estado.value
        })
    
    # Estadísticas
    cantidad_morosos = len(morosos_list)
    deuda_promedio = total_deuda / cantidad_morosos if cantidad_morosos > 0 else 0
    
    # Rangos de deuda
    rango_0_500 = sum(1 for m in morosos_list if m["deuda"] < 500)
    rango_500_1000 = sum(1 for m in morosos_list if 500 <= m["deuda"] < 1000)
    rango_1000_mas = sum(1 for m in morosos_list if m["deuda"] >= 1000)
    
    return {
        "cantidad_morosos": cantidad_morosos,
        "total_deuda": float(total_deuda),
        "deuda_promedio": float(deuda_promedio),
        "morosos": morosos_list,
        "por_rango": {
            "menos_500": rango_0_500,
            "500_a_1000": rango_500_1000,
            "mas_1000": rango_1000_mas
        },
        "fecha_reporte": date.today().isoformat()
    }


# ==================== REPORTE DE ACCESOS ====================

@router.get("/accesos")
async def obtener_reporte_accesos(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reporte de accesos
    
    Estadísticas de control de acceso en un período.
    """
    # Determinar período
    if not fecha_desde or not fecha_hasta:
        # Por defecto: última semana
        fecha_hasta_obj = date.today()
        fecha_desde_obj = fecha_hasta_obj - timedelta(days=7)
    else:
        fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
        fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
    
    inicio = datetime.combine(fecha_desde_obj, datetime.min.time())
    fin = datetime.combine(fecha_hasta_obj, datetime.max.time())
    
    # Total de accesos
    total_accesos = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio.isoformat(),
        Acceso.fecha_hora <= fin.isoformat()
    ).scalar() or 0
    
    # Por resultado
    permitidos = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio.isoformat(),
        Acceso.fecha_hora <= fin.isoformat(),
        Acceso.resultado == ResultadoAcceso.PERMITIDO
    ).scalar() or 0
    
    rechazados = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio.isoformat(),
        Acceso.fecha_hora <= fin.isoformat(),
        Acceso.resultado == ResultadoAcceso.RECHAZADO
    ).scalar() or 0
    
    advertencias = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio.isoformat(),
        Acceso.fecha_hora <= fin.isoformat(),
        Acceso.resultado == ResultadoAcceso.ADVERTENCIA
    ).scalar() or 0
    
    # Accesos por día
    accesos_por_dia = []
    current_date = fecha_desde_obj
    
    while current_date <= fecha_hasta_obj:
        inicio_dia = datetime.combine(current_date, datetime.min.time())
        fin_dia = datetime.combine(current_date, datetime.max.time())
        
        cantidad = db.query(func.count(Acceso.id)).filter(
            Acceso.fecha_hora >= inicio_dia.isoformat(),
            Acceso.fecha_hora <= fin_dia.isoformat()
        ).scalar() or 0
        
        accesos_por_dia.append({
            "fecha": current_date.isoformat(),
            "cantidad": cantidad
        })
        
        current_date += timedelta(days=1)
    
    # Top 10 socios con más accesos
    top_socios = db.query(
        Miembro.numero_miembro,
        Miembro.nombre_completo,
        func.count(Acceso.id).label('cantidad_accesos')
    ).join(
        Acceso, Acceso.miembro_id == Miembro.id
    ).filter(
        Acceso.fecha_hora >= inicio.isoformat(),
        Acceso.fecha_hora <= fin.isoformat()
    ).group_by(
        Miembro.id,
        Miembro.numero_miembro,
        Miembro.nombre_completo
    ).order_by(
        func.count(Acceso.id).desc()
    ).limit(10).all()
    
    top_socios_list = [
        {
            "numero_miembro": s.numero_miembro,
            "nombre_completo": s.nombre_completo,
            "cantidad_accesos": s.cantidad_accesos
        }
        for s in top_socios
    ]
    
    # Promedio diario
    dias = (fecha_hasta_obj - fecha_desde_obj).days + 1
    promedio_diario = total_accesos / dias if dias > 0 else 0
    
    return {
        "total_accesos": total_accesos,
        "permitidos": permitidos,
        "rechazados": rechazados,
        "advertencias": advertencias,
        "promedio_diario": round(promedio_diario, 1),
        "accesos_por_dia": accesos_por_dia,
        "top_socios": top_socios_list,
        "fecha_desde": fecha_desde_obj.isoformat(),
        "fecha_hasta": fecha_hasta_obj.isoformat(),
        "periodo_dias": dias
    }


# ==================== REPORTE CONSOLIDADO ====================

@router.get("/dashboard")
async def obtener_reporte_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reporte consolidado para dashboard principal
    
    Vista general rápida del estado del sistema.
    """
    hoy = date.today()
    
    # Socios
    total_socios = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False
    ).scalar() or 0
    
    socios_activos = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.ACTIVO
    ).scalar() or 0
    
    socios_morosos = db.query(func.count(Miembro.id)).filter(
        Miembro.is_deleted == False,
        Miembro.estado == EstadoMiembro.MOROSO
    ).scalar() or 0
    
    # Finanzas del mes actual
    inicio_mes = hoy.replace(day=1)
    
    ingresos_mes = db.query(func.sum(MovimientoCaja.monto)).filter(
        MovimientoCaja.tipo == "ingreso",
        MovimientoCaja.fecha_movimiento >= inicio_mes
    ).scalar() or 0.0
    
    egresos_mes = db.query(func.sum(MovimientoCaja.monto)).filter(
        MovimientoCaja.tipo == "egreso",
        MovimientoCaja.fecha_movimiento >= inicio_mes
    ).scalar() or 0.0
    
    # Accesos del día
    inicio_hoy = datetime.combine(hoy, datetime.min.time())
    fin_hoy = datetime.combine(hoy, datetime.max.time())
    
    accesos_hoy = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio_hoy.isoformat(),
        Acceso.fecha_hora <= fin_hoy.isoformat()
    ).scalar() or 0
    
    return {
        "socios": {
            "total": total_socios,
            "activos": socios_activos,
            "morosos": socios_morosos,
            "porcentaje_morosos": round(socios_morosos / total_socios * 100, 1) if total_socios > 0 else 0
        },
        "finanzas_mes": {
            "ingresos": float(ingresos_mes),
            "egresos": float(egresos_mes),
            "balance": float(ingresos_mes - egresos_mes)
        },
        "accesos": {
            "hoy": accesos_hoy
        },
        "fecha": hoy.isoformat()
    }

    """
Endpoints de Exportación - Agregar a reportes.py
backend/app/routers/reportes.py (AGREGAR AL FINAL)
"""

from fastapi.responses import StreamingResponse

# Agregar estos imports al inicio del archivo
from app.services.export_service import ExportService

# Agregar estos endpoints al final del archivo reportes.py:

@router.get("/exportar/socios/excel")
async def exportar_socios_excel(
    estado: Optional[str] = Query(None),
    categoria_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exportar lista de socios a Excel
    """
    try:
        # Obtener socios con filtros
        query = db.query(Miembro).filter(Miembro.is_deleted == False)
        
        if estado:
            query = query.filter(Miembro.estado == estado)
        if categoria_id:
            query = query.filter(Miembro.categoria_id == categoria_id)
        
        socios = query.all()
        
        # Convertir a diccionarios
        socios_data = []
        for socio in socios:
            socios_data.append({
                "numero_miembro": socio.numero_miembro,
                "numero_documento": socio.numero_documento,
                "nombre_completo": socio.nombre_completo,
                "email": socio.email,
                "telefono": socio.telefono or socio.celular,
                "estado": socio.estado.value,
                "categoria": {"nombre": socio.categoria.nombre} if socio.categoria else None,
                "saldo_cuenta": socio.saldo_cuenta,
                "fecha_alta": socio.fecha_alta
            })
        
        # Generar Excel
        excel_file = ExportService.exportar_socios_excel(socios_data)
        
        # Retornar como descarga
        filename = f"socios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exportando socios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar: {str(e)}"
        )


@router.get("/exportar/pagos/excel")
async def exportar_pagos_excel(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    miembro_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exportar lista de pagos a Excel
    """
    try:
        query = db.query(Pago)
        
        if fecha_desde:
            fecha_desde_obj = datetime.fromisoformat(fecha_desde).date()
            query = query.filter(Pago.fecha_pago >= fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.fromisoformat(fecha_hasta).date()
            query = query.filter(Pago.fecha_pago <= fecha_hasta_obj)
        
        if miembro_id:
            query = query.filter(Pago.miembro_id == miembro_id)
        
        pagos = query.order_by(Pago.fecha_pago.desc()).all()
        
        # Convertir a diccionarios
        pagos_data = []
        for pago in pagos:
            miembro = db.query(Miembro).filter(Miembro.id == pago.miembro_id).first()
            pagos_data.append({
                "numero_comprobante": pago.numero_comprobante,
                "fecha_pago": pago.fecha_pago,
                "nombre_miembro": miembro.nombre_completo if miembro else "",
                "miembro": {"numero_miembro": miembro.numero_miembro} if miembro else None,
                "concepto": pago.concepto,
                "monto": pago.monto,
                "descuento": pago.descuento,
                "recargo": pago.recargo,
                "monto_final": pago.monto_final,
                "metodo_pago": pago.metodo_pago.value,
                "estado": pago.estado.value
            })
        
        # Generar Excel
        excel_file = ExportService.exportar_pagos_excel(pagos_data)
        
        filename = f"pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exportando pagos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar: {str(e)}"
        )


@router.get("/exportar/morosidad/excel")
async def exportar_morosidad_excel(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exportar reporte de morosidad a Excel
    """
    try:
        # Obtener morosos
        morosos = db.query(Miembro).filter(
            Miembro.is_deleted == False,
            Miembro.saldo_cuenta < 0
        ).order_by(Miembro.saldo_cuenta.asc()).all()
        
        # Convertir a diccionarios
        morosos_data = []
        for miembro in morosos:
            morosos_data.append({
                "numero_miembro": miembro.numero_miembro,
                "nombre_completo": miembro.nombre_completo,
                "email": miembro.email,
                "telefono": miembro.telefono or miembro.celular,
                "deuda": abs(miembro.saldo_cuenta),
                "dias_mora": miembro.dias_mora,
                "ultima_cuota_pagada": miembro.ultima_cuota_pagada,
                "categoria": miembro.categoria.nombre if miembro.categoria else ""
            })
        
        # Generar Excel
        excel_file = ExportService.exportar_morosidad_excel(morosos_data)
        
        filename = f"morosidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exportando morosidad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar: {str(e)}"
        )


@router.get("/exportar/accesos/excel")
async def exportar_accesos_excel(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exportar accesos a Excel
    """
    try:
        # Construir query
        query = db.query(Acceso)
        
        if fecha_inicio:
            query = query.filter(Acceso.fecha_hora >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(Acceso.fecha_hora <= fecha_fin)
        
        accesos = query.order_by(Acceso.fecha_hora.desc()).all()
        
        # Convertir a diccionarios
        accesos_data = []
        for acceso in accesos:
            miembro = db.query(Miembro).filter(Miembro.id == acceso.miembro_id).first()
            accesos_data.append({
                "fecha_hora": acceso.fecha_hora,
                "nombre_miembro": miembro.nombre_completo if miembro else "Desconocido",
                "numero_miembro": miembro.numero_miembro if miembro else "",
                "tipo_acceso": acceso.tipo_acceso.value,
                "resultado": acceso.resultado.value,
                "ubicacion": acceso.ubicacion,
                "mensaje": acceso.mensaje,
                "estado_snapshot": acceso.estado_miembro_snapshot,
                "saldo_snapshot": acceso.saldo_cuenta_snapshot
            })
        
        # Generar Excel
        excel_file = ExportService.exportar_accesos_excel(accesos_data)
        
        filename = f"accesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exportando accesos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al exportar: {str(e)}"
        )