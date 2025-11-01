"""
Router de Notificaciones - Envío de emails
backend/app/routers/notificaciones.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.miembro import Miembro, EstadoMiembro
from app.models.usuario import Usuario
from app.utils.dependencies import get_current_user, require_operador
from app.schemas.common import MessageResponse
from app.config import settings
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recordatorio", response_model=MessageResponse)
async def enviar_recordatorio_individual(
    miembro_id: int,
    email: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Enviar recordatorio de cuota a un socio específico
    
    Si no se especifica email, usa el del socio.
    """
    # Verificar que el socio exista
    miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Determinar email destino
    email_destino = email or miembro.email
    
    if not email_destino:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El socio no tiene email registrado"
        )
    
    # Verificar si tiene deuda
    if miembro.saldo_cuenta >= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El socio no tiene deuda pendiente"
        )
    
    deuda = abs(miembro.saldo_cuenta)
    
    try:
        # Enviar recordatorio usando el servicio
        resultado = await NotificationService.enviar_recordatorio_individual(
            miembro_id=miembro_id,
            db=db,
            email_override=email
        )
        
        if not resultado["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=resultado.get("error", "Error al enviar email")
            )
        
        logger.info(
            f"[EMAIL] Recordatorio enviado a {miembro.numero_miembro} "
            f"({email_destino}) - Deuda: ${deuda:.2f}"
        )
        
        return MessageResponse(
            message="Recordatorio enviado exitosamente",
            detail=f"Email enviado a {email_destino}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enviando recordatorio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar email: {str(e)}"
        )


@router.post("/recordatorios-masivos")
async def enviar_recordatorios_masivos(
    solo_morosos: bool = True,
    dias_mora_minimo: int = 5,
    incluir_email: bool = True,
    background_tasks: BackgroundTasks = None,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Enviar recordatorios masivos de cuota
    
    Args:
        solo_morosos: Si True, solo envía a socios con estado MOROSO
        dias_mora_minimo: Días mínimos de mora para enviar
        incluir_email: Si True, envía emails (False para test/preview)
    
    Returns:
        Estadísticas de envío
    """
    try:
        # Preview mode: solo contar sin enviar
        if not incluir_email:
            query = db.query(Miembro).filter(
                Miembro.is_deleted == False,
                Miembro.saldo_cuenta < 0,
                Miembro.email.isnot(None)
            )
            
            if solo_morosos:
                query = query.filter(Miembro.estado == EstadoMiembro.MOROSO)
            
            morosos = query.all()
            
            # Filtrar por días de mora
            if dias_mora_minimo > 0:
                morosos = [
                    m for m in morosos 
                    if (m.dias_mora or 0) >= dias_mora_minimo
                ]
            
            return {
                "success": True,
                "enviados": 0,
                "fallidos": 0,
                "total_procesados": len(morosos),
                "preview": True,
                "message": f"Se enviarían {len(morosos)} recordatorios"
            }
        
        # Envío real usando el servicio
        resultado = await NotificationService.enviar_recordatorios_masivos(
            solo_morosos=solo_morosos,
            dias_mora_minimo=dias_mora_minimo,
            db=db
        )
        
        logger.info(
            f"[EMAIL] Recordatorios masivos - "
            f"Enviados: {resultado['enviados']}, "
            f"Fallidos: {resultado['fallidos']}"
        )
        
        return {
            "success": True,
            "enviados": resultado["enviados"],
            "fallidos": resultado["fallidos"],
            "total_procesados": resultado.get("total_procesados", 0),
            "message": f"Recordatorios enviados: {resultado['enviados']}",
            "errores": resultado.get("errores", [])
        }
    
    except Exception as e:
        logger.error(f"Error en envío masivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar recordatorios: {str(e)}"
        )


@router.get("/test-email")
async def test_configuracion_email(
    current_user: Usuario = Depends(require_operador)
):
    """
    Probar configuración de email
    
    Verifica que las credenciales SMTP estén configuradas y funcionen.
    """
    try:
        # Usar el servicio para probar
        resultado = await NotificationService.test_email_config()
        
        if resultado["success"]:
            return {
                "success": True,
                "configured": True,
                "message": "Configuración SMTP correcta",
                "detail": resultado.get("message"),
                "config": resultado.get("config", {})
            }
        else:
            return {
                "success": False,
                "configured": False,
                "message": "Error en configuración SMTP",
                "detail": resultado.get("error"),
                "help": "Verifica las variables SMTP_* en tu archivo .env"
            }
    
    except Exception as e:
        logger.error(f"Error probando configuración email: {e}")
        return {
            "success": False,
            "configured": False,
            "message": "Error al probar configuración",
            "detail": str(e),
            "help": "Verifica las variables SMTP_HOST, SMTP_USER, SMTP_PASSWORD en .env"
        }


@router.get("/preview-morosos")
async def preview_morosos(
    solo_morosos: bool = True,
    dias_mora_minimo: int = 5,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Vista previa de socios que recibirían recordatorios
    
    Útil para verificar antes de enviar masivamente.
    """
    query = db.query(Miembro).filter(
        Miembro.is_deleted == False,
        Miembro.saldo_cuenta < 0,
        Miembro.email.isnot(None)
    )
    
    if solo_morosos:
        query = query.filter(Miembro.estado == EstadoMiembro.MOROSO)
    
    morosos = query.all()
    
    # Filtrar por días de mora
    if dias_mora_minimo > 0:
        morosos = [
            m for m in morosos 
            if (m.dias_mora or 0) >= dias_mora_minimo
        ]
    
    # Preparar preview
    preview = []
    total_deuda = 0
    
    for miembro in morosos[:50]:  # Limitar a 50 para preview
        deuda = abs(miembro.saldo_cuenta)
        total_deuda += deuda
        
        preview.append({
            "numero_miembro": miembro.numero_miembro,
            "nombre_completo": miembro.nombre_completo,
            "email": miembro.email,
            "deuda": deuda,
            "dias_mora": miembro.dias_mora or 0,
            "estado": miembro.estado.value
        })
    
    return {
        "total_destinatarios": len(morosos),
        "total_deuda": total_deuda,
        "preview_primeros_50": preview,
        "filtros": {
            "solo_morosos": solo_morosos,
            "dias_mora_minimo": dias_mora_minimo
        }
    }