from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.config import get_settings
from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import SiteConfig
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config
from app.utils.security import create_access_token


def _reset_admin_config() -> None:
    init_database()
    login_rate_limiter.clear()
    with SessionLocal() as db:
        db.execute(delete(SiteConfig))
        db.commit()
        ensure_default_site_config(db)


def test_login_success_returns_jwt_token() -> None:
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["username"] == "admin"
    assert isinstance(payload["data"]["token"], str)
    assert payload["data"]["token"]
    assert isinstance(payload["data"]["expires_at"], str)


def test_login_failure_with_invalid_password() -> None:
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )

    assert response.status_code == 401


def test_protected_endpoint_requires_valid_token() -> None:
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        unauthorized = client.get("/api/auth/me")
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = login.json()["data"]["token"]
        authorized = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json()["data"]["username"] == "admin"


def test_expired_token_is_rejected() -> None:
    _reset_admin_config()
    app = create_app()
    settings = get_settings()
    expired_token, _ = create_access_token(
        subject="admin",
        secret_key=settings.jwt_secret,
        expires_delta=timedelta(seconds=-1),
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

    assert response.status_code == 401


def test_login_is_rate_limited_by_client_ip() -> None:
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong-password"},
                headers={"x-forwarded-for": "10.10.10.1"},
            )
            assert response.status_code == 401

        blocked = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
            headers={"x-forwarded-for": "10.10.10.1"},
        )
        other_ip = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
            headers={"x-forwarded-for": "10.10.10.2"},
        )

    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") == "900"
    assert other_ip.status_code == 401
