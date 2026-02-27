from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import SiteConfig
from ..utils.security import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _get_config_value(db: Session, key: str) -> str | None:
    stmt = select(SiteConfig).where(SiteConfig.key == key)
    row = db.execute(stmt).scalar_one_or_none()
    return row.value if row else None


def get_current_admin_username(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    settings = get_settings()
    try:
        subject = decode_access_token(credentials.credentials, settings.jwt_secret)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
        ) from None

    admin_username = _get_config_value(db, "admin_username")
    if not admin_username or subject != admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token subject",
        )

    return subject

