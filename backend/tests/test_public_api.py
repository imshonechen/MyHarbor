from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.main import create_app
from app.database import SessionLocal, init_database
from app.models import Site, SiteConfig, VisitLog
from app.services.bootstrap import ensure_default_site_config


def _reset_public_test_data() -> None:
    init_database()
    with SessionLocal() as db:
        db.execute(delete(VisitLog))
        db.execute(delete(Site))
        db.execute(delete(SiteConfig))
        db.commit()


def test_get_public_config_returns_initialized_defaults() -> None:
    _reset_public_test_data()
    with SessionLocal() as db:
        ensure_default_site_config(db)

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/config/public")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert body["data"]["site_title"] == "MyHarbor"
    assert "site_description" in body["data"]
    assert "copyright" in body["data"]
    assert "icp_number" in body["data"]


def test_get_public_sites_only_returns_public_and_supports_filters() -> None:
    _reset_public_test_data()
    with SessionLocal() as db:
        db.add_all(
            [
                Site(
                    name="Docs",
                    url="https://docs.example.com",
                    description="Public docs",
                    tags="tools,docs",
                    is_public=True,
                    status="online",
                    sort_order=2,
                    last_check_time=datetime.now(timezone.utc),
                ),
                Site(
                    name="Blog",
                    url="https://blog.example.com",
                    description="Public blog",
                    tags="blog",
                    is_public=True,
                    status="offline",
                    sort_order=1,
                ),
                Site(
                    name="Internal",
                    url="https://internal.example.com",
                    description="Private service",
                    tags="tools",
                    is_public=False,
                    status="unknown",
                    sort_order=0,
                ),
            ]
        )
        db.commit()

    app = create_app()
    with TestClient(app) as client:
        all_resp = client.get("/api/sites/public")
        tag_resp = client.get("/api/sites/public", params={"tag": "tools"})
        query_resp = client.get("/api/sites/public", params={"q": "blog"})

    assert all_resp.status_code == 200
    all_items = all_resp.json()["data"]["items"]
    assert len(all_items) == 2
    assert [item["name"] for item in all_items] == ["Blog", "Docs"]
    assert all(item["is_public"] is True for item in all_items)
    assert all_items[1]["tags_list"] == ["tools", "docs"]

    assert tag_resp.status_code == 200
    tag_items = tag_resp.json()["data"]["items"]
    assert len(tag_items) == 1
    assert tag_items[0]["name"] == "Docs"

    assert query_resp.status_code == 200
    query_items = query_resp.json()["data"]["items"]
    assert len(query_items) == 1
    assert query_items[0]["name"] == "Blog"


def test_record_visit_endpoints_write_visit_logs() -> None:
    _reset_public_test_data()
    with SessionLocal() as db:
        site = Site(
            name="Docs",
            url="https://docs.example.com",
            description="Public docs",
            tags="tools,docs",
            is_public=True,
            status="online",
            sort_order=1,
        )
        db.add(site)
        db.commit()
        db.refresh(site)
        site_id = site.id

    app = create_app()
    with TestClient(app) as client:
        home_resp = client.post("/api/visit")
        site_resp = client.post(f"/api/visit/{site_id}")
        not_found_resp = client.post("/api/visit/999999")

    assert home_resp.status_code == 200
    assert home_resp.json()["data"]["recorded"] is True
    assert site_resp.status_code == 200
    assert site_resp.json()["data"]["recorded"] is True
    assert not_found_resp.status_code == 404

    with SessionLocal() as db:
        logs = db.execute(select(VisitLog).order_by(VisitLog.id.asc())).scalars().all()

    assert len(logs) == 2
    assert logs[0].site_id is None
    assert logs[1].site_id == site_id

