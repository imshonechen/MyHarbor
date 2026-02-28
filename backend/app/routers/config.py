from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_admin_username
from ..models import SiteConfig
from ..utils.html_sanitizer import sanitize_copyright_html
from ..utils.security import hash_password

router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_KEYS = (
    "site_title",
    "site_description",
    "copyright",
    "icp_number",
    "admin_username",
    "admin_route_code",
    "check_interval",
)

ROUTE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6,32}$")


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


def _get_config_map(db: Session) -> dict[str, str]:
    rows = db.execute(select(SiteConfig).where(SiteConfig.key.in_(CONFIG_KEYS + ("admin_password",)))).scalars().all()
    return {row.key: row.value for row in rows}


def _upsert_config_value(db: Session, key: str, value: str) -> None:
    row = db.execute(select(SiteConfig).where(SiteConfig.key == key)).scalar_one_or_none()
    if row is None:
        db.add(SiteConfig(key=key, value=value))
    else:
        row.value = value


class ConfigUpdateRequest(BaseModel):
    site_title: str | None = Field(default=None, min_length=1, max_length=120)
    site_description: str | None = Field(default=None, max_length=1000)
    copyright: str | None = Field(default=None, max_length=300)
    icp_number: str | None = Field(default=None, max_length=120)
    admin_username: str | None = Field(default=None, min_length=1, max_length=64)
    admin_password: str | None = Field(default=None, min_length=1, max_length=128)
    admin_route_code: str | None = Field(default=None, min_length=6, max_length=32)
    check_interval: int | None = Field(default=None, ge=1, le=1440)

    @field_validator("admin_route_code")
    @classmethod
    def validate_route_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        code = value.strip()
        if not ROUTE_CODE_PATTERN.fullmatch(code):
            raise ValueError("admin_route_code must be 6-32 alphanumeric characters")
        return code


@router.get("")
def get_system_config(
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    values = _get_config_map(db)
    data = {
        "site_title": values.get("site_title", "MyHarbor"),
        "site_description": values.get("site_description", ""),
        "copyright": sanitize_copyright_html(values.get("copyright", "")),
        "icp_number": values.get("icp_number", ""),
        "admin_username": values.get("admin_username", "admin"),
        "admin_route_code": values.get("admin_route_code", ""),
        "check_interval": int(values.get("check_interval", "5")),
    }
    return _ok(data)


@router.put("")
def update_system_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin_username),
) -> dict[str, object]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no fields to update")

    relogin_required = False
    new_route_code: str | None = None

    for key, value in updates.items():
        if key == "admin_password":
            _upsert_config_value(db, "admin_password", hash_password(value))
            relogin_required = True
            continue
        if key == "check_interval":
            _upsert_config_value(db, "check_interval", str(value))
            continue
        if key == "admin_username":
            username = value.strip()
            _upsert_config_value(db, "admin_username", username)
            if username != current_admin:
                relogin_required = True
            continue
        if key == "admin_route_code":
            code = value.strip()
            _upsert_config_value(db, "admin_route_code", code)
            new_route_code = code
            continue
        if key == "copyright":
            cleaned = sanitize_copyright_html(value or "")
            _upsert_config_value(db, "copyright", cleaned)
            continue
        _upsert_config_value(db, key, value)

    db.commit()
    return _ok(
        {
            "updated": True,
            "new_route_code": new_route_code,
            "relogin_required": relogin_required,
        }
    )
