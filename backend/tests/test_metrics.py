"""
Pruebas de endpoint /metrics y header X-Request-ID
"""

def test_metrics_endpoint_available(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    # Debe ser texto plano (Prometheus o fallback)
    assert r.headers.get("content-type", "").startswith("text/plain")
    assert isinstance(r.content, (bytes, bytearray))
    # Primer caracter suele ser '#' en formato Prometheus
    assert r.content.strip().startswith(b"#")


def test_request_id_header_present(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert r.headers["X-Request-ID"].strip() != ""
