"""
Validadores reutilizables para formularios
frontend-desktop/src/utils/validators.py
"""
import re
from typing import Tuple


def validar_email(email: str) -> Tuple[bool, str]:
    """
    Validar formato de email
    
    Returns:
        (es_valido, mensaje_error)
    """
    if not email:
        return False, "Email es obligatorio"
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        return False, "Email inválido"
    return True, ""


def validar_documento(doc: str, tipo: str = "dni") -> Tuple[bool, str]:
    """
    Validar documento de identidad
    
    Args:
        doc: Número de documento
        tipo: Tipo de documento (dni, cuil, cuit, etc.)
    
    Returns:
        (es_valido, mensaje_error)
    """
    if not doc or not doc.strip():
        return False, "Documento es obligatorio"
    if tipo == "dni" and (len(doc) < 7 or len(doc) > 8):
        return False, "DNI debe tener 7-8 dígitos"
    if not doc.isdigit():
        return False, "Documento debe ser numérico"
    return True, ""


def validar_telefono(tel: str) -> Tuple[bool, str]:
    """
    Validar número de teléfono
    
    Returns:
        (es_valido, mensaje_error)
    """
    if not tel:
        return True, ""  # Opcional
    if len(tel) < 8 or len(tel) > 15:
        return False, "Teléfono debe tener 8-15 dígitos"
    return True, ""


def validar_monto(monto_str: str, permitir_cero: bool = False) -> Tuple[bool, str, float]:
    """
    Validar y convertir monto monetario
    
    Args:
        monto_str: String con el monto
        permitir_cero: Si False, rechaza montos de 0
    
    Returns:
        (es_valido, mensaje_error, monto_float)
    """
    if not monto_str or not monto_str.strip():
        return False, "Monto es obligatorio", 0.0
    
    try:
        monto = float(monto_str)
        if monto < 0:
            return False, "El monto no puede ser negativo", 0.0
        if not permitir_cero and monto == 0:
            return False, "El monto debe ser mayor a cero", 0.0
        return True, "", monto
    except ValueError:
        return False, "Ingresa un monto válido", 0.0


def validar_fecha(fecha_str: str, formato: str = "%Y-%m-%d") -> Tuple[bool, str]:
    """
    Validar formato de fecha
    
    Args:
        fecha_str: String con la fecha
        formato: Formato esperado (default: YYYY-MM-DD)
    
    Returns:
        (es_valido, mensaje_error)
    """
    if not fecha_str:
        return False, "Fecha es obligatoria"
    
    from datetime import datetime
    try:
        datetime.strptime(fecha_str, formato)
        return True, ""
    except ValueError:
        return False, f"Formato de fecha inválido. Use: {formato}"


def validar_nombre_completo(nombre: str, apellido: str) -> Tuple[bool, str]:
    """
    Validar nombre y apellido
    
    Returns:
        (es_valido, mensaje_error)
    """
    if not nombre or not nombre.strip():
        return False, "Nombre es obligatorio"
    if not apellido or not apellido.strip():
        return False, "Apellido es obligatorio"
    if len(nombre.strip()) < 2:
        return False, "Nombre debe tener al menos 2 caracteres"
    if len(apellido.strip()) < 2:
        return False, "Apellido debe tener al menos 2 caracteres"
    return True, ""


def validar_numero_positivo(numero_str: str, nombre_campo: str = "Número") -> Tuple[bool, str, int]:
    """
    Validar número entero positivo
    
    Returns:
        (es_valido, mensaje_error, numero_int)
    """
    if not numero_str or not numero_str.strip():
        return False, f"{nombre_campo} es obligatorio", 0
    
    try:
        numero = int(numero_str)
        if numero <= 0:
            return False, f"{nombre_campo} debe ser positivo", 0
        return True, "", numero
    except ValueError:
        return False, f"{nombre_campo} debe ser un número entero", 0