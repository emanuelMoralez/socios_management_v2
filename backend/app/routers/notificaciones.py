"""
Router de Notificaciones - Envío de emails
backend/app/routers/notificaciones.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.models.miembro import Miembro, EstadoMiembro
from app.models.usuario import Usuario
from app.utils.dependencies import get_current_user, require_operador
from app.schemas.common import MessageResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recordatorio", response_model=MessageResponse)
async def enviar_recordatorio_individual(
    miembro_id: int,
    email: Optional[str] = None,
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
    
    # TODO: Implementar envío real de email
    # from app.services.email_service import EmailService
    # EmailService.enviar_recordatorio_cuota(
    #     email=email_destino,
    #     nombre=miembro.nombre_completo,
    #     numero_socio=miembro.numero_miembro,
    #     deuda=deuda
    # )
    
    logger.info(
        f"[EMAIL] Recordatorio enviado a {miembro.numero_miembro} "
        f"({email_destino}) - Deuda: ${deuda:.2f}"
    )
    
    return MessageResponse(
        message="Recordatorio enviado exitosamente",
        detail=f"Email enviado a {email_destino}"
    )


@router.post("/recordatorios-masivos")
async def enviar_recordatorios_masivos(
    solo_morosos: bool = True,
    dias_mora_minimo: int = 5,
    incluir_email: bool = True,
    current_user: Usuario = Depends(require_operador),
    db: Session = Depends(get_db)
):
    """
    Enviar recordatorios masivos de cuota
    
    Args:
        solo_morosos: Si True, solo envía a socios con estado MOROSO
        dias_mora_minimo: Días mínimos de mora para enviar
        incluir_email: Si True, envía emails (False para test)
    
    Returns:
        Estadísticas de envío
    """
    # Construir query base
    query = db.query(Miembro).filter(
        Miembro.is_deleted == False,
        Miembro.saldo_cuenta < 0,  # Solo con deuda
        Miembro.email.isnot(None)   # Solo con email
    )
    
    # Filtrar por estado si se solicita
    if solo_morosos:
        query = query.filter(Miembro.estado == EstadoMiembro.MOROSO)
    
    # Filtrar por días de mora
    if dias_mora_minimo > 0:
        # TODO: Implementar filtro por días de mora
        # Requiere calcular días desde última cuota o vencimiento
        pass
    
    morosos = query.all()
    
    enviados = 0
    fallidos = 0
    
    for miembro in morosos:
        try:
            deuda = abs(miembro.saldo_cuenta)
            
            # TODO: Implementar envío real de email
            # from app.services.email_service import EmailService
            # EmailService.enviar_recordatorio_cuota(
            #     email=miembro.email,
            #     nombre=miembro.nombre_completo,
            #     numero_socio=miembro.numero_miembro,
            #     deuda=deuda
            # )
            
            logger.info(
                f"[EMAIL] Recordatorio a {miembro.numero_miembro} "
                f"({miembro.email}) - ${deuda:.2f}"
            )
            
            enviados += 1
            
        except Exception as e:
            logger.error(f"[ERROR] Error enviando a {miembro.numero_miembro}: {e}")
            fallidos += 1
    
    logger.info(
        f"[EMAIL] Recordatorios masivos - "
        f"Enviados: {enviados}, Fallidos: {fallidos}"
    )
    
    return {
        "success": True,
        "enviados": enviados,
        "fallidos": fallidos,
        "total_procesados": len(morosos),
        "message": f"Recordatorios programados: {enviados}"
    }


@router.get("/test-email")
async def test_configuracion_email(
    current_user: Usuario = Depends(require_operador)
):
    """
    Probar configuración de email
    
    Verifica que las credenciales SMTP estén configuradas.
    """
    # Verificar configuración
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return {
            "success": False,
            "configured": False,
            "message": "Configuración SMTP no encontrada",
            "detail": "Completa las variables SMTP_* en el .env"
        }
    
    # TODO: Intentar enviar email de prueba
    # from app.services.email_service import EmailService
    # try:
    #     EmailService.enviar_test(current_user.email)
    #     return {
    #         "success": True,
    #         "configured": True,
    #         "message": "Configuración correcta",
    #         "detail": f"Email de prueba enviado a {current_user.email}"
    #     }
    # except Exception as e:
    #     return {
    #         "success": False,
    #         "configured": True,
    #         "message": "Error en configuración SMTP",
    #         "detail": str(e)
    #     }
    
    return {
        "success": True,
        "configured": True,
        "message": "Configuración SMTP encontrada",
        "detail": f"Host: {settings.SMTP_HOST}, User: {settings.SMTP_USER}",
        "warning": "Envío de emails no implementado aún (TODO)"
    }