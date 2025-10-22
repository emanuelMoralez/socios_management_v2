"""
Importación centralizada de todos los schemas
backend/app/schemas/__init__.py
"""

# Common
from app.schemas.common import (
    MessageResponse,
    SuccessResponse,
    ErrorResponse,
    PaginationMeta,
    PaginatedResponse,
    OrderBy,
    DateRangeFilter,
    TimestampMixin,
    IDResponse
)

# Auth
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    TokenPayload
)

# Usuario
from app.schemas.usuario import (
    UsuarioBase,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListItem,
    UsuarioProfile,
    UpdateProfile,
    CambiarRolRequest,
    ToggleActiveRequest
)

# Miembro
from app.schemas.miembro import (
    CategoriaBase,
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse,
    MiembroBase,
    MiembroCreate,
    MiembroUpdate,
    MiembroResponse,
    MiembroListItem,
    GenerarQRRequest,
    QRResponse,
    MiembroSearchParams,
    EstadoFinanciero,
    CambiarEstadoRequest,
    DarDeBajaRequest
)

# Pago
from app.schemas.pago import (
    PagoBase,
    PagoCreate,
    PagoUpdate,
    PagoResponse,
    PagoListItem,
    RegistrarPagoRapido,
    AnularPagoRequest,
    MovimientoCajaBase,
    MovimientoCajaCreate,
    MovimientoCajaResponse,
    ResumenFinanciero,
    EstadisticasPago,
    ExportarPagosRequest,
    GenerarComprobanteRequest
)

# Acceso
from app.schemas.acceso import (
    ValidarQRRequest,
    ValidarQRResponse,
    RegistrarAccesoManual,
    AccesoResponse,
    AccesoListItem,
    HistorialAccesosMiembro,
    FiltroHistorialAccesos,
    EstadisticasAcceso,
    AccesosPorDia,
    ResumenAccesos,
    EventoAccesoBase,
    EventoAccesoCreate,
    EventoAccesoUpdate,
    EventoAccesoResponse,
    AlertaAcceso,
    ConfiguracionAcceso,
    ExportarAccesosRequest
)

__all__ = [
    # Common
    "MessageResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginationMeta",
    "PaginatedResponse",
    "OrderBy",
    "DateRangeFilter",
    "TimestampMixin",
    "IDResponse",
    
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "ForgotPasswordRequest",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "TokenPayload",
    
    # Usuario
    "UsuarioBase",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioResponse",
    "UsuarioListItem",
    "UsuarioProfile",
    "UpdateProfile",
    "CambiarRolRequest",
    "ToggleActiveRequest",
    
    # Miembro
    "CategoriaBase",
    "CategoriaCreate",
    "CategoriaUpdate",
    "CategoriaResponse",
    "MiembroBase",
    "MiembroCreate",
    "MiembroUpdate",
    "MiembroResponse",
    "MiembroListItem",
    "GenerarQRRequest",
    "QRResponse",
    "MiembroSearchParams",
    "EstadoFinanciero",
    "CambiarEstadoRequest",
    "DarDeBajaRequest",
    
    # Pago
    "PagoBase",
    "PagoCreate",
    "PagoUpdate",
    "PagoResponse",
    "PagoListItem",
    "RegistrarPagoRapido",
    "AnularPagoRequest",
    "MovimientoCajaBase",
    "MovimientoCajaCreate",
    "MovimientoCajaResponse",
    "ResumenFinanciero",
    "EstadisticasPago",
    "ExportarPagosRequest",
    "GenerarComprobanteRequest",
    
    # Acceso
    "ValidarQRRequest",
    "ValidarQRResponse",
    "RegistrarAccesoManual",
    "AccesoResponse",
    "AccesoListItem",
    "HistorialAccesosMiembro",
    "FiltroHistorialAccesos",
    "EstadisticasAcceso",
    "AccesosPorDia",
    "ResumenAccesos",
    "EventoAccesoBase",
    "EventoAccesoCreate",
    "EventoAccesoUpdate",
    "EventoAccesoResponse",
    "AlertaAcceso",
    "ConfiguracionAcceso",
    "ExportarAccesosRequest",
]