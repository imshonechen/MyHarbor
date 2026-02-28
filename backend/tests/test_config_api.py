from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import SiteConfig
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config


def _reset_config_data() -> None:
    init_database()
    login_rate_limiter.clear()
    with SessionLocal() as db:
        db.execute(delete(SiteConfig))
        db.commit()
        ensure_default_site_config(db)


def _login(client: TestClient, username: str = "admin", password: str = "admin123") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["token"]


def test_get_config_requires_auth_and_returns_values() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        unauthorized = client.get("/api/config")
        token = _login(client)
        authorized = client.get("/api/config", headers={"Authorization": f"Bearer {token}"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    payload = authorized.json()["data"]
    assert payload["site_title"] == "MyHarbor"
    assert payload["admin_username"] == "admin"
    assert isinstance(payload["check_interval"], int)


def test_update_public_config_applies_immediately() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        update_resp = client.put(
            "/api/config",
            headers=headers,
            json={
                "site_title": "MyHarbor Pro",
                "site_description": "new description",
                "copyright": "copyright 2026",
                "icp_number": "ICP-123456",
                "check_interval": 30,
            },
        )
        public_resp = client.get("/api/config/public")
        admin_resp = client.get("/api/config", headers=headers)

    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["updated"] is True
    assert public_resp.status_code == 200
    assert public_resp.json()["data"]["site_title"] == "MyHarbor Pro"
    assert admin_resp.status_code == 200
    assert admin_resp.json()["data"]["check_interval"] == 30


def test_update_admin_credentials_requires_relogin_and_new_credentials_work() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        old_token = _login(client)
        headers = {"Authorization": f"Bearer {old_token}"}
        update_resp = client.put(
            "/api/config",
            headers=headers,
            json={
                "admin_username": "new-admin",
                "admin_password": "new-password-123",
            },
        )
        old_me = client.get("/api/auth/me", headers=headers)
        old_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        new_login = client.post("/api/auth/login", json={"username": "new-admin", "password": "new-password-123"})

    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["relogin_required"] is True
    assert old_me.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_update_route_code_returns_new_code() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        update_resp = client.put(
            "/api/config",
            headers=headers,
            json={"admin_route_code": "Abc12345"},
        )
        config_resp = client.get("/api/config", headers=headers)

    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["new_route_code"] == "Abc12345"
    assert config_resp.status_code == 200
    assert config_resp.json()["data"]["admin_route_code"] == "Abc12345"


def test_copyright_html_is_sanitized_to_prevent_xss() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        raw = (
            '<a href="javascript:alert(1)" onclick="alert(2)">X</a> '
            '<a href="https://example.com" title="ok">MyHarbor</a>'
            "<script>alert(3)</script>"
        )
        update_resp = client.put("/api/config", headers=headers, json={"copyright": raw})
        public_resp = client.get("/api/config/public")
        admin_resp = client.get("/api/config", headers=headers)

    assert update_resp.status_code == 200
    assert public_resp.status_code == 200
    assert admin_resp.status_code == 200

    public_html = public_resp.json()["data"]["copyright"]
    admin_html = admin_resp.json()["data"]["copyright"]

    for html in (public_html, admin_html):
        assert "<script" not in html.lower()
        assert "onclick" not in html.lower()
        assert "javascript:" not in html.lower()
        assert "example.com" in html


def test_icp_number_html_is_sanitized_to_prevent_xss() -> None:
    _reset_config_data()
    app = create_app()
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        raw = (
            '<a href="javascript:alert(1)" onclick="alert(2)">ICP</a> '
            '<a href="https://beian.miit.gov.cn/" title="ok">备案信息</a>'
            "<script>alert(3)</script>"
        )
        update_resp = client.put("/api/config", headers=headers, json={"icp_number": raw})
        public_resp = client.get("/api/config/public")
        admin_resp = client.get("/api/config", headers=headers)

    assert update_resp.status_code == 200
    assert public_resp.status_code == 200
    assert admin_resp.status_code == 200

    public_html = public_resp.json()["data"]["icp_number"]
    admin_html = admin_resp.json()["data"]["icp_number"]

    for html in (public_html, admin_html):
        assert "<script" not in html.lower()
        assert "onclick" not in html.lower()
        assert "javascript:" not in html.lower()
        assert "beian.miit.gov.cn" in html
