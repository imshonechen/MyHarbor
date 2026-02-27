from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_admin_username
from ..schemas import ApiResponse
from ..services.stats_service import get_site_ranking, get_stats_overview, get_stats_trend

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


@router.get("/overview", response_model=ApiResponse)
def get_overview(
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    return _ok(get_stats_overview(db))


@router.get("/sites", response_model=ApiResponse)
def get_sites_stats(
    range_type: Literal["day", "month", "year", "total"] = Query(default="day", alias="range"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    return _ok({"items": get_site_ranking(db, range_type=range_type, limit=limit)})


@router.get("/trend", response_model=ApiResponse)
def get_trend(
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    return _ok({"items": get_stats_trend(db, days=days)})
