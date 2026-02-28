from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..models import Site, VisitLog, VisitStats

RangeType = Literal["day", "month", "year", "total"]


def _range_start_date(range_type: RangeType, today: date) -> date | None:
    if range_type == "day":
        return today
    if range_type == "month":
        return today.replace(day=1)
    if range_type == "year":
        return today.replace(month=1, day=1)
    return None


def _today_window(today: date) -> tuple[datetime, datetime]:
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _sum_home_stats_before_today(db: Session, start_date: date | None, today: date) -> int:
    end_date = today - timedelta(days=1)
    if start_date is not None and start_date > end_date:
        return 0

    stmt = select(func.coalesce(func.sum(VisitStats.click_count), 0)).where(VisitStats.site_id.is_(None))
    if start_date is not None:
        stmt = stmt.where(VisitStats.date >= start_date)
    stmt = stmt.where(VisitStats.date <= end_date)
    return int(db.execute(stmt).scalar_one())


def _sum_site_stats_before_today(
    db: Session,
    start_date: date | None,
    today: date,
    site_id: int | None = None,
) -> int:
    end_date = today - timedelta(days=1)
    if start_date is not None and start_date > end_date:
        return 0

    stmt = select(func.coalesce(func.sum(VisitStats.click_count), 0))
    if site_id is None:
        stmt = stmt.where(VisitStats.site_id.is_not(None))
    else:
        stmt = stmt.where(VisitStats.site_id == site_id)
    if start_date is not None:
        stmt = stmt.where(VisitStats.date >= start_date)
    stmt = stmt.where(VisitStats.date <= end_date)
    return int(db.execute(stmt).scalar_one())


def _sum_today_home_logs(db: Session, today: date) -> int:
    today_start, tomorrow_start = _today_window(today)
    stmt = select(func.count(VisitLog.id)).where(
        VisitLog.site_id.is_(None),
        VisitLog.visited_at >= today_start,
        VisitLog.visited_at < tomorrow_start,
    )
    return int(db.execute(stmt).scalar_one())


def _sum_today_site_logs(db: Session, today: date) -> int:
    today_start, tomorrow_start = _today_window(today)
    stmt = select(func.count(VisitLog.id)).where(
        VisitLog.site_id.is_not(None),
        VisitLog.visited_at >= today_start,
        VisitLog.visited_at < tomorrow_start,
    )
    return int(db.execute(stmt).scalar_one())


def _group_site_stats_before_today(
    db: Session,
    start_date: date | None,
    today: date,
) -> dict[int, int]:
    end_date = today - timedelta(days=1)
    if start_date is not None and start_date > end_date:
        return {}

    stmt = (
        select(VisitStats.site_id, func.sum(VisitStats.click_count))
        .where(VisitStats.site_id.is_not(None))
        .group_by(VisitStats.site_id)
    )
    if start_date is not None:
        stmt = stmt.where(VisitStats.date >= start_date)
    stmt = stmt.where(VisitStats.date <= end_date)

    rows = db.execute(stmt).all()
    result: dict[int, int] = {}
    for site_id, click_count in rows:
        if site_id is None:
            continue
        result[int(site_id)] = int(click_count)
    return result


def _group_today_site_logs(db: Session, today: date) -> dict[int, int]:
    today_start, tomorrow_start = _today_window(today)
    stmt = (
        select(VisitLog.site_id, func.count(VisitLog.id))
        .where(
            VisitLog.site_id.is_not(None),
            VisitLog.visited_at >= today_start,
            VisitLog.visited_at < tomorrow_start,
        )
        .group_by(VisitLog.site_id)
    )
    rows = db.execute(stmt).all()
    result: dict[int, int] = {}
    for site_id, count in rows:
        if site_id is None:
            continue
        result[int(site_id)] = int(count)
    return result


def get_stats_overview(db: Session) -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    home: dict[str, int] = {}
    for key in ("day", "month", "year", "total"):
        start_date = _range_start_date(key, today)  # type: ignore[arg-type]
        value = _sum_home_stats_before_today(db, start_date, today) + _sum_today_home_logs(db, today)
        home[key] = value

    sites_total = _sum_site_stats_before_today(db, None, today) + _sum_today_site_logs(db, today)
    return {"home": home, "sites_total": sites_total}


def get_site_ranking(
    db: Session,
    range_type: RangeType = "day",
    limit: int = 20,
) -> list[dict[str, object]]:
    today = datetime.now(timezone.utc).date()
    start_date = _range_start_date(range_type, today)

    counts = defaultdict(int)
    for site_id, value in _group_site_stats_before_today(db, start_date, today).items():
        counts[site_id] += value
    for site_id, value in _group_today_site_logs(db, today).items():
        counts[site_id] += value

    if not counts:
        return []

    site_rows = db.execute(select(Site.id, Site.name).where(Site.id.in_(list(counts.keys())))).all()
    name_by_id = {int(site_id): name for site_id, name in site_rows}

    items = [
        {
            "site_id": site_id,
            "site_name": name_by_id.get(site_id, f"Site-{site_id}"),
            "click_count": int(click_count),
        }
        for site_id, click_count in counts.items()
    ]
    items.sort(key=lambda item: (-int(item["click_count"]), int(item["site_id"])))
    return items[:limit]


