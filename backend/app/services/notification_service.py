"""
Servicio de Notificaciones por Email
backend/app/services/notification_service.py
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.models.miembro import Miembro
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio para envío de notificaciones por email"""
    
    @staticmethod
    def _get_smtp_connection():
        """
        Establecer conexión SMTP
        
        Returns:
            smtplib.SMTP: Conexión SMTP configurada
        """
        try:
            # Verificar configuración
            if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                raise ValueError("Configuración SMTP incompleta")
            
            # Crear conexión
            if settings.SMTP_TLS:
                smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                smtp.starttls()
            else:
                smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            
            # Autenticar
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            return smtp
        
        except Exception as e:
            logger.error(f"Error conectando SMTP: {e}")
            raise
    
    @staticmethod
    def _crear_email_recordatorio(
        miembro: Miembro,
        deuda: float,
        dias_mora: int
    ) -> MIMEMultipart:
        """
        Crear email de recordatorio de cuota
        
        Args:
            miembro: Objeto Miembro
            deuda: Monto de deuda
            dias_mora: Días de mora
        
        Returns:
            MIMEMultipart: Email construido
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Recordatorio de Cuota - {settings.PROJECT_NAME}"
        msg['From'] = f"{settings.PROJECT_NAME} <{settings.SMTP_USER}>"
        msg['To'] = miembro.email
        
        # Texto plano
        text = f"""
Hola {miembro.nombre_completo},

Te recordamos que tienes una deuda pendiente de ${deuda:,.2f}.

Días de mora: {dias_mora}
Categoría: {miembro.categoria.nombre if miembro.categoria else 'N/A'}
Cuota mensual: ${miembro.categoria.cuota_mensual if miembro.categoria else 0:,.2f}

Por favor, acércate a nuestras oficinas para regularizar tu situación.

Gracias por tu atención.

