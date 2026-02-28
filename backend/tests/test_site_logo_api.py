from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import Site, SiteConfig, SiteStatusLog, VisitLog, VisitStats
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config


def _reset_data() -> None:
    init_database()
    login_rate_limiter.clear()
    with SessionLocal() as db:
        db.execute(delete(SiteStatusLog))
        db.execute(delete(VisitStats))
        db.execute(delete(VisitLog))
        db.execute(delete(Site))
        db.execute(delete(SiteConfig))
        db.commit()
        ensure_default_site_config(db)


def _login_and_get_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["data"]["token"]


def test_fetch_site_logo_requires_authentication() -> None:
    _reset_data()
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/sites/logo", params={"url": "https://example.com"})
    assert response.status_code == 401


def test_fetch_site_logo_returns_logo_url(monkeypatch) -> None:
    _reset_data()
    app = create_app()

    import app.routers.sites as sites_router

    monkeypatch.setattr(
        sites_router,
        "fetch_site_logo_url",
        lambda url, timeout_seconds=5: "https://example.com/icon-512.png",
    )

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/sites/logo", headers=headers, params={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["data"]["logo_url"] == "https://example.com/icon-512.png"


def test_fetch_site_logo_returns_null_when_not_found(monkeypatch) -> None:
    _reset_data()
    app = create_app()

    import app.routers.sites as sites_router

    monkeypatch.setattr(sites_router, "fetch_site_logo_url", lambda url, timeout_seconds=5: None)

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/sites/logo", headers=headers, params={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["data"]["logo_url"] is None


def test_fetch_site_logo_validates_url_scheme() -> None:
    _reset_data()
    app = create_app()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/sites/logo", headers=headers, params={"url": "ftp://example.com"})

    assert response.status_code == 400
