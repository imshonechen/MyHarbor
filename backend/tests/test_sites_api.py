from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import Site, SiteConfig, SiteStatusLog, VisitLog, VisitStats
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config


def _reset_sites_data() -> None:
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


def test_sites_endpoints_require_authentication() -> None:
    _reset_sites_data()
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/sites")
    assert response.status_code == 401


def test_create_list_update_toggle_delete_site() -> None:
    _reset_sites_data()
    app = create_app()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post(
            "/api/sites",
            headers=headers,
            json={
                "name": "Docs",
                "url": "https://docs.example.com",
                "description": "Documentation portal",
                "tags": ["tools", "docs"],
                "is_public": True,
                "sort_order": 2,
            },
        )
        assert create_resp.status_code == 200
        site_id = create_resp.json()["data"]["id"]

        list_resp = client.get("/api/sites", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["data"]["total"] == 1

        update_resp = client.put(
            f"/api/sites/{site_id}",
            headers=headers,
            json={"name": "Docs Hub", "url": "https://docs-hub.example.com", "is_public": False},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["name"] == "Docs Hub"
        assert update_resp.json()["data"]["is_public"] is False

        toggle_resp = client.patch(f"/api/sites/{site_id}/toggle", headers=headers)
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["data"]["is_public"] is True

        delete_resp = client.delete(f"/api/sites/{site_id}", headers=headers)
        assert delete_resp.status_code == 200
        assert delete_resp.json()["data"]["deleted"] is True

        list_after_delete = client.get("/api/sites", headers=headers)
        assert list_after_delete.status_code == 200
        assert list_after_delete.json()["data"]["total"] == 0


def test_create_site_validates_url_and_unique_constraint() -> None:
    _reset_sites_data()
    app = create_app()
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        invalid_url = client.post(
            "/api/sites",
            headers=headers,
            json={"name": "Bad", "url": "ftp://invalid.example.com"},
        )
        assert invalid_url.status_code == 422

        first = client.post(
            "/api/sites",
            headers=headers,
            json={"name": "Docs", "url": "https://docs.example.com"},
        )
        assert first.status_code == 200

        duplicate = client.post(
            "/api/sites",
            headers=headers,
            json={"name": "Docs2", "url": "https://docs.example.com"},
        )
        assert duplicate.status_code == 409


def test_delete_site_cascades_related_logs() -> None:
    _reset_sites_data()
    app = create_app()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = client.post(
            "/api/sites",
            headers=headers,
            json={"name": "Docs", "url": "https://docs.example.com"},
        )
        site_id = create_resp.json()["data"]["id"]

    with SessionLocal() as db:
        db.add(SiteStatusLog(site_id=site_id, status="online", response_time=120))
        db.add(VisitLog(site_id=site_id, ip="127.0.0.1", user_agent="pytest"))
        db.add(VisitStats(site_id=site_id, date=date.today(), click_count=5))
        db.commit()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        delete_resp = client.delete(f"/api/sites/{site_id}", headers=headers)
        assert delete_resp.status_code == 200

    with SessionLocal() as db:
        assert db.execute(select(Site).where(Site.id == site_id)).scalar_one_or_none() is None
        assert db.execute(select(SiteStatusLog).where(SiteStatusLog.site_id == site_id)).first() is None
        assert db.execute(select(VisitLog).where(VisitLog.site_id == site_id)).first() is None
        assert db.execute(select(VisitStats).where(VisitStats.site_id == site_id)).first() is None


def test_list_sites_supports_filters() -> None:
    _reset_sites_data()
    app = create_app()

    with SessionLocal() as db:
        db.add_all(
            [
                Site(
                    name="Docs",
                    url="https://docs.example.com",
                    tags="tools,docs",
                    description="Documentation",
                    is_public=True,
                    status="online",
                    sort_order=2,
                    last_check_time=datetime.now(timezone.utc),
                ),
                Site(
                    name="Blog",
                    url="https://blog.example.com",
                    tags="content",
                    description="Team blog",
                    is_public=False,
                    status="offline",
                    sort_order=1,
                ),
            ]
        )
        db.commit()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        by_tag = client.get("/api/sites?tag=tools", headers=headers)
        by_status = client.get("/api/sites?status=offline", headers=headers)
        by_public = client.get("/api/sites?is_public=true", headers=headers)
        by_q = client.get("/api/sites?q=blog", headers=headers)

    assert by_tag.status_code == 200
    assert by_tag.json()["data"]["total"] == 1
    assert by_tag.json()["data"]["items"][0]["name"] == "Docs"

    assert by_status.status_code == 200
    assert by_status.json()["data"]["total"] == 1
    assert by_status.json()["data"]["items"][0]["name"] == "Blog"

    assert by_public.status_code == 200
    assert by_public.json()["data"]["total"] == 1
    assert by_public.json()["data"]["items"][0]["name"] == "Docs"

    assert by_q.status_code == 200
    assert by_q.json()["data"]["total"] == 1
    assert by_q.json()["data"]["items"][0]["name"] == "Blog"


def test_batch_sort_update_persists_order() -> None:
    _reset_sites_data()
    app = create_app()

    with SessionLocal() as db:
        db.add_all(
            [
                Site(name="Alpha", url="https://alpha.example.com", sort_order=30, status="unknown"),
                Site(name="Beta", url="https://beta.example.com", sort_order=20, status="unknown"),
                Site(name="Gamma", url="https://gamma.example.com", sort_order=10, status="unknown"),
            ]
        )
        db.commit()
        sites = db.execute(select(Site).order_by(Site.id.asc())).scalars().all()
        alpha_id, beta_id, gamma_id = [item.id for item in sites]

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        sort_resp = client.put(
            "/api/sites/sort",
            headers=headers,
            json={
                "items": [
                    {"id": gamma_id, "sort_order": 5},
                    {"id": alpha_id, "sort_order": 15},
                    {"id": beta_id, "sort_order": 25},
                ]
            },
        )
        list_resp = client.get("/api/sites", headers=headers)

    assert sort_resp.status_code == 200
    assert sort_resp.json()["data"]["updated"] == 3
    assert list_resp.status_code == 200
    ordered_names = [item["name"] for item in list_resp.json()["data"]["items"]]
    assert ordered_names == ["Gamma", "Alpha", "Beta"]


def test_batch_sort_update_rejects_duplicate_ids() -> None:
    _reset_sites_data()
    app = create_app()

    with SessionLocal() as db:
        db.add(Site(name="Alpha", url="https://alpha.example.com", sort_order=10, status="unknown"))
        db.commit()
        site_id = db.execute(select(Site.id)).scalar_one()

    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        sort_resp = client.put(
            "/api/sites/sort",
            headers=headers,
            json={
                "items": [
                    {"id": site_id, "sort_order": 10},
                    {"id": site_id, "sort_order": 20},
                ]
            },
        )

    assert sort_resp.status_code == 400
