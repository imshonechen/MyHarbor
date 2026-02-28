from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import Site, SiteConfig, SiteStatusLog, VisitLog, VisitStats
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config


def _reset_stats_data() -> None:
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


def _seed_visit_data() -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    forty_days_ago = today - timedelta(days=40)
    four_hundred_days_ago = today - timedelta(days=400)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        site_a = Site(name="Docs", url="https://docs.example.com", status="unknown")
        site_b = Site(name="Blog", url="https://blog.example.com", status="unknown")
        db.add_all([site_a, site_b])
        db.commit()
        db.refresh(site_a)
        db.refresh(site_b)

        db.add_all(
            [
                VisitStats(site_id=None, date=yesterday, click_count=5),
                VisitStats(site_id=None, date=forty_days_ago, click_count=7),
                VisitStats(site_id=site_a.id, date=yesterday, click_count=11),
                VisitStats(site_id=site_b.id, date=yesterday, click_count=4),
                VisitStats(site_id=site_a.id, date=forty_days_ago, click_count=10),
                VisitStats(site_id=site_b.id, date=four_hundred_days_ago, click_count=20),
                VisitLog(site_id=None, ip="127.0.0.1", user_agent="ua", visited_at=now),
                VisitLog(site_id=None, ip="127.0.0.2", user_agent="ua", visited_at=now),
                VisitLog(site_id=site_a.id, ip="127.0.0.1", user_agent="ua", visited_at=now),
                VisitLog(site_id=site_a.id, ip="127.0.0.2", user_agent="ua", visited_at=now),
                VisitLog(site_id=site_a.id, ip="127.0.0.3", user_agent="ua", visited_at=now),
                VisitLog(site_id=site_b.id, ip="127.0.0.4", user_agent="ua", visited_at=now),
            ]
        )
        db.commit()

    return {
        "today": today,
        "yesterday": yesterday,
        "forty_days_ago": forty_days_ago,
        "site_a_name": "Docs",
        "site_b_name": "Blog",
    }


def test_stats_endpoints_require_authentication() -> None:
    _reset_stats_data()
    app = create_app()
    with TestClient(app) as client:
        overview_resp = client.get("/api/stats/overview")
        table_resp = client.get("/api/stats/table")

    assert overview_resp.status_code == 401
    assert table_resp.status_code == 401


def test_stats_overview_returns_day_month_year_total() -> None:
    _reset_stats_data()
    seed = _seed_visit_data()
    today = seed["today"]
    yesterday = seed["yesterday"]
    forty_days_ago = seed["forty_days_ago"]

    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    expected_home_day = 2
    expected_home_month = (5 if yesterday >= month_start else 0) + (7 if forty_days_ago >= month_start else 0) + 2
    expected_home_year = (5 if yesterday >= year_start else 0) + (7 if forty_days_ago >= year_start else 0) + 2
    expected_home_total = 5 + 7 + 2
    expected_sites_total = 11 + 4 + 10 + 20 + 4

    app = create_app()
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/stats/overview", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["home"]["day"] == expected_home_day
    assert data["home"]["month"] == expected_home_month
    assert data["home"]["year"] == expected_home_year
    assert data["home"]["total"] == expected_home_total
    assert data["sites_total"] == expected_sites_total


def test_site_ranking_supports_range_and_limit() -> None:
    _reset_stats_data()
    seed = _seed_visit_data()

    app = create_app()
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        day_resp = client.get("/api/stats/sites", headers=headers, params={"range": "day"})
        top_total_resp = client.get("/api/stats/sites", headers=headers, params={"range": "total", "limit": 1})

    assert day_resp.status_code == 200
    day_items = day_resp.json()["data"]["items"]
    assert len(day_items) == 2
    assert day_items[0]["site_name"] == seed["site_a_name"]
    assert day_items[0]["click_count"] == 3
    assert day_items[1]["site_name"] == seed["site_b_name"]
    assert day_items[1]["click_count"] == 1

    assert top_total_resp.status_code == 200
    top_total_items = top_total_resp.json()["data"]["items"]
    assert len(top_total_items) == 1
    assert top_total_items[0]["site_name"] == seed["site_b_name"]
    assert top_total_items[0]["click_count"] == 25


def test_stats_trend_returns_continuous_series() -> None:
    _reset_stats_data()
    _seed_visit_data()

    app = create_app()
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/stats/trend", headers=headers, params={"days": 3})

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 3
    assert items[-1]["home_count"] == 2
    assert items[-1]["site_click_count"] == 4
    assert items[-2]["home_count"] == 5
    assert items[-2]["site_click_count"] == 15


def test_click_table_returns_home_first_then_sites_with_windows() -> None:
    _reset_stats_data()
    _seed_visit_data()

    app = create_app()
    with TestClient(app) as client:
        token = _login_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/stats/table", headers=headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 3

    home = items[0]
    assert home["site_id"] is None
    assert home["site_url"] == "/"
    assert home["clicks_today"] == 2
    assert home["clicks_7d"] == 7
    assert home["clicks_30d"] == 7
    assert home["clicks_90d"] == 14
    assert home["clicks_365d"] == 14
    assert home["clicks_total"] == 14

    site_a = items[1]
    assert site_a["site_name"] == "Docs"
    assert site_a["site_url"] == "https://docs.example.com"
    assert site_a["clicks_today"] == 3
    assert site_a["clicks_7d"] == 14
    assert site_a["clicks_30d"] == 14
    assert site_a["clicks_90d"] == 24
    assert site_a["clicks_365d"] == 24
    assert site_a["clicks_total"] == 24

    site_b = items[2]
    assert site_b["site_name"] == "Blog"
    assert site_b["site_url"] == "https://blog.example.com"
    assert site_b["clicks_today"] == 1
    assert site_b["clicks_7d"] == 5
    assert site_b["clicks_30d"] == 5
    assert site_b["clicks_90d"] == 5
    assert site_b["clicks_365d"] == 5
    assert site_b["clicks_total"] == 25
