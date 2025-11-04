from app.services.qr_service import QRService


def test_generar_qr_miembro_shape():
    data = QRService.generar_qr_miembro(
        miembro_id=123,
        numero_documento="12345678",
        numero_miembro="M-00123",
        nombre_completo="Juan Perez",
        personalizar=False,
    )
    assert isinstance(data, dict)
    for key in ("qr_code", "qr_hash", "image_bytes", "timestamp", "metadata"):
        assert key in data
    assert data["qr_code"].startswith("CLUB-123-")
    assert isinstance(data["image_bytes"], (bytes, bytearray))


def test_extraer_id_de_qr():
    qr = "CLUB-42-abcdef0123456789"
    assert QRService.extraer_id_de_qr(qr) == 42
