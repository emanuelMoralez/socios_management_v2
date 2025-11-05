"""
Router de control de acceso - Validación QR
ESTE ES EL ENDPOINT MÁS CRÍTICO PARA LA APP MÓVIL
backend/app/routers/accesos.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, date
from typing import List, Optional
import logging

from app.database import get_db
from app.schemas.acceso import (
    ValidarQRRequest,
    ValidarQRResponse,
    RegistrarAccesoManual,
    AccesoResponse,
    AccesoListItem,
    HistorialAccesosMiembro,
    FiltroHistorialAccesos,
    ResumenAccesos,
    EstadisticasAcceso
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.models.acceso import Acceso, TipoAcceso, ResultadoAcceso
from app.models.miembro import Miembro, EstadoMiembro
from app.models.usuario import Usuario
from app.services.qr_service import QRService
from app.utils.dependencies import get_current_user, require_portero, PaginationParams
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/validar-qr", response_model=ValidarQRResponse)
async def validar_acceso_qr(
    validacion: ValidarQRRequest,
    current_user: Usuario = Depends(require_portero),
    db: Session = Depends(get_db)
):
    """
     ENDPOINT PRINCIPAL PARA LA APP MÓVIL 
    
    Valida el acceso de un miembro mediante código QR
    
    Flujo:
    1. Portero escanea QR con la app móvil
    2. App envía el código QR a este endpoint
    3. Backend valida integridad del QR
    4. Backend verifica estado del miembro
    5. Backend registra el acceso
    6. Retorna respuesta con nivel de alerta (verde/amarillo/rojo)
    
    **Respuestas:**
    - [OK] Verde (success): Acceso permitido, todo OK
    - [WARN] Amarillo (warning): Acceso permitido con advertencia (deuda menor)
    - [ERROR] Rojo (error): Acceso denegado (moroso, suspendido, QR inválido)
    """
    logger.info(f"[PHONE] Validación QR recibida de {current_user.username}")
    
    # Extraer ID del miembro del QR
    miembro_id = QRService.extraer_id_de_qr(validacion.qr_code)
    
    if not miembro_id:
        logger.warning(f"[ERROR] QR inválido: {validacion.qr_code}")
        
        # NO registrar en BD cuando el QR es completamente inválido (no se puede extraer ID)
        # Solo logueamos el intento para auditoría en logs
        logger.error(
            f"[SECURITY] Intento de acceso con QR inválido - "
            f"Portero: {current_user.username} - "
            f"Dispositivo: {validacion.dispositivo_id} - "
            f"Ubicación: {validacion.ubicacion}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código QR inválido o corrupto"
        )
    
    # Buscar miembro en la base de datos
    miembro = db.query(Miembro).filter(
        Miembro.id == miembro_id,
        Miembro.is_deleted == False
    ).first()
    
    if not miembro:
        logger.warning(f"[ERROR] Miembro no encontrado: ID {miembro_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Validar integridad del QR
    qr_valido, mensaje_error = QRService.validar_qr(
        qr_code=validacion.qr_code,
        miembro_id=miembro.id,
        numero_documento=miembro.numero_documento,
        fecha_alta=miembro.qr_generated_at
    )
    
    if not qr_valido:
        logger.warning(f"[ERROR] QR adulterado para miembro {miembro.numero_miembro}: {mensaje_error}")
        
        # Registrar intento de fraude
        acceso = Acceso(
            miembro_id=miembro.id,
            fecha_hora=datetime.utcnow().isoformat(),
            tipo_acceso=TipoAcceso.QR,
            resultado=ResultadoAcceso.RECHAZADO,
            ubicacion=validacion.ubicacion,
            dispositivo_id=validacion.dispositivo_id,
            qr_code_escaneado=validacion.qr_code,
            qr_validacion_exitosa=False,
            mensaje=f"QR adulterado: {mensaje_error}",
            registrado_por_id=current_user.id,
            estado_miembro_snapshot=miembro.estado.value,
            saldo_cuenta_snapshot=miembro.saldo_cuenta
        )
        db.add(acceso)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"QR adulterado o inválido: {mensaje_error}"
        )
    
    # ============================================
    # LÓGICA DE VALIDACIÓN DE ACCESO
    # ============================================
    
    acceso_permitido = False
    nivel_alerta = "error"
    mensaje = ""
    resultado = ResultadoAcceso.RECHAZADO
    
    # Verificar estado del miembro
    if miembro.estado == EstadoMiembro.MOROSO:
        deuda = abs(miembro.saldo_cuenta) if miembro.saldo_cuenta < 0 else 0
        mensaje = f"[ERROR] ACCESO DENEGADO - Cuota impaga. Deuda: ${deuda:.2f}"
        nivel_alerta = "error"
        resultado = ResultadoAcceso.RECHAZADO
        
    elif miembro.estado == EstadoMiembro.SUSPENDIDO:
        mensaje = "[ERROR] ACCESO DENEGADO - Socio suspendido"
        nivel_alerta = "error"
        resultado = ResultadoAcceso.RECHAZADO
        
    elif miembro.estado == EstadoMiembro.BAJA:
        mensaje = "[ERROR] ACCESO DENEGADO - Socio dado de baja"
        nivel_alerta = "error"
        resultado = ResultadoAcceso.RECHAZADO
        
    elif miembro.estado == EstadoMiembro.ACTIVO:
        # Miembro activo - verificar deuda
        if miembro.saldo_cuenta < 0:
            deuda = abs(miembro.saldo_cuenta)
            
            # Si la deuda es menor al límite, permitir con advertencia
            if deuda <= settings.DEUDA_MAXIMA_ADVERTENCIA:
                acceso_permitido = True
                mensaje = f"[WARN] ACCESO PERMITIDO - Advertencia: Deuda de ${deuda:.2f}"
                nivel_alerta = "warning"
                resultado = ResultadoAcceso.ADVERTENCIA
            else:
                mensaje = f"[ERROR] ACCESO DENEGADO - Deuda excesiva: ${deuda:.2f}"
                nivel_alerta = "error"
                resultado = ResultadoAcceso.RECHAZADO
        else:
            # Todo OK
            acceso_permitido = True
            mensaje = f"[OK] ACCESO AUTORIZADO - Bienvenido {miembro.nombre}"
            nivel_alerta = "success"
            resultado = ResultadoAcceso.PERMITIDO
    
    # Registrar el acceso en la base de datos
    acceso = Acceso(
        miembro_id=miembro.id,
        fecha_hora=datetime.utcnow().isoformat(),
        tipo_acceso=TipoAcceso.QR,
        resultado=resultado,
        ubicacion=validacion.ubicacion or "No especificada",
        dispositivo_id=validacion.dispositivo_id,
        qr_code_escaneado=validacion.qr_code,
        qr_validacion_exitosa=True,
        mensaje=mensaje,
        observaciones=validacion.observaciones,
        registrado_por_id=current_user.id,
        latitud=validacion.latitud,
        longitud=validacion.longitud,
        estado_miembro_snapshot=miembro.estado.value,
        saldo_cuenta_snapshot=miembro.saldo_cuenta
    )
    
    db.add(acceso)
    db.commit()
    db.refresh(acceso)
    
    logger.info(
        f"{'[OK]' if acceso_permitido else '[ERROR]'} Acceso {resultado.value} - "
        f"Miembro: {miembro.numero_miembro} - "
        f"Portero: {current_user.username}"
    )
    
    # Preparar respuesta para la app móvil
    response = ValidarQRResponse(
        acceso_permitido=acceso_permitido,
        resultado=resultado,
        nivel_alerta=nivel_alerta,
        mensaje=mensaje,
        miembro={
            "id": miembro.id,
            "numero_miembro": miembro.numero_miembro,
            "nombre_completo": miembro.nombre_completo,
            "foto_url": miembro.foto_url,
            "categoria": miembro.categoria.nombre if miembro.categoria else "Sin categoría",
            "estado": miembro.estado.value,
            "saldo_cuenta": miembro.saldo_cuenta,
            "ultima_cuota_pagada": miembro.ultima_cuota_pagada.isoformat() if miembro.ultima_cuota_pagada else None
        },
        acceso_id=acceso.id,
        timestamp=acceso.fecha_hora,
        deuda=abs(miembro.saldo_cuenta) if miembro.saldo_cuenta < 0 else None,
        dias_mora=miembro.dias_mora
    )
    
    return response


@router.post("/manual", response_model=AccesoResponse)
async def registrar_acceso_manual(
    acceso_data: RegistrarAccesoManual,
    current_user: Usuario = Depends(require_portero),
    db: Session = Depends(get_db)
):
    """
    Registrar acceso manual (sin QR)
    
    Para casos donde el miembro no tiene QR o el portero
    necesita registrar manualmente por autorización especial.
    """
    miembro = db.query(Miembro).filter(Miembro.id == acceso_data.miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Validar acceso (similar a QR pero más flexible)
    acceso_permitido = acceso_data.forzar_acceso or miembro.puede_acceder
    resultado = ResultadoAcceso.PERMITIDO if acceso_permitido else ResultadoAcceso.RECHAZADO
    mensaje = "Acceso manual autorizado" if acceso_permitido else "Acceso manual denegado"
    
    acceso = Acceso(
        miembro_id=miembro.id,
        fecha_hora=datetime.utcnow().isoformat(),
        tipo_acceso=TipoAcceso.MANUAL,
        resultado=resultado,
        ubicacion=acceso_data.ubicacion or "No especificada",
        mensaje=mensaje,
        observaciones=acceso_data.observaciones,
        registrado_por_id=current_user.id,
        estado_miembro_snapshot=miembro.estado.value,
        saldo_cuenta_snapshot=miembro.saldo_cuenta
    )
    
    db.add(acceso)
    db.commit()
    db.refresh(acceso)
    
    logger.info(f" Acceso manual registrado - Miembro: {miembro.numero_miembro}")
    
    return acceso


@router.get("/historial", response_model=PaginatedResponse[AccesoListItem])
async def obtener_historial_accesos(
    miembro_id: Optional[int] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    resultado: Optional[ResultadoAcceso] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de accesos con filtros
    
    Filtros disponibles:
    - miembro_id: Filtrar por miembro específico
    - fecha_inicio/fecha_fin: Rango de fechas
    - resultado: Filtrar por resultado (permitido, rechazado, advertencia)
    """
    query = db.query(Acceso)
    
    # Aplicar filtros
    if miembro_id:
        query = query.filter(Acceso.miembro_id == miembro_id)
    
    if fecha_inicio:
        query = query.filter(Acceso.fecha_hora >= fecha_inicio)
    
    if fecha_fin:
        query = query.filter(Acceso.fecha_hora <= fecha_fin)
    
    if resultado:
        query = query.filter(Acceso.resultado == resultado)
    
    # Total de registros
    total = query.count()
    
    # Paginación
    accesos = query.order_by(desc(Acceso.fecha_hora)).offset(pagination.skip).limit(pagination.limit).all()
    
    # Convertir a lista simplificada
    items = []
    for acceso in accesos:
        miembro = db.query(Miembro).filter(Miembro.id == acceso.miembro_id).first()
        items.append(AccesoListItem(
            id=acceso.id,
            fecha_hora=acceso.fecha_hora,
            tipo_acceso=acceso.tipo_acceso,
            resultado=acceso.resultado,
            ubicacion=acceso.ubicacion,
            miembro_id=acceso.miembro_id,
            nombre_miembro=miembro.nombre_completo if miembro else "Desconocido",
            numero_miembro=miembro.numero_miembro if miembro else None
        ))
    
    return PaginatedResponse(
        items=items,
        pagination=pagination.get_metadata(total)
    )


