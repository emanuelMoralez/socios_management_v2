"""
Servicio de generación y validación de códigos QR
backend/app/services/qr_service.py
"""
import qrcode
import hashlib
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Optional, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class QRService:
    """Servicio para gestión de códigos QR únicos e inmutables"""
    
    @staticmethod
    def generar_qr_miembro(
        miembro_id: int,
        numero_documento: str,
        numero_miembro: str,
        nombre_completo: Optional[str] = None,
        timestamp: Optional[str] = None,
        personalizar: bool = True
    ) -> Dict[str, any]:
        """
        Genera un código QR único para un miembro
        
        El QR es INMUTABLE y contiene:
        - ID del miembro
        - Checksum de seguridad
        - Timestamp de generación
        
        Formato: {PREFIX}-{ID}-{CHECKSUM}
        Ejemplo: CLUB-123-a1b2c3d4e5f6
        
        Args:
            miembro_id: ID del miembro en la base de datos
            numero_documento: Documento del miembro (para checksum)
            numero_miembro: Número de miembro (ej: M-00001)
            nombre_completo: Nombre para personalización visual
            timestamp: Timestamp ISO (si no se provee, usa actual)
            personalizar: Si True, agrega nombre y logo al QR
        
        Returns:
            Dict con:
                - qr_code: String del código QR
                - qr_hash: Hash SHA256 del código
                - image_bytes: Imagen PNG en bytes
                - timestamp: Timestamp de generación
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        # Crear payload base
        data_string = f"{miembro_id}|{numero_documento}|{timestamp}"
        
        # Generar checksum seguro usando SECRET_KEY
        hash_input = f"{data_string}|{settings.QR_SECRET_KEY}"
        checksum = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Formato final del QR
        qr_payload = f"{settings.ORG_PREFIX}-{miembro_id}-{checksum}"
        
        logger.info(f"Generando QR para miembro #{miembro_id}: {qr_payload}")
        
        # Configurar QR
        qr = qrcode.QRCode(
            version=settings.QR_VERSION,
            error_correction=getattr(
                qrcode.constants,
                f"ERROR_CORRECT_{settings.QR_ERROR_CORRECTION}"
            ),
            box_size=settings.QR_BOX_SIZE,
            border=settings.QR_BORDER,
        )
        
        qr.add_data(qr_payload)
        qr.make(fit=True)
        
        # Crear imagen base
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGB")
        
        # Personalizar si se solicita
        if personalizar and nombre_completo:
            img = QRService._personalizar_qr(
                img,
                nombre_completo,
                numero_miembro
            )
        
        # Convertir a bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        
        # Hash del payload completo para la BD
        qr_hash = hashlib.sha256(qr_payload.encode()).hexdigest()
        
        return {
            "qr_code": qr_payload,
            "qr_hash": qr_hash,
            "image_bytes": image_bytes,
            "timestamp": timestamp,
            "metadata": {
                "miembro_id": miembro_id,
                "checksum": checksum,
                "generated_at": timestamp
            }
        }
    
    @staticmethod
    def _personalizar_qr(
        img: Image,
        nombre_completo: str,
        numero_miembro: str
    ) -> Image:
        """
        Personaliza la imagen QR con información del miembro
        
        Args:
            img: Imagen QR base
            nombre_completo: Nombre del miembro
            numero_miembro: Número de miembro
        
        Returns:
            Imagen personalizada
        """
        # Dimensiones del nuevo canvas
        padding = 40
        text_space_top = 80
        text_space_bottom = 100
        
        canvas_width = img.width + (padding * 2)
        canvas_height = img.height + text_space_top + text_space_bottom
        
        # Crear canvas blanco
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
        
        # Centrar QR
        qr_x = padding
        qr_y = text_space_top
        canvas.paste(img, (qr_x, qr_y))
        
        # Preparar para dibujar texto
        draw = ImageDraw.Draw(canvas)
        
        # Intentar cargar fuentes, si falla usar default
        try:
            font_title = ImageFont.truetype("arial.ttf", 28)
            font_text = ImageFont.truetype("arial.ttf", 22)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            try:
                # Intentar con DejaVu (Linux)
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                # Usar fuente por defecto
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Título superior
        titulo = settings.ORG_NAME.upper()
        bbox = draw.textbbox((0, 0), titulo, font=font_title)
        text_width = bbox[2] - bbox[0]
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, 20), titulo, fill='black', font=font_title)
        
        # Línea divisoria
        draw.line([(20, 65), (canvas_width - 20, 65)], fill='gray', width=2)
        
        # Nombre del miembro (abajo del QR)
        y_offset = qr_y + img.height + 20
        
        # Limitar longitud del nombre
        if len(nombre_completo) > 30:
            nombre_completo = nombre_completo[:27] + "..."
        
        bbox = draw.textbbox((0, 0), nombre_completo, font=font_text)
        text_width = bbox[2] - bbox[0]
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, y_offset), nombre_completo, fill='black', font=font_text)
        
        # Número de miembro
        y_offset += 35
        bbox = draw.textbbox((0, 0), numero_miembro, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_x = (canvas_width - text_width) // 2
        draw.text((text_x, y_offset), numero_miembro, fill='gray', font=font_small)
        
        # Opcional: Agregar logo del club
        # Descomentar si tienes un logo
        # try:
        #     logo = Image.open("assets/logo.png")
        #     logo = logo.resize((60, 60))
        #     logo_x = (canvas_width - 60) // 2
        #     logo_y = qr_y + (img.height - 60) // 2
        #     canvas.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
        # except Exception as e:
        #     logger.warning(f"No se pudo cargar logo: {e}")
        
        return canvas
    
    @staticmethod
    def validar_qr(
        qr_code: str,
        miembro_id: int,
        numero_documento: str,
        fecha_alta: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida la integridad y autenticidad de un código QR
        
        Args:
            qr_code: Código QR escaneado
            miembro_id: ID del miembro en BD
            numero_documento: Documento del miembro
            fecha_alta: Fecha de alta del miembro (ISO string)
        
        Returns:
            Tuple (es_valido, mensaje_error)
            - True, None si es válido
            - False, "mensaje" si es inválido
        """
        try:
            # Parsear QR
            parts = qr_code.split('-')
            
            if len(parts) != 3:
                return False, "Formato de QR inválido"
            
            prefix, id_str, checksum_recibido = parts
            
            # Verificar prefijo
            if prefix != settings.ORG_PREFIX:
                return False, f"QR no pertenece a esta organización"
            
            # Verificar ID
            try:
                qr_miembro_id = int(id_str)
            except ValueError:
                return False, "ID de miembro inválido en QR"
            
            if qr_miembro_id != miembro_id:
                return False, "QR no corresponde a este miembro"
            
            # Recalcular checksum esperado
            # Usar fecha_alta como timestamp (el QR es inmutable)
            data_string = f"{miembro_id}|{numero_documento}|{fecha_alta}"
            hash_input = f"{data_string}|{settings.QR_SECRET_KEY}"
            checksum_esperado = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
            
            # Comparar checksums
            if checksum_recibido != checksum_esperado:
                return False, "QR adulterado o inválido"
            
            logger.info(f"[OK] QR válido para miembro #{miembro_id}")
            return True, None
        
        except Exception as e:
            logger.error(f"[ERROR] Error validando QR: {e}")
            return False, f"Error de validación: {str(e)}"
    
    @staticmethod
    def extraer_id_de_qr(qr_code: str) -> Optional[int]:
        """
        Extrae el ID del miembro de un código QR
        
        Args:
            qr_code: Código QR
        
        Returns:
            ID del miembro o None si es inválido
        """
        try:
            parts = qr_code.split('-')
            if len(parts) == 3:
                return int(parts[1])
        except:
            pass
        
        return None
    
    @staticmethod
    def generar_qr_simple(
        data: str,
        size: int = 300
    ) -> bytes:
        """
        Genera un QR simple sin personalización
        Útil para URLs, textos, etc.
        
        Args:
            data: Datos a codificar
            size: Tamaño de la imagen en pixels
        
        Returns:
            Imagen QR en bytes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionar
        img = img.resize((size, size), Image.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()