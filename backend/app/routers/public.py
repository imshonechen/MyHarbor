from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Request

from ..database import get_db
from ..models import Site, SiteConfig, VisitLog
from ..schemas import ApiResponse, PublicConfigData, PublicSiteItem, PublicSitesData, VisitRecordData
from ..utils.html_sanitizer import sanitize_footer_html
from ..utils.visit_deduplicator import visit_deduplicator

router = APIRouter(prefix="/api", tags=["public"])

PUBLIC_CONFIG_KEYS = ("site_title", "site_description", "copyright", "icp_number")


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


@router.get("/config/public", response_model=ApiResponse)
def get_public_config(db: Session = Depends(get_db)) -> dict[str, object]:
    stmt = select(SiteConfig).where(SiteConfig.key.in_(PUBLIC_CONFIG_KEYS))
    rows = db.execute(stmt).scalars().all()
    values = {row.key: row.value for row in rows}

    config = PublicConfigData(
        site_title=values.get("site_title", "MyHarbor"),
        site_description=values.get("site_description", ""),
        copyright=sanitize_footer_html(values.get("copyright", "")),
        icp_number=sanitize_footer_html(values.get("icp_number", "")),
    )
    return _ok(config.model_dump())


@router.get("/sites/public", response_model=ApiResponse)
def get_public_sites(
    q: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    stmt = select(Site).where(Site.is_public.is_(True))

    if q:
        q = q.strip()
        if q:
            like_q = f"%{q}%"
            stmt = stmt.where(or_(Site.name.ilike(like_q), Site.description.ilike(like_q)))

    if tag:
        tag = tag.strip()
        if tag:
            stmt = stmt.where(Site.tags.ilike(f"%{tag}%"))

    stmt = stmt.order_by(Site.sort_order.asc(), Site.id.asc())
    sites = db.execute(stmt).scalars().all()

    items = [
        PublicSiteItem(
            id=site.id,
            name=site.name,
            url=site.url,
            logo=site.logo,
            description=site.description,
            tags=site.tags or "",
            tags_list=_parse_tags(site.tags),
            is_public=site.is_public,
            status=site.status,
            sort_order=site.sort_order,
            last_check_time=site.last_check_time,
        )
        for site in sites
    ]

    data = PublicSitesData(items=items, total=len(items))
    return _ok(data.model_dump())


@router.post("/visit", response_model=ApiResponse)
def record_home_visit(request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    ip = request.client.host if request.client else None

    # 检查是否应该记录（防刷流）
    if not visit_deduplicator.should_record(ip, "home"):
        return _ok(VisitRecordData(recorded=False).model_dump())

    user_agent = request.headers.get("user-agent")
    db.add(VisitLog(site_id=None, ip=ip, user_agent=user_agent))
    db.commit()
    return _ok(VisitRecordData(recorded=True).model_dump())


@router.post("/visit/{site_id}", response_model=ApiResponse)
def record_site_visit(site_id: int, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="site not found")

    ip = request.client.host if request.client else None

    # 检查是否应该记录（防刷流）
    if not visit_deduplicator.should_record(ip, f"site:{site_id}"):
        return _ok(VisitRecordData(recorded=False).model_dump())

    user_agent = request.headers.get("user-agent")
    db.add(VisitLog(site_id=site_id, ip=ip, user_agent=user_agent))
    db.commit()
    return _ok(VisitRecordData(recorded=True).model_dump())
