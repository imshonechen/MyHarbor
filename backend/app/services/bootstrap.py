from __future__ import annotations

import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import SiteConfig
from ..utils.security import hash_password

DEFAULT_CONFIG_VALUES: dict[str, str] = {
    "site_title": "MyHarbor",
    "site_description": "欢迎来到 MyHarbor",
    "copyright": "&copy; 2026 MyHarbor",
    "icp_number": "",
    "admin_username": "admin",
    "check_interval": "5",
}


def generate_route_code(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_config_value(db: Session, key: str) -> str | None:
    stmt = select(SiteConfig).where(SiteConfig.key == key)
    row = db.execute(stmt).scalar_one_or_none()
    return row.value if row else None


def ensure_default_site_config(db: Session) -> tuple[bool, str]:
    existing = db.execute(select(SiteConfig.id).limit(1)).first()
    if existing is not None:
        route_code = _get_config_value(db, "admin_route_code") or ""
        return False, route_code

    route_code = generate_route_code()
    defaults = {
        **DEFAULT_CONFIG_VALUES,
        "admin_password": hash_password("admin123"),
        "admin_route_code": route_code,
    }

    for key, value in defaults.items():
        db.add(SiteConfig(key=key, value=value))
    db.commit()

    return True, route_code

