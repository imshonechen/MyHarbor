from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies.auth import get_current_admin_username
from ..models import Site, SiteStatusLog
from ..services.site_checker import SiteCheckResult, check_all_sites, check_single_site
from ..services.site_logo_service import fetch_site_logo_url

router = APIRouter(prefix="/api/sites", tags=["sites"])


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


def _is_valid_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalize_tags(tags: list[str] | None) -> str | None:
    if not tags:
        return None
    cleaned = [tag.strip() for tag in tags if tag and tag.strip()]
    return ",".join(cleaned) if cleaned else None


def _split_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    return [item.strip() for item in raw_tags.split(",") if item.strip()]


def _serialize_site(site: Site) -> dict[str, object]:
    return {
        "id": site.id,
        "name": site.name,
        "url": site.url,
        "logo": site.logo,
        "description": site.description,
        "tags": site.tags or "",
        "tags_list": _split_tags(site.tags),
        "is_public": site.is_public,
        "status": site.status,
        "sort_order": site.sort_order,
        "last_check_time": site.last_check_time.replace(tzinfo=timezone.utc).isoformat() if site.last_check_time else None,
        "created_at": site.created_at.replace(tzinfo=timezone.utc).isoformat(),
        "updated_at": site.updated_at.replace(tzinfo=timezone.utc).isoformat(),
    }


def _serialize_check_result(result: SiteCheckResult) -> dict[str, object]:
    return {
        "site_id": result.site_id,
        "status": result.status,
        "response_time": result.response_time,
        "checked_at": result.checked_at.replace(tzinfo=timezone.utc).isoformat() if result.checked_at.tzinfo is None else result.checked_at.isoformat(),
    }


class SiteCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=2048)
    logo: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    is_public: bool = True
    sort_order: int = 9999

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not _is_valid_http_url(value):
            raise ValueError("url must start with http:// or https://")
        return value


class SiteUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    logo: str | None = Field(default=None, max_length=2048)
    description: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    is_public: bool | None = None
    sort_order: int | None = None
    status: str | None = None
    last_check_time: datetime | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not _is_valid_http_url(value):
            raise ValueError("url must start with http:// or https://")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in {"online", "offline", "unknown"}:
            raise ValueError("invalid status")
        return value


class SiteSortItem(BaseModel):
    id: int
    sort_order: int


class SiteSortRequest(BaseModel):
    items: list[SiteSortItem] = Field(min_length=1)


def _ensure_unique_url(db: Session, url: str, excluding_id: int | None = None) -> None:
    stmt = select(Site).where(Site.url == url)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing is None:
        return
    if excluding_id is not None and existing.id == excluding_id:
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="site url already exists",
    )


