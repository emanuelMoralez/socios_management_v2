"""
Modelo Pago - Registro de pagos y movimientos
backend/app/models/pago.py
"""
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    Enum as SQLEnum, Text, Date
)
from sqlalchemy.orm import relationship
from datetime import date
import enum

from app.models.base import BaseModel


class TipoPago(str, enum.Enum):
    """Tipos de pago"""
    CUOTA = "cuota"              # Cuota mensual/periódica
    INSCRIPCION = "inscripcion"  # Cuota de inscripción
    CONSUMO = "consumo"          # Pago por consumo (cooperativas)
    ACTIVIDAD = "actividad"      # Pago por actividad específica
    MULTA = "multa"              # Multa o recargo
    OTRO = "otro"                # Otros conceptos


class MetodoPago(str, enum.Enum):
    """Métodos de pago"""
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    DEPOSITO = "deposito"
    DEBITO = "debito"
    CREDITO = "credito"
    CHEQUE = "cheque"
    ONLINE = "online"  # Para fase 3


class EstadoPago(str, enum.Enum):
    """Estados del pago"""
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"


class Pago(BaseModel):
    """Registro de pagos realizados por miembros"""
    __tablename__ = "pagos"
    
    # Relación con miembro
    miembro_id = Column(Integer, ForeignKey("miembros.id"), nullable=False, index=True)
    miembro = relationship("Miembro", back_populates="pagos", lazy="selectin")
    
    # Datos del pago
    tipo = Column(SQLEnum(TipoPago), nullable=False)
    concepto = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Montos
    monto = Column(Float, nullable=False)
    descuento = Column(Float, default=0.0, nullable=False)
    recargo = Column(Float, default=0.0, nullable=False)
    monto_final = Column(Float, nullable=False)
    
    # Método y estado
    metodo_pago = Column(SQLEnum(MetodoPago), nullable=False)
    estado = Column(
        SQLEnum(EstadoPago),
        default=EstadoPago.PENDIENTE,
        nullable=False
    )
    
    # Fechas
    fecha_pago = Column(Date, default=date.today, nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    fecha_periodo = Column(Date, nullable=True)  # Ej: "Cuota de Enero 2025"
    
    # Comprobante
    numero_comprobante = Column(String(50), unique=True, nullable=True, index=True)
    comprobante_url = Column(String(500), nullable=True)  # PDF del recibo
    
    # Referencia externa (para integraciones fase 3)
    referencia_externa = Column(String(255), nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True)
    
    # Usuario que registró el pago
    registrado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    registrado_por = relationship("Usuario")
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    def calcular_monto_final(self):
        """Calcula el monto final con descuentos y recargos"""
        self.monto_final = self.monto - self.descuento + self.recargo
        return self.monto_final
    
    def generar_numero_comprobante(self):
        """Genera número de comprobante único"""
        # Formato: REC-2025-00001
        year = date.today().year
        # En una implementación real, buscar el último número
        return f"REC-{year}-{self.id:05d}"
    
    def __repr__(self):
        return (
            f"<Pago #{self.numero_comprobante}: "
            f"{self.concepto} - ${self.monto_final}>"
        )


class MovimientoCaja(BaseModel):
    """
    Movimientos de caja (ingresos y egresos generales)
    Contabilidad básica
    """
    __tablename__ = "movimientos_caja"
    
    # Tipo de movimiento
    tipo = Column(
        SQLEnum("ingreso", "egreso", name="tipo_movimiento"),
        nullable=False
    )
    
    # Datos
    concepto = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    monto = Column(Float, nullable=False)
    
    # Categoría contable
    categoria_contable = Column(String(100), nullable=True)
    
    # Fecha
    fecha_movimiento = Column(Date, default=date.today, nullable=False)
    
    # Comprobante
    numero_comprobante = Column(String(50), nullable=True)
    comprobante_url = Column(String(500), nullable=True)
    
    # Relación con pago (si corresponde)
    pago_id = Column(Integer, ForeignKey("pagos.id"), nullable=True)
    pago = relationship("Pago")
    
    # Usuario que registró
    registrado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    registrado_por = relationship("Usuario")
    
    def __repr__(self):
        signo = "+" if self.tipo == "ingreso" else "-"
        return f"<MovimientoCaja {signo}${self.monto}: {self.concepto}>"