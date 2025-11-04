"""
Tests para endpoints de exportación a Excel

Valida que los endpoints de exportación devuelvan archivos Excel válidos
con los headers y content-type correctos.
"""

import pytest
from fastapi.testclient import TestClient


def test_exportar_socios_excel(client: TestClient, auth_tokens: dict):
    """
    Test exportar socios a Excel - debe devolver archivo con content-type correcto
    Exporta incluso si no hay datos (archivo Excel vacío pero válido)
    """
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    
    # Exportar socios a Excel (puede estar vacío, pero debe devolver un archivo válido)
    r = client.get("/api/reportes/exportar/socios/excel", headers=headers)
    
    assert r.status_code == 200, r.text
    # Verificar content-type
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in r.headers["content-type"]
    # Verificar header Content-Disposition
    disposition = r.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "socios" in disposition and ".xlsx" in disposition
    # Verificar que el contenido no esté vacío (archivo Excel mínimo tiene header)
    assert len(r.content) > 0


def test_exportar_pagos_excel(client: TestClient, auth_tokens: dict):
    """
    Test exportar pagos a Excel - debe devolver archivo con content-type correcto
    Exporta incluso si no hay datos (archivo Excel vacío pero válido)
    """
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    
    # Exportar pagos a Excel (puede estar vacío, pero debe devolver un archivo válido)
    r = client.get("/api/reportes/exportar/pagos/excel", headers=headers)
    
    assert r.status_code == 200, r.text
    # Verificar content-type
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in r.headers["content-type"]
    # Verificar header Content-Disposition
    disposition = r.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "pagos" in disposition and ".xlsx" in disposition
    # Verificar contenido no vacío (archivo Excel mínimo tiene header)
    assert len(r.content) > 0


def test_exportar_morosidad_excel(client: TestClient, auth_tokens: dict):
    """
    Test exportar morosidad a Excel - debe devolver archivo con content-type correcto
    Exporta incluso si no hay datos (archivo Excel vacío pero válido)
    """
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    
    # Exportar morosidad a Excel (puede estar vacío, pero debe devolver un archivo válido)
    r = client.get("/api/reportes/exportar/morosidad/excel", headers=headers)
    
    assert r.status_code == 200, r.text
    # Verificar content-type
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in r.headers["content-type"]
    # Verificar header Content-Disposition
    disposition = r.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "morosidad" in disposition and ".xlsx" in disposition
    # Verificar contenido no vacío (archivo Excel mínimo tiene header)
    assert len(r.content) > 0


def test_exportar_socios_sin_autenticacion(client: TestClient):
    """
    Verificar que los endpoints de exportación requieren autenticación
    """
    # Sin header de autorización -> FastAPI devuelve 403 cuando falta el token, no 401
    r = client.get("/api/reportes/exportar/socios/excel")
    assert r.status_code in [401, 403], "Debe requerir autenticación"
    
    r = client.get("/api/reportes/exportar/pagos/excel")
    assert r.status_code in [401, 403], "Debe requerir autenticación"
    
    r = client.get("/api/reportes/exportar/morosidad/excel")
    assert r.status_code in [401, 403], "Debe requerir autenticación"