@router.get("")
def list_sites(
    q: str | None = None,
    tag: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    is_public: bool | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    stmt = select(Site)
    count_stmt = select(func.count()).select_from(Site)
    filters = []

    if q:
        q = q.strip()
        if q:
            like_q = f"%{q}%"
            filters.append(or_(Site.name.ilike(like_q), Site.url.ilike(like_q), Site.description.ilike(like_q)))
    if tag:
        tag = tag.strip()
        if tag:
            filters.append(Site.tags.ilike(f"%{tag}%"))
    if status_filter:
        if status_filter not in {"online", "offline", "unknown"}:
            raise HTTPException(status_code=400, detail="invalid status filter")
        filters.append(Site.status == status_filter)
    if is_public is not None:
        filters.append(Site.is_public.is_(is_public))

    for condition in filters:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    stmt = stmt.order_by(Site.sort_order.asc(), Site.id.asc()).offset((page - 1) * size).limit(size)
    items = db.execute(stmt).scalars().all()
    total = db.execute(count_stmt).scalar_one()

    return _ok(
        {
            "items": [_serialize_site(site) for site in items],
            "total": total,
            "page": page,
            "size": size,
        }
    )


@router.post("")
def create_site(
    payload: SiteCreateRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    _ensure_unique_url(db, payload.url)
    site = Site(
        name=payload.name.strip(),
        url=payload.url,
        logo=payload.logo.strip() if payload.logo else None,
        description=payload.description.strip() if payload.description else None,
        tags=_normalize_tags(payload.tags),
        is_public=payload.is_public,
        sort_order=payload.sort_order,
        status="unknown",
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return _ok(_serialize_site(site))


@router.put("/sort")
def update_site_sort_orders(
    payload: SiteSortRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site_ids = [item.id for item in payload.items]
    if len(site_ids) != len(set(site_ids)):
        raise HTTPException(status_code=400, detail="duplicate site id in sort payload")

    stmt = select(Site).where(Site.id.in_(site_ids))
    sites = db.execute(stmt).scalars().all()
    if len(sites) != len(site_ids):
        existing_ids = {site.id for site in sites}
        missing_ids = [site_id for site_id in site_ids if site_id not in existing_ids]
        raise HTTPException(status_code=404, detail=f"site not found: {missing_ids[0]}")

    site_map = {site.id: site for site in sites}
    for item in payload.items:
        site_map[item.id].sort_order = item.sort_order

    db.commit()
    return _ok({"updated": len(payload.items)})


@router.get("/logo")
def fetch_logo_url(
    url: str = Query(min_length=1, max_length=2048),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    normalized = url.strip()
    if not _is_valid_http_url(normalized):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")

    settings = get_settings()
    logo_url = fetch_site_logo_url(normalized, timeout_seconds=settings.check_timeout_seconds)
    return _ok({"logo_url": logo_url})


@router.post("/check-all")
def check_all_site_status(
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    settings = get_settings()
    sites = db.execute(select(Site).order_by(Site.id.asc())).scalars().all()
    if not sites:
        return _ok({"total": 0, "online": 0, "offline": 0, "checked_at": None})

    results = check_all_sites(db, sites, timeout_seconds=settings.check_timeout_seconds)
    db.commit()

    online_count = sum(1 for item in results if item.status == "online")
    offline_count = sum(1 for item in results if item.status == "offline")
    max_checked_at = max(item.checked_at for item in results)
    checked_at = max_checked_at.replace(tzinfo=timezone.utc).isoformat() if max_checked_at.tzinfo is None else max_checked_at.isoformat()
    return _ok(
        {
            "total": len(results),
            "online": online_count,
            "offline": offline_count,
            "checked_at": checked_at,
        }
    )


@router.post("/{site_id}/check")
def check_single_site_status(
    site_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="site not found")

    settings = get_settings()
    result = check_single_site(db, site, timeout_seconds=settings.check_timeout_seconds)
    db.commit()
    return _ok(_serialize_check_result(result))


@router.get("/{site_id}/status-logs")
def list_site_status_logs(
    site_id: int,
    days: int = Query(default=30, ge=1, le=30),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="site not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logs = (
        db.execute(
            select(SiteStatusLog)
            .where(
                SiteStatusLog.site_id == site_id,
                SiteStatusLog.checked_at >= cutoff,
            )
            .order_by(SiteStatusLog.checked_at.desc())
        )
        .scalars()
        .all()
    )
    return _ok(
        {
            "site_id": site_id,
            "items": [
                {
                    "status": item.status,
                    "response_time": item.response_time,
                    "checked_at": item.checked_at.replace(tzinfo=timezone.utc).isoformat(),
                }
                for item in logs
            ],
        }
    )


@router.put("/{site_id}")
def update_site(
    site_id: int,
    payload: SiteUpdateRequest,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="site not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no fields to update")

    if "url" in updates and updates["url"] is not None:
        _ensure_unique_url(db, updates["url"], excluding_id=site.id)

    if "name" in updates and updates["name"] is not None:
        site.name = updates["name"].strip()
    if "url" in updates and updates["url"] is not None:
        site.url = updates["url"]
    if "logo" in updates:
        site.logo = updates["logo"].strip() if updates["logo"] else None
    if "description" in updates:
        site.description = updates["description"].strip() if updates["description"] else None
    if "tags" in updates:
        site.tags = _normalize_tags(updates["tags"])
    if "is_public" in updates and updates["is_public"] is not None:
        site.is_public = updates["is_public"]
    if "sort_order" in updates and updates["sort_order"] is not None:
        site.sort_order = updates["sort_order"]
    if "status" in updates and updates["status"] is not None:
        site.status = updates["status"]
    if "last_check_time" in updates:
        site.last_check_time = updates["last_check_time"]

    db.commit()
    db.refresh(site)
    return _ok(_serialize_site(site))


@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="site not found")

    db.delete(site)
    db.commit()
    return _ok({"deleted": True})


@router.patch("/{site_id}/toggle")
def toggle_site_public(
    site_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="site not found")

    site.is_public = not site.is_public
    db.commit()
    db.refresh(site)
    return _ok({"id": site.id, "is_public": site.is_public})
