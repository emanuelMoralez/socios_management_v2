"""
Métricas y observabilidad
backend/app/metrics.py

Expone una pequeña capa de abstracción sobre prometheus_client con
fallback seguro cuando la librería no está instalada. De esta forma
el backend no rompe en entornos sin dependencias extra, pero permite
activar métricas simplemente instalando prometheus-client.
"""
from __future__ import annotations

import time
from typing import Optional, TYPE_CHECKING, Any

try:
    # Import opcional: si no está disponible, activamos un modo "no-op"
    from prometheus_client import Counter, Histogram, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest  # type: ignore[import-not-found]
    _PROM_AVAILABLE = True
except Exception:  # ImportError u otros problemas de entorno
    Counter = Histogram = CollectorRegistry = object  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"  # tipo por defecto
    def generate_latest(_registry):  # type: ignore
        return b"# metrics disabled (prometheus_client no instalado)\n"
    _PROM_AVAILABLE = False

if TYPE_CHECKING:
    # Tipos solo para el analizador estático
    from prometheus_client import Counter as _Counter, Histogram as _Histogram, CollectorRegistry as _CollectorRegistry  # type: ignore[import-not-found]
else:
    _Counter = _Histogram = _CollectorRegistry = Any  # type: ignore


# Registro y métricas globales (lazy init)
_registry: Optional["_CollectorRegistry"] = None
_http_requests_total: Optional["_Counter"] = None
_http_request_duration_seconds: Optional["_Histogram"] = None
_audit_events_total: Optional["_Counter"] = None


def init_metrics() -> None:
    """Inicializa el registro y las métricas si Prometheus está disponible."""
    global _registry, _http_requests_total, _http_request_duration_seconds, _audit_events_total

    if not _PROM_AVAILABLE:
        # Sin librería: no hacemos nada, pero mantenemos API estable
        return

    if _registry is not None:
        return  # ya inicializado

    _registry = CollectorRegistry()

    _http_requests_total = Counter(
        "http_requests_total",
        "Total de requests HTTP",
        labelnames=("method", "path", "status"),
        registry=_registry,
    )

    _http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "Duración de requests HTTP en segundos",
        labelnames=("method", "path"),
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
        registry=_registry,
    )

    _audit_events_total = Counter(
        "audit_events_total",
        "Eventos de auditoría registrados",
        labelnames=("tipo", "severidad"),
        registry=_registry,
    )


def track_http(method: str, path: str, status: int, duration_seconds: float) -> None:
    """Actualiza contadores y histogramas de HTTP si están disponibles."""
    if _PROM_AVAILABLE and _registry is not None and _http_requests_total and _http_request_duration_seconds:
        try:
            _http_requests_total.labels(method=method, path=path, status=str(status)).inc()
            _http_request_duration_seconds.labels(method=method, path=path).observe(duration_seconds)
        except Exception:
            # Nunca romper por métricas
            pass


def inc_audit(tipo: str, severidad: str) -> None:
    """Incrementa contador de eventos de auditoría si está disponible."""
    if _PROM_AVAILABLE and _registry is not None and _audit_events_total:
        try:
            _audit_events_total.labels(tipo=tipo, severidad=severidad).inc()
        except Exception:
            pass


def get_metrics_text() -> tuple[bytes, str]:
    """
    Devuelve (payload, content_type) para el endpoint /metrics.
    Si Prometheus no está disponible, devuelve un comentario informativo.
    """
    if _PROM_AVAILABLE and _registry is not None:
        try:
            return generate_latest(_registry), CONTENT_TYPE_LATEST
        except Exception:
            # Evitar fallos por errores de serialización
            return b"# error generando metricas\n", CONTENT_TYPE_LATEST
    # Fallback
    return b"# metrics disabled (prometheus_client no instalado)\n", CONTENT_TYPE_LATEST


def now() -> float:
    """Helper para timestamp de alta resolución (segundos como float)."""
    return time.perf_counter()
