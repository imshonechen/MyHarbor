from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal
from ..models import Site, SiteConfig, SiteStatusLog, VisitLog, VisitStats
from .site_checker import check_all_sites

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_scheduler_lock = Lock()


def _get_config_int(db: Session, key: str, default: int) -> int:
    row = db.execute(select(SiteConfig).where(SiteConfig.key == key)).scalar_one_or_none()
    if row is None:
        return default
    try:
        return int(row.value)
    except (TypeError, ValueError):
        return default


def _resolve_check_interval_minutes() -> int:
    with SessionLocal() as db:
        interval = _get_config_int(db, "check_interval", 5)
    return max(1, min(1440, interval))


def run_site_check_job() -> dict[str, object]:
    settings = get_settings()
    with SessionLocal() as db:
        sites = db.execute(select(Site).order_by(Site.id.asc())).scalars().all()
        if not sites:
            return {"total": 0, "online": 0, "offline": 0}

        results = check_all_sites(db, sites, timeout_seconds=settings.check_timeout_seconds)
        db.commit()
        online = sum(1 for item in results if item.status == "online")
        offline = sum(1 for item in results if item.status == "offline")
        return {"total": len(results), "online": online, "offline": offline}


def aggregate_visit_logs_for_date(db: Session, target_date: date) -> int:
    date_text = target_date.isoformat()
    rows = db.execute(
        select(VisitLog.site_id, func.count(VisitLog.id))
        .where(func.date(VisitLog.visited_at) == date_text)
        .group_by(VisitLog.site_id)
    ).all()

    groups = 0
    for site_id, count in rows:
        stmt = select(VisitStats).where(VisitStats.date == target_date)
        if site_id is None:
            stmt = stmt.where(VisitStats.site_id.is_(None))
        else:
            stmt = stmt.where(VisitStats.site_id == site_id)

        record = db.execute(stmt).scalar_one_or_none()
        if record is None:
            db.add(VisitStats(site_id=site_id, date=target_date, click_count=int(count)))
        else:
            record.click_count = int(count)
        groups += 1
    return groups


def run_visit_aggregation_job(target_date: date | None = None) -> dict[str, object]:
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    with SessionLocal() as db:
        groups = aggregate_visit_logs_for_date(db, target_date)
        db.commit()
    return {"date": target_date.isoformat(), "groups": groups}


def run_cleanup_job(now: datetime | None = None) -> dict[str, int]:
    now_value = now or datetime.now(timezone.utc)
    status_cutoff = now_value - timedelta(days=30)
    visit_cutoff = now_value - timedelta(days=90)

    with SessionLocal() as db:
        status_deleted = db.execute(delete(SiteStatusLog).where(SiteStatusLog.checked_at < status_cutoff)).rowcount or 0
        visit_deleted = db.execute(delete(VisitLog).where(VisitLog.visited_at < visit_cutoff)).rowcount or 0
        db.commit()
    return {"site_status_log_deleted": int(status_deleted), "visit_log_deleted": int(visit_deleted)}


def _create_scheduler() -> BackgroundScheduler:
    check_interval = _resolve_check_interval_minutes()
    scheduler = BackgroundScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_site_check_job,
        trigger=IntervalTrigger(minutes=check_interval),
        id="site-check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_visit_aggregation_job,
        trigger=CronTrigger(hour=0, minute=5),
        id="visit-aggregation",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_cleanup_job,
        trigger=CronTrigger(hour=0, minute=30),
        id="log-cleanup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def start_scheduler() -> None:
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("Scheduler disabled by configuration.")
        return

    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            return
        _scheduler = _create_scheduler()
        _scheduler.start()
        logger.info("Scheduler started.")


def stop_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is None:
            return
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")

