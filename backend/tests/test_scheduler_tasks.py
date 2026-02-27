from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.database import SessionLocal, init_database
from app.models import Site, SiteConfig, SiteStatusLog, VisitLog, VisitStats
from app.services.bootstrap import ensure_default_site_config
from app.services.scheduler import run_cleanup_job, run_visit_aggregation_job


def _reset_scheduler_test_data() -> None:
    init_database()
    with SessionLocal() as db:
        db.execute(delete(SiteStatusLog))
        db.execute(delete(VisitStats))
        db.execute(delete(VisitLog))
        db.execute(delete(Site))
        db.execute(delete(SiteConfig))
        db.commit()
        ensure_default_site_config(db)


def test_visit_aggregation_job_writes_daily_stats() -> None:
    _reset_scheduler_test_data()
    target_date = date(2026, 2, 16)
    target_dt = datetime(2026, 2, 16, 8, 0, tzinfo=timezone.utc)

    with SessionLocal() as db:
        site = Site(name="Docs", url="https://docs.example.com", status="unknown")
        db.add(site)
        db.commit()
        db.refresh(site)
        db.add_all(
            [
                VisitLog(site_id=None, ip="127.0.0.1", user_agent="ua", visited_at=target_dt),
                VisitLog(site_id=site.id, ip="127.0.0.1", user_agent="ua", visited_at=target_dt),
                VisitLog(site_id=site.id, ip="127.0.0.1", user_agent="ua", visited_at=target_dt + timedelta(hours=1)),
                VisitLog(
                    site_id=site.id,
                    ip="127.0.0.1",
                    user_agent="ua",
                    visited_at=target_dt + timedelta(days=1),
                ),
            ]
        )
        db.commit()

    result = run_visit_aggregation_job(target_date=target_date)
    assert result["date"] == "2026-02-16"
    assert result["groups"] == 2

    with SessionLocal() as db:
        rows = db.execute(select(VisitStats).where(VisitStats.date == target_date)).scalars().all()
        summary = {(row.site_id, row.date.isoformat()): row.click_count for row in rows}

    assert summary[(None, "2026-02-16")] == 1
    site_key = next(key for key in summary if key[0] is not None)
    assert summary[site_key] == 2


def test_cleanup_job_removes_expired_logs_only() -> None:
    _reset_scheduler_test_data()
    now = datetime(2026, 2, 16, 0, 0, tzinfo=timezone.utc)

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
                    response_time=10,
                    checked_at=now - timedelta(days=31),
                ),
                SiteStatusLog(
                    site_id=site.id,
                    status="offline",
                    response_time=20,
                    checked_at=now - timedelta(days=10),
                ),
                VisitLog(
                    site_id=site.id,
                    ip="127.0.0.1",
                    user_agent="ua",
                    visited_at=now - timedelta(days=91),
                ),
                VisitLog(
                    site_id=site.id,
                    ip="127.0.0.1",
                    user_agent="ua",
                    visited_at=now - timedelta(days=10),
                ),
            ]
        )
        db.commit()

    result = run_cleanup_job(now=now)
    assert result["site_status_log_deleted"] == 1
    assert result["visit_log_deleted"] == 1

    with SessionLocal() as db:
        status_count = db.execute(select(SiteStatusLog)).scalars().all()
        visit_count = db.execute(select(VisitLog)).scalars().all()

    assert len(status_count) == 1
    assert len(visit_count) == 1

