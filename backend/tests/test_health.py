from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_service_state() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"ok", "error"}

