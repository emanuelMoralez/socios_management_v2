"""
Servicio de Generación de PDFs
backend/app/services/pdf_service.py
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from typing import Optional
import os

from app.config import settings


class PDFService:
    """Servicio para generación de documentos PDF"""
    
    @staticmethod
    def _get_logo_path() -> Optional[str]:
        """Obtener ruta del logo de la organización"""
        logo_path = os.path.join("static", "images", "logo.png")
        return logo_path if os.path.exists(logo_path) else None
    
    @staticmethod
    def _add_header(elements: list, titulo: str):
        """Agregar encabezado con logo y título"""
        styles = getSampleStyleSheet()
        
        # Logo (si existe)
        logo_path = PDFService._get_logo_path()
        if logo_path:
            logo = Image(logo_path, width=2*inch, height=0.8*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        
        # Título de organización
        org_style = ParagraphStyle(
            'OrgName',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(settings.ORG_NAME, org_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Título del documento
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(titulo, title_style))
        elements.append(Spacer(1, 0.3*inch))
    
    @staticmethod
    def _add_footer(canvas, doc):
        """Agregar pie de página"""
        canvas.saveState()
        
        # Fecha de generación
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            inch,
            0.5*inch,
            f"Generado: {fecha_generacion}"
        )
        
        # Número de página
        page_num = canvas.getPageNumber()
        canvas.drawRightString(
            doc.pagesize[0] - inch,
            0.5*inch,
            f"Página {page_num}"
        )
        
        canvas.restoreState()
    
    @staticmethod
    def generar_recibo_pago(
        numero_recibo: str,
        fecha_pago: datetime,
        miembro_nombre: str,
        miembro_numero: str,
        concepto: str,
        monto: float,
        metodo_pago: str,
        usuario_nombre: str,
        observaciones: Optional[str] = None
    ) -> BytesIO:
        """
        Generar recibo de pago en PDF
        
        Args:
            numero_recibo: Número de comprobante
            fecha_pago: Fecha del pago
            miembro_nombre: Nombre del socio
            miembro_numero: Número de socio
            concepto: Concepto del pago
            monto: Monto pagado
            metodo_pago: Método de pago (efectivo, transferencia, etc.)
            usuario_nombre: Usuario que registró el pago
            observaciones: Observaciones adicionales
        
        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Header
        PDFService._add_header(elements, "RECIBO DE PAGO")
        
        # Información del recibo
        recibo_data = [
            ["Número de Recibo:", numero_recibo],
            ["Fecha:", fecha_pago.strftime("%d/%m/%Y %H:%M")],
        ]
        
        recibo_table = Table(recibo_data, colWidths=[2*inch, 4*inch])
        recibo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(recibo_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Datos del socio
        elements.append(Paragraph("<b>DATOS DEL SOCIO</b>", styles['Heading3']))
        socio_data = [
            ["Nombre:", miembro_nombre],
            ["N° Socio:", miembro_numero],
        ]
        
        socio_table = Table(socio_data, colWidths=[2*inch, 4*inch])
        socio_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(socio_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Detalles del pago
        elements.append(Paragraph("<b>DETALLES DEL PAGO</b>", styles['Heading3']))
        pago_data = [
            ["Concepto:", concepto],
            ["Monto:", f"$ {monto:,.2f}"],
            ["Método de Pago:", metodo_pago.replace("_", " ").title()],
        ]
        
        pago_table = Table(pago_data, colWidths=[2*inch, 4*inch])
        pago_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            # Destacar monto
            ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (1, 1), 14),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#006600')),
        ]))
        elements.append(pago_table)
        
        # Observaciones
        if observaciones:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("<b>Observaciones:</b>", styles['Normal']))
            elements.append(Paragraph(observaciones, styles['Normal']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Firma
        firma_style = ParagraphStyle(
            'Firma',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER
        )
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("_" * 40, firma_style))
        elements.append(Paragraph(f"<b>{usuario_nombre}</b>", firma_style))
        elements.append(Paragraph("Firma y Sello", firma_style))
        
        # Generar PDF
        doc.build(elements, onFirstPage=PDFService._add_footer, onLaterPages=PDFService._add_footer)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generar_credencial_socio(
        miembro_nombre: str,
        miembro_numero: str,
        categoria: str,
        fecha_alta: datetime,
        qr_image_bytes: bytes,
        foto_bytes: Optional[bytes] = None
    ) -> BytesIO:
        """
        Generar credencial de socio en PDF
        
        Args:
            miembro_nombre: Nombre completo del socio
            miembro_numero: Número de socio
            categoria: Categoría del socio
            fecha_alta: Fecha de alta
            qr_image_bytes: Bytes del QR en formato PNG
            foto_bytes: Foto del socio (opcional)
        
        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()
        
        # Tamaño de credencial (formato tarjeta)
        pagesize = (3.5*inch, 2.2*inch)
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            rightMargin=0.2*inch,
            leftMargin=0.2*inch,
            topMargin=0.2*inch,
            bottomMargin=0.2*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Logo pequeño
        logo_path = PDFService._get_logo_path()
        if logo_path:
            logo = Image(logo_path, width=1*inch, height=0.4*inch)
            elements.append(logo)
        
        # Nombre de organización
        org_style = ParagraphStyle(
            'OrgSmall',
            fontSize=10,
            textColor=colors.HexColor('#366092'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(settings.ORG_NAME, org_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Datos del socio
        nombre_style = ParagraphStyle(
            'Nombre',
            fontSize=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(miembro_nombre, nombre_style))
        
        datos_style = ParagraphStyle(
            'Datos',
            fontSize=9,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"N° Socio: <b>{miembro_numero}</b>", datos_style))
        elements.append(Paragraph(f"Categoría: {categoria}", datos_style))
        elements.append(Paragraph(f"Desde: {fecha_alta.strftime('%d/%m/%Y')}", datos_style))
        
        elements.append(Spacer(1, 0.1*inch))
        
        # QR Code
        qr_buffer = BytesIO(qr_image_bytes)
        qr_image = Image(qr_buffer, width=1*inch, height=1*inch)
        elements.append(qr_image)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generar_reporte_custom(
        titulo: str,
        datos_tabla: list,
        headers_tabla: list,
        descripcion: Optional[str] = None
    ) -> BytesIO:
        """
        Generar reporte personalizado con tabla de datos
        
        Args:
            titulo: Título del reporte
            datos_tabla: Lista de listas con los datos
            headers_tabla: Lista con nombres de columnas
            descripcion: Descripción opcional del reporte
        
        Returns:
            BytesIO con el PDF generado
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Header
        PDFService._add_header(elements, titulo)
        
        # Descripción
        if descripcion:
            elements.append(Paragraph(descripcion, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Tabla
        tabla_data = [headers_tabla] + datos_tabla
        
        tabla = Table(tabla_data)
        tabla.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        elements.append(tabla)
        
        doc.build(elements, onFirstPage=PDFService._add_footer, onLaterPages=PDFService._add_footer)
        buffer.seek(0)
        return buffer