@router.get("/resumen", response_model=ResumenAccesos)
async def obtener_resumen_accesos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener resumen de accesos para dashboard
    
    Incluye:
    - Total de accesos hoy, esta semana, este mes
    - Rechazos del día
    - Últimos 10 accesos
    """
    from datetime import timedelta
    
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    # Accesos de hoy
    accesos_hoy = db.query(func.count(Acceso.id)).filter(
        func.date(Acceso.fecha_hora) == hoy
    ).scalar() or 0
    
    # Accesos de la semana
    accesos_semana = db.query(func.count(Acceso.id)).filter(
        func.date(Acceso.fecha_hora) >= inicio_semana
    ).scalar() or 0
    
    # Accesos del mes
    accesos_mes = db.query(func.count(Acceso.id)).filter(
        func.date(Acceso.fecha_hora) >= inicio_mes
    ).scalar() or 0
    
    # Rechazos hoy
    rechazos_hoy = db.query(func.count(Acceso.id)).filter(
        func.date(Acceso.fecha_hora) == hoy,
        Acceso.resultado == ResultadoAcceso.RECHAZADO
    ).scalar() or 0
    
    # Últimos accesos
    ultimos = db.query(Acceso).order_by(desc(Acceso.fecha_hora)).limit(10).all()
    
    ultimos_accesos = []
    for acceso in ultimos:
        miembro = db.query(Miembro).filter(Miembro.id == acceso.miembro_id).first()
        ultimos_accesos.append(AccesoListItem(
            id=acceso.id,
            fecha_hora=acceso.fecha_hora,
            tipo_acceso=acceso.tipo_acceso,
            resultado=acceso.resultado,
            ubicacion=acceso.ubicacion,
            miembro_id=acceso.miembro_id,
            nombre_miembro=miembro.nombre_completo if miembro else "Desconocido",
            numero_miembro=miembro.numero_miembro if miembro else None
        ))
    
    return ResumenAccesos(
        hoy=accesos_hoy,
        semana=accesos_semana,
        mes=accesos_mes,
        rechazos_hoy=rechazos_hoy,
        ultimos_accesos=ultimos_accesos
    )


@router.get("/estadisticas", response_model=EstadisticasAcceso)
async def obtener_estadisticas_accesos(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas detalladas de accesos del día
    
    Para el panel de control de accesos en tiempo real.
    Incluye:
    - Total de accesos hoy
    - Entradas hoy
    - Salidas hoy
    - Rechazos hoy
    - Promedio por hora
    """
    from datetime import datetime, time
    
    hoy = date.today()
    inicio_hoy = datetime.combine(hoy, time.min)
    fin_hoy = datetime.combine(hoy, time.max)
    
    # Total de accesos hoy
    total_hoy = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio_hoy.isoformat(),
        Acceso.fecha_hora <= fin_hoy.isoformat()
    ).scalar() or 0
    
    # Accesos permitidos (entradas)
    entradas_hoy = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio_hoy.isoformat(),
        Acceso.fecha_hora <= fin_hoy.isoformat(),
        Acceso.resultado == ResultadoAcceso.PERMITIDO
    ).scalar() or 0
    
    # Salidas (si tienes un campo tipo_movimiento, sino usar el mismo que entradas)
    # Por ahora asumimos que todas son entradas
    salidas_hoy = 0  # Implementar si tienes lógica de entrada/salida
    
    # Rechazos
    rechazos_hoy = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio_hoy.isoformat(),
        Acceso.fecha_hora <= fin_hoy.isoformat(),
        Acceso.resultado == ResultadoAcceso.RECHAZADO
    ).scalar() or 0
    
    # Advertencias
    advertencias_hoy = db.query(func.count(Acceso.id)).filter(
        Acceso.fecha_hora >= inicio_hoy.isoformat(),
        Acceso.fecha_hora <= fin_hoy.isoformat(),
        Acceso.resultado == ResultadoAcceso.ADVERTENCIA
    ).scalar() or 0
    
    # Hora actual
    hora_actual = datetime.now().hour
    promedio_por_hora = round(total_hoy / hora_actual, 1) if hora_actual > 0 else 0
    
    # Accesos por hora (últimas 24 horas)
    accesos_por_hora = []
    for hora in range(24):
        inicio_hora = datetime.combine(hoy, time(hora, 0))
        fin_hora = datetime.combine(hoy, time(hora, 59, 59))
        
        cantidad = db.query(func.count(Acceso.id)).filter(
            Acceso.fecha_hora >= inicio_hora.isoformat(),
            Acceso.fecha_hora <= fin_hora.isoformat()
        ).scalar() or 0
        
        accesos_por_hora.append({
            "hora": f"{hora:02d}:00",
            "cantidad": cantidad
        })
    
    # Último acceso
    ultimo_acceso = db.query(Acceso).order_by(
        desc(Acceso.fecha_hora)
    ).first()
    
    ultimo_acceso_info = None
    if ultimo_acceso:
        miembro = db.query(Miembro).filter(
            Miembro.id == ultimo_acceso.miembro_id
        ).first()
        
        if miembro:
            ultimo_acceso_info = {
                "fecha_hora": ultimo_acceso.fecha_hora,
                "nombre_miembro": miembro.nombre_completo,
                "resultado": ultimo_acceso.resultado.value
            }
    
    return EstadisticasAcceso(
        total_hoy=total_hoy,
        entradas_hoy=entradas_hoy,
        salidas_hoy=salidas_hoy,
        rechazos_hoy=rechazos_hoy,
        advertencias_hoy=advertencias_hoy,
        promedio_por_hora=promedio_por_hora,
        accesos_por_hora=accesos_por_hora,
        ultimo_acceso=ultimo_acceso_info,
        fecha=hoy.isoformat()
    )