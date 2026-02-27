from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_admin_username
from ..models import Site, SiteConfig

router = APIRouter(prefix="/api/backup", tags=["backup"])


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


def _serialize_site_for_export(site: Site) -> dict[str, object]:
    return {
        "name": site.name,
        "url": site.url,
        "logo": site.logo,
        "description": site.description,
        "tags": site.tags,
        "is_public": site.is_public,
        "sort_order": site.sort_order,
    }


def _get_public_config(db: Session) -> dict[str, str]:
    config_keys = ("site_title", "site_description", "copyright", "icp_number")
    rows = db.execute(select(SiteConfig).where(SiteConfig.key.in_(config_keys))).scalars().all()
    return {row.key: row.value for row in rows}


@router.get("/export")
def export_backup(
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> StreamingResponse:
    sites = db.execute(select(Site).order_by(Site.sort_order.asc(), Site.id.asc())).scalars().all()
    config = _get_public_config(db)

    backup_data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "sites": [_serialize_site_for_export(site) for site in sites],
        "config": config,
    }

    json_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
    buffer = BytesIO(json_bytes)

    filename = f"myharbor-backup-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(json_bytes)),
        },
    )


@router.post("/import")
def import_backup(
    file: UploadFile = File(...),
    strategy: str = Form(default="skip"),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    if strategy not in {"skip", "overwrite"}:
        raise HTTPException(status_code=400, detail="strategy must be 'skip' or 'overwrite'")

    try:
        content = file.file.read()
        backup_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"failed to read file: {str(e)}")

    if not isinstance(backup_data, dict):
        raise HTTPException(status_code=400, detail="backup data must be a JSON object")

    sites_data = backup_data.get("sites", [])
    if not isinstance(sites_data, list):
        raise HTTPException(status_code=400, detail="sites must be an array")

    total = len(sites_data)
    created = 0
    updated = 0
    skipped = 0

    try:
        for site_data in sites_data:
            if not isinstance(site_data, dict):
                continue

            url = site_data.get("url")
            if not url:
                continue

            existing = db.execute(select(Site).where(Site.url == url)).scalar_one_or_none()

            if existing is None:
                site = Site(
                    name=site_data.get("name", "")[:100],
                    url=url[:2048],
                    logo=site_data.get("logo")[:2048] if site_data.get("logo") else None,
                    description=site_data.get("description")[:500] if site_data.get("description") else None,
                    tags=site_data.get("tags"),
                    is_public=site_data.get("is_public", True),
                    sort_order=site_data.get("sort_order", 9999),
                    status="unknown",
                )
                db.add(site)
                created += 1
            elif strategy == "overwrite":
                existing.name = site_data.get("name", existing.name)[:100]
                existing.logo = site_data.get("logo")[:2048] if site_data.get("logo") else None
                existing.description = site_data.get("description")[:500] if site_data.get("description") else None
                existing.tags = site_data.get("tags")
                existing.is_public = site_data.get("is_public", existing.is_public)
                existing.sort_order = site_data.get("sort_order", existing.sort_order)
                updated += 1
            else:
                skipped += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"import failed: {str(e)}")

    return _ok(
        {
            "total": total,
            "created": created,
            "updated": updated,
            "skipped": skipped,
        }
    )