def get_stats_trend(db: Session, days: int = 30) -> list[dict[str, object]]:
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=max(1, days) - 1)

    series: dict[date, dict[str, object]] = {}
    current = start_date
    while current <= today:
        series[current] = {
            "date": current.isoformat(),
            "home_count": 0,
            "site_click_count": 0,
        }
        current += timedelta(days=1)

    stats_end_date = today - timedelta(days=1)
    if start_date <= stats_end_date:
        rows = (
            db.execute(
                select(VisitStats.date, VisitStats.site_id, func.sum(VisitStats.click_count))
                .where(VisitStats.date >= start_date, VisitStats.date <= stats_end_date)
                .group_by(VisitStats.date, VisitStats.site_id)
            )
            .all()
        )
        for stats_date, site_id, click_count in rows:
            bucket = series.get(stats_date)
            if bucket is None:
                continue
            if site_id is None:
                bucket["home_count"] = int(bucket["home_count"]) + int(click_count)
            else:
                bucket["site_click_count"] = int(bucket["site_click_count"]) + int(click_count)

    home_today = _sum_today_home_logs(db, today)
    site_today = _sum_today_site_logs(db, today)
    if today in series:
        series[today]["home_count"] = int(series[today]["home_count"]) + home_today
        series[today]["site_click_count"] = int(series[today]["site_click_count"]) + site_today

    return [series[key] for key in sorted(series.keys())]


def get_click_table(db: Session) -> list[dict[str, object]]:
    today = datetime.now(timezone.utc).date()
    today_start, tomorrow_start = _today_window(today)
    stats_end_date = today - timedelta(days=1)

    today_log_rows = (
        db.execute(
            select(VisitLog.site_id, func.count(VisitLog.id))
            .where(
                VisitLog.visited_at >= today_start,
                VisitLog.visited_at < tomorrow_start,
            )
            .group_by(VisitLog.site_id)
        )
        .all()
    )
    today_counts: dict[int | None, int] = {site_id: int(count) for site_id, count in today_log_rows}

    start_7d = today - timedelta(days=6)
    start_30d = today - timedelta(days=29)
    start_90d = today - timedelta(days=89)
    start_365d = today - timedelta(days=364)

    window_counts: dict[int | None, dict[str, int]] = {}
    if start_365d <= stats_end_date:
        d7_case = case((VisitStats.date >= start_7d, VisitStats.click_count), else_=0)
        d30_case = case((VisitStats.date >= start_30d, VisitStats.click_count), else_=0)
        d90_case = case((VisitStats.date >= start_90d, VisitStats.click_count), else_=0)
        stmt = (
            select(
                VisitStats.site_id,
                func.coalesce(func.sum(d7_case), 0),
                func.coalesce(func.sum(d30_case), 0),
                func.coalesce(func.sum(d90_case), 0),
                func.coalesce(func.sum(VisitStats.click_count), 0),
            )
            .where(VisitStats.date >= start_365d, VisitStats.date <= stats_end_date)
            .group_by(VisitStats.site_id)
        )
        for site_id, d7, d30, d90, d365 in db.execute(stmt).all():
            window_counts[site_id] = {
                "7d": int(d7),
                "30d": int(d30),
                "90d": int(d90),
                "365d": int(d365),
            }

    total_rows = (
        db.execute(
            select(VisitStats.site_id, func.coalesce(func.sum(VisitStats.click_count), 0))
            .where(VisitStats.date <= stats_end_date)
            .group_by(VisitStats.site_id)
        )
        .all()
    )
    totals_before_today: dict[int | None, int] = {site_id: int(total) for site_id, total in total_rows}

    site_rows = (
        db.execute(select(Site.id, Site.name, Site.url).order_by(Site.sort_order.asc(), Site.id.asc()))
        .all()
    )

    def _build_row(site_id: int | None, site_name: str, site_url: str) -> dict[str, object]:
        today_clicks = today_counts.get(site_id, 0)
        windows = window_counts.get(site_id, {"7d": 0, "30d": 0, "90d": 0, "365d": 0})
        total_clicks = totals_before_today.get(site_id, 0) + today_clicks
        return {
            "site_id": site_id,
            "site_name": site_name,
            "site_url": site_url,
            "clicks_today": today_clicks,
            "clicks_7d": int(windows["7d"]) + today_clicks,
            "clicks_30d": int(windows["30d"]) + today_clicks,
            "clicks_90d": int(windows["90d"]) + today_clicks,
            "clicks_365d": int(windows["365d"]) + today_clicks,
            "clicks_total": total_clicks,
        }

    items: list[dict[str, object]] = [_build_row(None, "Home", "/")]
    for site_id, site_name, site_url in site_rows:
        items.append(_build_row(int(site_id), site_name, site_url))
    return items