---
{settings.PROJECT_NAME}
Este es un mensaje automático, por favor no responder.
        """
        
        # HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #366092;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 1px solid #ddd;
        }}
        .deuda-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .deuda-monto {{
            font-size: 24px;
            font-weight: bold;
            color: #d9534f;
        }}
        .info-row {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .info-label {{
            font-weight: bold;
            color: #666;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{settings.PROJECT_NAME}</h1>
            <p>Recordatorio de Cuota</p>
        </div>
        
        <div class="content">
            <p>Hola <strong>{miembro.nombre_completo}</strong>,</p>
            
            <p>Te recordamos que tienes una deuda pendiente:</p>
            
            <div class="deuda-box">
                <div class="deuda-monto">${deuda:,.2f}</div>
                <p style="margin: 5px 0 0 0; color: #856404;">
                    {'⚠️ Mora de ' + str(dias_mora) + ' días' if dias_mora > 0 else ''}
                </p>
            </div>
            
            <div class="info-row">
                <span class="info-label">N° Socio:</span> {miembro.numero_miembro}
            </div>
            <div class="info-row">
                <span class="info-label">Categoría:</span> {miembro.categoria.nombre if miembro.categoria else 'N/A'}
            </div>
            <div class="info-row">
                <span class="info-label">Cuota Mensual:</span> ${miembro.categoria.cuota_mensual if miembro.categoria else 0:,.2f}
            </div>
            
            <p style="margin-top: 20px;">
                Por favor, acércate a nuestras oficinas para regularizar tu situación.
            </p>
            
            <p>Gracias por tu atención.</p>
        </div>
        
        <div class="footer">
            <p>{settings.PROJECT_NAME}</p>
            <p>Este es un mensaje automático, por favor no responder.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Adjuntar partes
        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        return msg
    
    @staticmethod
    async def enviar_recordatorio_individual(
        miembro_id: int,
        db: Session,
        email_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enviar recordatorio a un socio específico
        
        Args:
            miembro_id: ID del miembro
            db: Sesión de base de datos
            email_override: Email alternativo (opcional)
        
        Returns:
            Dict con resultado del envío
        """
        try:
            # Obtener miembro
            miembro = db.query(Miembro).filter(Miembro.id == miembro_id).first()
            
            if not miembro:
                return {
                    "success": False,
                    "error": "Miembro no encontrado"
                }
            
            # Verificar email
            email_destino = email_override or miembro.email
            if not email_destino:
                return {
                    "success": False,
                    "error": "El socio no tiene email registrado"
                }
            
            # Calcular deuda y mora
            deuda = abs(miembro.saldo_cuenta) if miembro.saldo_cuenta < 0 else 0
            dias_mora = miembro.dias_mora or 0
            
            if deuda <= 0:
                return {
                    "success": False,
                    "error": "El socio no tiene deuda"
                }
            
            # Crear email
            msg = NotificationService._crear_email_recordatorio(
                miembro=miembro,
                deuda=deuda,
                dias_mora=dias_mora
            )
            
            # Si hay override, cambiar destinatario
            if email_override:
                msg['To'] = email_override
            
            # Enviar
            smtp = NotificationService._get_smtp_connection()
            smtp.send_message(msg)
            smtp.quit()
            
            logger.info(f"Recordatorio enviado a {email_destino} (Socio: {miembro.numero_miembro})")
            
            return {
                "success": True,
                "email": email_destino,
                "miembro": miembro.nombre_completo,
                "deuda": deuda
            }
        
        except Exception as e:
            logger.error(f"Error enviando recordatorio a miembro {miembro_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def enviar_recordatorios_masivos(
        solo_morosos: bool,
        dias_mora_minimo: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Enviar recordatorios masivos
        
        Args:
            solo_morosos: Si True, solo envía a socios en estado MOROSO
            dias_mora_minimo: Días mínimos de mora para enviar
            db: Sesión de base de datos
        
        Returns:
            Dict con estadísticas de envío
        """
        enviados = 0
        fallidos = 0
        errores = []
        
        try:
            # Construir query
            query = db.query(Miembro).filter(
                Miembro.is_deleted == False,
                Miembro.email.isnot(None),
                Miembro.saldo_cuenta < 0  # Tiene deuda
            )
            
            # Filtro por estado
            if solo_morosos:
                from app.models.miembro import EstadoMiembro
                query = query.filter(Miembro.estado == EstadoMiembro.MOROSO)
            
            socios = query.all()
            
            # Filtrar por días de mora
            socios_filtrados = [
                s for s in socios
                if (s.dias_mora or 0) >= dias_mora_minimo
            ]
            
            logger.info(f"Enviando recordatorios a {len(socios_filtrados)} socios...")
            
            # Enviar a cada uno
            for socio in socios_filtrados:
                try:
                    deuda = abs(socio.saldo_cuenta)
                    dias_mora = socio.dias_mora or 0
                    
                    # Crear y enviar email
                    msg = NotificationService._crear_email_recordatorio(
                        miembro=socio,
                        deuda=deuda,
                        dias_mora=dias_mora
                    )
                    
                    smtp = NotificationService._get_smtp_connection()
                    smtp.send_message(msg)
                    smtp.quit()
                    
                    enviados += 1
                    logger.info(f"✓ Enviado a {socio.email} ({socio.numero_miembro})")
                
                except Exception as e:
                    fallidos += 1
                    error_msg = f"Error con {socio.numero_miembro}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
            
            return {
                "enviados": enviados,
                "fallidos": fallidos,
                "total_procesados": len(socios_filtrados),
                "errores": errores[:10]  # Limitar a 10 errores
            }
        
        except Exception as e:
            logger.error(f"Error en envío masivo: {e}")
            return {
                "enviados": enviados,
                "fallidos": fallidos,
                "error_general": str(e)
            }
    
    @staticmethod
    async def test_email_config() -> Dict[str, Any]:
        """
        Probar configuración de email
        
        Returns:
            Dict con resultado del test
        """
        try:
            # Verificar configuración
            if not settings.SMTP_HOST:
                return {
                    "success": False,
                    "error": "SMTP_HOST no configurado"
                }
            
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                return {
                    "success": False,
                    "error": "Credenciales SMTP no configuradas"
                }
            
            # Intentar conectar
            smtp = NotificationService._get_smtp_connection()
            
            # Enviar email de prueba
            msg = MIMEMultipart()
            msg['Subject'] = f"Test de Configuración - {settings.PROJECT_NAME}"
            msg['From'] = settings.SMTP_USER
            msg['To'] = settings.SMTP_USER
            
            body = f"""
Este es un email de prueba de configuración SMTP.

Configuración:
- Host: {settings.SMTP_HOST}
- Puerto: {settings.SMTP_PORT}
- Usuario: {settings.SMTP_USER}
- TLS: {settings.SMTP_TLS}

Si recibes este email, la configuración es correcta.

---
{settings.PROJECT_NAME}
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            smtp.send_message(msg)
            smtp.quit()
            
            return {
                "success": True,
                "message": f"Email de prueba enviado a {settings.SMTP_USER}",
                "config": {
                    "host": settings.SMTP_HOST,
                    "port": settings.SMTP_PORT,
                    "user": settings.SMTP_USER,
                    "tls": settings.SMTP_TLS
                }
            }
        
        except Exception as e:
            logger.error(f"Error en test de email: {e}")
            return {
                "success": False,
                "error": str(e)
            }