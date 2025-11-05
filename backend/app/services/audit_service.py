"""
Servicio de Auditoría
backend/app/services/audit_service.py
"""
from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional, Dict, Any
import logging

from app.models.actividad import Actividad, TipoActividad, NivelSeveridad

logger = logging.getLogger(__name__)


class AuditService:
    """Servicio para registrar actividades de auditoría"""
    
    @staticmethod
    def registrar(
        db: Session,
        tipo: TipoActividad,
        descripcion: str,
        usuario_id: Optional[int] = None,
        entidad_tipo: Optional[str] = None,
        entidad_id: Optional[int] = None,
        datos_adicionales: Optional[Dict[str, Any]] = None,
        severidad: NivelSeveridad = NivelSeveridad.INFO,
        request: Optional[Request] = None
    ) -> Actividad:
        """
        Registrar actividad en el sistema
        
        Args:
            db: Sesión de base de datos
            tipo: Tipo de actividad (enum)
            descripcion: Descripción legible
            usuario_id: ID del usuario que ejecuta
            entidad_tipo: Tipo de entidad afectada ("miembro", "pago")
            entidad_id: ID de la entidad afectada
            datos_adicionales: Datos extra en JSON
            severidad: Nivel de severidad
            request: Request de FastAPI (para extraer IP y User-Agent)
        
        Returns:
            Actividad creada
        
        Ejemplo:
            AuditService.registrar(
                db=db,
                tipo=TipoActividad.PAGO_REGISTRADO,
                descripcion=f"Pago de ${monto} registrado para {miembro.nombre}",
                usuario_id=current_user.id,
                entidad_tipo="pago",
                entidad_id=pago.id,
                datos_adicionales={
                    "monto": monto,
                    "miembro_id": miembro.id,
                    "metodo": metodo_pago
                },
                request=request
            )
        """
        # Extraer IP y User-Agent del request
        ip_address = None
        user_agent = None
        
        if request:
            # IP real (considerando proxies)
            ip_address = request.headers.get("X-Forwarded-For")
            if ip_address:
                ip_address = ip_address.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None
            
            # User-Agent
            user_agent = request.headers.get("User-Agent")
        
        try:
            actividad = Actividad.crear(
                tipo=tipo,
                descripcion=descripcion,
                usuario_id=usuario_id,
                entidad_tipo=entidad_tipo,
                entidad_id=entidad_id,
                datos_adicionales=datos_adicionales,
                severidad=severidad,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(actividad)
            db.commit()
            db.refresh(actividad)
            
            # Log adicional para eventos críticos
            if severidad in [NivelSeveridad.ERROR, NivelSeveridad.CRITICAL]:
                logger.warning(
                    f"[AUDIT] {severidad.value.upper()}: {descripcion}",
                    extra={
                        "tipo": tipo.value,
                        "usuario_id": usuario_id,
                        "entidad": f"{entidad_tipo}:{entidad_id}" if entidad_tipo else None
                    }
                )
            
            return actividad
            
        except Exception as e:
            logger.error(f"Error registrando actividad: {e}", exc_info=True)
            db.rollback()
            # No fallar la operación principal por error en auditoría
            return None
    
    @staticmethod
    def registrar_login_exitoso(
        db: Session,
        usuario_id: int,
        username: str,
        request: Optional[Request] = None
    ):
        """Registrar login exitoso"""
        return AuditService.registrar(
            db=db,
            tipo=TipoActividad.LOGIN_EXITOSO,
            descripcion=f"Usuario '{username}' inició sesión",
            usuario_id=usuario_id,
            severidad=NivelSeveridad.INFO,
            request=request
        )
    
    @staticmethod
    def registrar_login_fallido(
        db: Session,
        username: str,
        motivo: str,
        request: Optional[Request] = None
    ):
        """Registrar intento fallido de login"""
        return AuditService.registrar(
            db=db,
            tipo=TipoActividad.LOGIN_FALLIDO,
            descripcion=f"Intento fallido de login para '{username}': {motivo}",
            severidad=NivelSeveridad.WARNING,
            datos_adicionales={"username": username, "motivo": motivo},
            request=request
        )
    
    @staticmethod
    def registrar_pago(
        db: Session,
        pago_id: int,
        miembro_nombre: str,
        monto: float,
        usuario_id: int,
        request: Optional[Request] = None
    ):
        """Registrar creación de pago"""
        return AuditService.registrar(
            db=db,
            tipo=TipoActividad.PAGO_REGISTRADO,
            descripcion=f"Pago de ${monto:,.2f} registrado para {miembro_nombre}",
            usuario_id=usuario_id,
            entidad_tipo="pago",
            entidad_id=pago_id,
            datos_adicionales={
                "monto": monto,
                "miembro": miembro_nombre
            },
            request=request
        )
    
    @staticmethod
    def registrar_pago_anulado(
        db: Session,
        pago_id: int,
        motivo: str,
        usuario_id: int,
        request: Optional[Request] = None
    ):
        """Registrar anulación de pago"""
        return AuditService.registrar(
            db=db,
            tipo=TipoActividad.PAGO_ANULADO,
            descripcion=f"Pago anulado. Motivo: {motivo}",
            usuario_id=usuario_id,
            entidad_tipo="pago",
            entidad_id=pago_id,
            severidad=NivelSeveridad.WARNING,
            datos_adicionales={"motivo": motivo},
            request=request
        )
    
    @staticmethod
    def registrar_miembro_creado(
        db: Session,
        miembro_id: int,
        miembro_nombre: str,
        usuario_id: int,
        request: Optional[Request] = None
    ):
        """Registrar creación de miembro"""
        return AuditService.registrar(
            db=db,
            tipo=TipoActividad.MIEMBRO_CREADO,
            descripcion=f"Nuevo socio registrado: {miembro_nombre}",
            usuario_id=usuario_id,
            entidad_tipo="miembro",
            entidad_id=miembro_id,
            datos_adicionales={"nombre": miembro_nombre},
            request=request
        )
    
    @staticmethod
    def registrar_acceso(
        db: Session,
        acceso_id: int,
        miembro_nombre: str,
        permitido: bool,
        motivo: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Registrar intento de acceso"""
        tipo = TipoActividad.ACCESO_PERMITIDO if permitido else TipoActividad.ACCESO_DENEGADO
        severidad = NivelSeveridad.INFO if permitido else NivelSeveridad.WARNING
        
        descripcion = f"Acceso {'permitido' if permitido else 'denegado'} a {miembro_nombre}"
        if motivo and not permitido:
            descripcion += f": {motivo}"
        
        return AuditService.registrar(
            db=db,
            tipo=tipo,
            descripcion=descripcion,
            entidad_tipo="acceso",
            entidad_id=acceso_id,
            severidad=severidad,
            datos_adicionales={
                "miembro": miembro_nombre,
                "permitido": permitido,
                "motivo": motivo
            },
            request=request
        )
    
    @staticmethod
    def obtener_actividades(
        db: Session,
        usuario_id: Optional[int] = None,
        entidad_tipo: Optional[str] = None,
        entidad_id: Optional[int] = None,
        tipo: Optional[TipoActividad] = None,
        limite: int = 100
    ):
        """
        Obtener actividades con filtros
        
        Returns:
            Lista de actividades ordenadas por fecha DESC
        """
        query = db.query(Actividad)
        
        if usuario_id:
            query = query.filter(Actividad.usuario_id == usuario_id)
        
        if entidad_tipo:
            query = query.filter(Actividad.entidad_tipo == entidad_tipo)
        
        if entidad_id:
            query = query.filter(Actividad.entidad_id == entidad_id)
        
        if tipo:
            query = query.filter(Actividad.tipo == tipo)
        
        return query.order_by(Actividad.fecha_hora.desc()).limit(limite).all()