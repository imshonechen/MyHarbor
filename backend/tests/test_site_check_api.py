from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import Site, SiteConfig, SiteStatusLog
from app.routers.auth import login_rate_limiter
from app.services import site_checker
from app.services.bootstrap import ensure_default_site_config


def _reset_check_data() -> None:
    init_database()
    login_rate_limiter.clear()
    with SessionLocal() as db:
        db.execute(delete(SiteStatusLog))
        db.execute(delete(Site))
        db.execute(delete(SiteConfig))
        db.commit()
        ensure_default_site_config(db)


def _login_and_get_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["data"]["token"]


def test_check_single_site_updates_status_and_creates_log(monkeypatch) -> None:
    _reset_check_data()
    app = create_app()

    with SessionLocal() as db:
        site = Site(name="Docs", url="https://docs.example.com", status="unknown")
        db.add(site)
        db.commit()
        db.refresh(site)
        site_id = site.id

    monkeypatch.setattr(site_checker, "check_site_url", lambda url, timeout_seconds=5: ("online", 123))

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(f"/api/sites/{site_id}/check", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["site_id"] == site_id
    assert payload["status"] == "online"
    assert payload["response_time"] == 123

    with SessionLocal() as db:
        updated = db.get(Site, site_id)
        logs = db.execute(select(SiteStatusLog).where(SiteStatusLog.site_id == site_id)).scalars().all()

    assert updated is not None
    assert updated.status == "online"
    assert updated.last_check_time is not None
    assert len(logs) == 1
    assert logs[0].status == "online"
    assert logs[0].response_time == 123


def test_check_all_sites_returns_summary_and_persists_logs(monkeypatch) -> None:
    _reset_check_data()
    app = create_app()

    with SessionLocal() as db:
        db.add_all(
            [
                Site(name="SiteA", url="https://a.example.com", status="unknown"),
                Site(name="SiteB", url="https://b.example.com", status="unknown"),
            ]
        )
        db.commit()

    def fake_check(url: str, timeout_seconds: int = 5) -> tuple[str, int | None]:
        if "a.example.com" in url:
            return "online", 90
        return "offline", None

    monkeypatch.setattr(site_checker, "check_site_url", fake_check)

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/sites/check-all", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 2
    assert payload["online"] == 1
    assert payload["offline"] == 1
    assert isinstance(payload["checked_at"], str)

    with SessionLocal() as db:
        logs = db.execute(select(SiteStatusLog)).scalars().all()
        sites = db.execute(select(Site).order_by(Site.id.asc())).scalars().all()

    assert len(logs) == 2
    assert sorted([item.status for item in logs]) == ["offline", "online"]
    assert sorted([item.status for item in sites]) == ["offline", "online"]


def test_check_single_site_returns_404_for_missing_site() -> None:
    _reset_check_data()
    app = create_app()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/sites/999999/check", headers=headers)

    assert response.status_code == 404


def test_list_site_status_logs_returns_recent_items() -> None:
    _reset_check_data()
    app = create_app()
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        site = Site(name="Docs", url="https://docs.example.com", status="unknown")
        db.add(site)
        db.commit()
        db.refresh(site)
        db.add_all(
            [
                SiteStatusLog(
                    site_id=site.id,
                    status="online",
                    response_time=88,
                    checked_at=now - timedelta(days=2),
                ),
                SiteStatusLog(
                    site_id=site.id,
                    status="offline",
                    response_time=None,
                    checked_at=now - timedelta(days=31),
                ),
            ]
        )
        db.commit()
        site_id = site.id

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/api/sites/{site_id}/status-logs", headers=headers, params={"days": 30})
        not_found = client.get("/api/sites/999999/status-logs", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["site_id"] == site_id
    assert len(payload["items"]) == 1
    assert payload["items"][0]["status"] == "online"
    assert payload["items"][0]["response_time"] == 88
    assert isinstance(payload["items"][0]["checked_at"], str)
    assert not_found.status_code == 404
