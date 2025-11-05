"""Tests para QRService - Generación y validación de códigos QR"""
import pytest
from app.services.qr_service import QRService


class TestGenerarQR:
    """Tests de generación de códigos QR"""
    
    def test_generar_qr_basico(self):
        """Test de generación básica sin personalización"""
        data = QRService.generar_qr_miembro(
            miembro_id=123,
            numero_documento="12345678",
            numero_miembro="M-00123",
            nombre_completo="Juan Perez",
            personalizar=False,
        )
        
        # Verificar estructura del dict
        assert isinstance(data, dict)
        assert "qr_code" in data
        assert "qr_hash" in data
        assert "image_bytes" in data
        assert "timestamp" in data
        assert "metadata" in data
        
        # Verificar formato del código
        assert data["qr_code"].startswith("CLUB-123-")
        assert len(data["qr_code"].split("-")) == 3  # CLUB-ID-CHECKSUM
        
        # Verificar que genera imagen
        assert isinstance(data["image_bytes"], (bytes, bytearray))
        assert len(data["image_bytes"]) > 0
    
    def test_generar_qr_personalizado(self):
        """Test de generación con personalización (nombre en QR)"""
        data = QRService.generar_qr_miembro(
            miembro_id=456,
            numero_documento="87654321",
            numero_miembro="M-00456",
            nombre_completo="Maria Lopez",
            personalizar=True,
        )
        
        assert data["qr_code"].startswith("CLUB-456-")
        assert data["metadata"]["miembro_id"] == 456
        assert data["metadata"]["checksum"] is not None
    
    def test_qr_hash_es_unico_por_miembro(self):
        """El hash debe ser único para cada miembro"""
        qr1 = QRService.generar_qr_miembro(1, "111", "M-001", "User 1", False)
        qr2 = QRService.generar_qr_miembro(2, "222", "M-002", "User 2", False)
        
        assert qr1["qr_hash"] != qr2["qr_hash"]
        assert qr1["qr_code"] != qr2["qr_code"]
    
    def test_qr_hash_es_consistente(self):
        """El mismo miembro debe generar el mismo formato de código"""
        qr1 = QRService.generar_qr_miembro(99, "999", "M-099", "Test User", False)
        qr2 = QRService.generar_qr_miembro(99, "999", "M-099", "Test User", False)
        
        # El código base debe ser el mismo (mismo ID)
        assert qr1["qr_code"].split("-")[1] == qr2["qr_code"].split("-")[1]  # Mismo ID


class TestValidarQR:
    """Tests de validación de códigos QR"""
    
    def test_extraer_id_valido(self):
        """Extraer ID de código QR válido"""
        assert QRService.extraer_id_de_qr("CLUB-42-abcdef0123456789") == 42
        assert QRService.extraer_id_de_qr("CLUB-1-xyz") == 1
        assert QRService.extraer_id_de_qr("CLUB-999-checksum") == 999
    
    def test_extraer_id_formato_invalido(self):
        """Códigos con formato inválido deben retornar None"""
        assert QRService.extraer_id_de_qr("INVALID") is None
        assert QRService.extraer_id_de_qr("CLUB-ABC-123") is None  # ID no numérico
        assert QRService.extraer_id_de_qr("CLUB-42") is None  # Falta checksum
        assert QRService.extraer_id_de_qr("") is None
    
    def test_validar_qr_correcto(self):
        """Validar QR generado correctamente debe retornar válido"""
        from datetime import datetime
        # Generar QR real y verificar que valida
        timestamp = datetime.utcnow().isoformat()
        data = QRService.generar_qr_miembro(777, "77777", "M-777", "Test", timestamp, False)
        qr_code = data["qr_code"]
        
        # El QR generado debe validar correctamente
        valido, mensaje = QRService.validar_qr(qr_code, 777, "77777", timestamp)
        assert valido is True
        assert mensaje is None
    
    def test_validar_qr_id_incorrecto(self):
        """QR con ID diferente debe fallar validación"""
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        # Generar QR para un miembro
        data = QRService.generar_qr_miembro(555, "55555", "M-555", "Test", timestamp, False)
        
        # Intentar validar con otro miembro_id
        valido, mensaje = QRService.validar_qr(data["qr_code"], 999, "55555", timestamp)
        assert valido is False
        assert mensaje is not None
    
    def test_validar_qr_documento_incorrecto(self):
        """QR con documento diferente debe fallar validación"""
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        data = QRService.generar_qr_miembro(888, "88888888", "M-888", "Test", timestamp, False)
        
        # Intentar validar con otro documento
        valido, mensaje = QRService.validar_qr(data["qr_code"], 888, "99999999", timestamp)
        assert valido is False
        assert mensaje is not None


class TestEdgeCases:
    """Tests de casos límite"""
    
    def test_id_muy_grande(self):
        """ID de miembro muy grande debe funcionar"""
        data = QRService.generar_qr_miembro(999999, "12345678", "M-999999", "Test", False)
        assert "CLUB-999999-" in data["qr_code"]
        assert QRService.extraer_id_de_qr(data["qr_code"]) == 999999
    
    def test_nombre_con_caracteres_especiales(self):
        """Nombres con tildes y ñ deben funcionar"""
        data = QRService.generar_qr_miembro(
            111, "11111", "M-111", "José Muñoz Peña", True
        )
        # Debe generar sin errores
        assert data["qr_code"].startswith("CLUB-111-")
        assert data["metadata"]["miembro_id"] == 111
    
    def test_documento_vacio(self):
        """Documento vacío no debe romper generación"""
        data = QRService.generar_qr_miembro(222, "", "M-222", "Test User", False)
        assert data["qr_code"].startswith("CLUB-222-")
