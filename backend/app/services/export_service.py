"""
Servicio de Exportación de Reportes
backend/app/services/export_service.py
"""
from io import BytesIO
from datetime import datetime, date
from typing import List, Dict, Any
import logging

# Excel
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class ExportService:
    """Servicio para exportar reportes en diferentes formatos"""
    
    @staticmethod
    def exportar_socios_excel(socios: List[Dict[str, Any]], filename: str = None) -> BytesIO:
        """
        Exportar lista de socios a Excel
        
        Args:
            socios: Lista de diccionarios con datos de socios
            filename: Nombre del archivo (opcional)
        
        Returns:
            BytesIO con el archivo Excel
        """
        if not filename:
            filename = f"socios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Socios"
        
        # Estilos
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Headers
        headers = [
            "N° Socio", "Documento", "Nombre Completo", "Email", 
            "Teléfono", "Estado", "Categoría", "Saldo", "Fecha Alta"
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        
        # Datos
        for row_num, socio in enumerate(socios, 2):
            ws.cell(row=row_num, column=1).value = socio.get("numero_miembro", "")
            ws.cell(row=row_num, column=2).value = socio.get("numero_documento", "")
            ws.cell(row=row_num, column=3).value = socio.get("nombre_completo", "")
            ws.cell(row=row_num, column=4).value = socio.get("email", "")
            ws.cell(row=row_num, column=5).value = socio.get("telefono", "")
            ws.cell(row=row_num, column=6).value = socio.get("estado", "").upper()
            
            categoria = socio.get("categoria")
            ws.cell(row=row_num, column=7).value = categoria.get("nombre", "") if categoria else ""
            
            ws.cell(row=row_num, column=8).value = socio.get("saldo_cuenta", 0)
            ws.cell(row=row_num, column=8).number_format = '$#,##0.00'
            
            fecha_alta = socio.get("fecha_alta")
            if fecha_alta:
                if isinstance(fecha_alta, str):
                    fecha_alta = datetime.fromisoformat(fecha_alta).date()
                ws.cell(row=row_num, column=9).value = fecha_alta
                ws.cell(row=row_num, column=9).number_format = 'DD/MM/YYYY'
            
            # Aplicar bordes
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_num, column=col).border = border
        
        # Ajustar ancho de columnas
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
        
        ws.column_dimensions['C'].width = 30  # Nombre completo
        ws.column_dimensions['D'].width = 25  # Email
        
        # Agregar filtros
        ws.auto_filter.ref = ws.dimensions
        
        # Guardar en BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        logger.info(f"Exportados {len(socios)} socios a Excel")
        return output
    
    @staticmethod
    def exportar_pagos_excel(pagos: List[Dict[str, Any]], filename: str = None) -> BytesIO:
        """Exportar lista de pagos a Excel"""
        if not filename:
            filename = f"pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Pagos"
        
        # Estilos
        header_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Headers
        headers = [
            "Comprobante", "Fecha", "Socio", "N° Socio", "Concepto",
            "Monto", "Descuento", "Recargo", "Total", "Método", "Estado"
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        
        # Datos
        for row_num, pago in enumerate(pagos, 2):
            ws.cell(row=row_num, column=1).value = pago.get("numero_comprobante", "")
            
            fecha_pago = pago.get("fecha_pago")
            if fecha_pago:
                if isinstance(fecha_pago, str):
                    fecha_pago = datetime.fromisoformat(fecha_pago).date()
                ws.cell(row=row_num, column=2).value = fecha_pago
                ws.cell(row=row_num, column=2).number_format = 'DD/MM/YYYY'
            
            ws.cell(row=row_num, column=3).value = pago.get("nombre_miembro", "")
            
            # Obtener número de socio si está en miembro
            miembro = pago.get("miembro")
            if miembro:
                ws.cell(row=row_num, column=4).value = miembro.get("numero_miembro", "")
            
            ws.cell(row=row_num, column=5).value = pago.get("concepto", "")
            
            # Montos
            ws.cell(row=row_num, column=6).value = pago.get("monto", 0)
            ws.cell(row=row_num, column=6).number_format = '$#,##0.00'
            
            ws.cell(row=row_num, column=7).value = pago.get("descuento", 0)
            ws.cell(row=row_num, column=7).number_format = '$#,##0.00'
            
            ws.cell(row=row_num, column=8).value = pago.get("recargo", 0)
            ws.cell(row=row_num, column=8).number_format = '$#,##0.00'
            
            ws.cell(row=row_num, column=9).value = pago.get("monto_final", 0)
            ws.cell(row=row_num, column=9).number_format = '$#,##0.00'
            
            ws.cell(row=row_num, column=10).value = pago.get("metodo_pago", "").upper()
            ws.cell(row=row_num, column=11).value = pago.get("estado", "").upper()
            
            # Aplicar bordes
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_num, column=col).border = border
        
        # Ajustar ancho de columnas
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
        
        ws.column_dimensions['C'].width = 25  # Nombre socio
        ws.column_dimensions['E'].width = 30  # Concepto
        
        # Fila de totales
        total_row = len(pagos) + 2
        ws.cell(row=total_row, column=5).value = "TOTAL"
        ws.cell(row=total_row, column=5).font = Font(bold=True)
        
        # Sumar montos finales
        ws.cell(row=total_row, column=9).value = f'=SUM(I2:I{len(pagos)+1})'
        ws.cell(row=total_row, column=9).number_format = '$#,##0.00'
        ws.cell(row=total_row, column=9).font = Font(bold=True)
        ws.cell(row=total_row, column=9).fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        
        # Filtros
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(pagos)+1}"
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        logger.info(f"Exportados {len(pagos)} pagos a Excel")
        return output
    
    @staticmethod
    def exportar_morosidad_excel(morosos: List[Dict[str, Any]], filename: str = None) -> BytesIO:
        """Exportar reporte de morosidad a Excel"""
        if not filename:
            filename = f"morosidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Morosidad"
        
        # Estilos
        header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Headers
        headers = [
            "N° Socio", "Nombre Completo", "Email", "Teléfono",
            "Deuda", "Días Mora", "Última Cuota", "Categoría"
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        
        # Datos
        for row_num, moroso in enumerate(morosos, 2):
            ws.cell(row=row_num, column=1).value = moroso.get("numero_miembro", "")
            ws.cell(row=row_num, column=2).value = moroso.get("nombre_completo", "")
            ws.cell(row=row_num, column=3).value = moroso.get("email", "")
            ws.cell(row=row_num, column=4).value = moroso.get("telefono", "")
            
            ws.cell(row=row_num, column=5).value = moroso.get("deuda", 0)
            ws.cell(row=row_num, column=5).number_format = '$#,##0.00'
            
            ws.cell(row=row_num, column=6).value = moroso.get("dias_mora", 0)
            
            ultima_cuota = moroso.get("ultima_cuota_pagada")
            if ultima_cuota:
                if isinstance(ultima_cuota, str):
                    ultima_cuota = datetime.fromisoformat(ultima_cuota).date()
                ws.cell(row=row_num, column=7).value = ultima_cuota
                ws.cell(row=row_num, column=7).number_format = 'DD/MM/YYYY'
            
            ws.cell(row=row_num, column=8).value = moroso.get("categoria", "")
            
            # Aplicar bordes
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_num, column=col).border = border
            
            # Colorear según deuda
            deuda = moroso.get("deuda", 0)
            if deuda > 5000:
                fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif deuda > 2000:
                fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            
            ws.cell(row=row_num, column=5).fill = fill
        
        # Ajustar anchos
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 20
        
        # Fila de totales
        total_row = len(morosos) + 2
        ws.cell(row=total_row, column=4).value = "TOTAL DEUDA"
        ws.cell(row=total_row, column=4).font = Font(bold=True)
        ws.cell(row=total_row, column=4).alignment = Alignment(horizontal="right")
        
        ws.cell(row=total_row, column=5).value = f'=SUM(E2:E{len(morosos)+1})'
        ws.cell(row=total_row, column=5).number_format = '$#,##0.00'
        ws.cell(row=total_row, column=5).font = Font(bold=True, size=14)
        ws.cell(row=total_row, column=5).fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        ws.cell(row=total_row, column=5).font = Font(bold=True, color="FFFFFF", size=14)
        
        # Filtros
        ws.auto_filter.ref = ws.dimensions
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        logger.info(f"Exportados {len(morosos)} morosos a Excel")
        return output
    
    @staticmethod
    def exportar_reporte_pdf(
        titulo: str,
        subtitulo: str,
        datos: List[Dict[str, Any]],
        columnas: List[str],
        filename: str = None
    ) -> BytesIO:
        """
        Exportar reporte genérico a PDF
        
        Args:
            titulo: Título del reporte
            subtitulo: Subtítulo (ej: fecha)
            datos: Lista de diccionarios con los datos
            columnas: Lista de nombres de columnas a mostrar
            filename: Nombre del archivo
        
        Returns:
            BytesIO con el PDF
        """
        if not filename:
            filename = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=1  # Centrado
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=1
        )
        
        # Título
        elements.append(Paragraph(titulo, title_style))
        elements.append(Paragraph(subtitulo, subtitle_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Preparar datos para la tabla
        table_data = [columnas]  # Headers
        
        for item in datos:
            row = [str(item.get(col, "")) for col in columnas]
            table_data.append(row)
        
        # Crear tabla
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        # Agregar pie de página con fecha
        elements.append(Spacer(1, 0.3 * inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=2  # Derecha
        )
        elements.append(
            Paragraph(
                f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                footer_style
            )
        )
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info(f"Generado PDF: {titulo}")
        return buffer