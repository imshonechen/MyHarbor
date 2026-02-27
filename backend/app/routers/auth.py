from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies.auth import get_current_admin_username
from ..models import SiteConfig
from ..utils.rate_limiter import LoginRateLimiter
from ..utils.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
login_rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=60, lock_seconds=15 * 60)


class LoginRequest(BaseModel):
    username: str
    password: str


def _ok(data: object, message: str = "ok") -> dict[str, object]:
    return {"code": 0, "message": message, "data": data}


def _resolve_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _get_config_value(db: Session, key: str) -> str | None:
    stmt = select(SiteConfig).where(SiteConfig.key == key)
    row = db.execute(stmt).scalar_one_or_none()
    return row.value if row else None


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    client_ip = _resolve_client_ip(request)
    allowed, retry_after = login_rate_limiter.check_and_record(client_ip)
    if not allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )

    admin_username = _get_config_value(db, "admin_username")
    admin_password_hash = _get_config_value(db, "admin_password")
    if not admin_username or not admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin credentials not initialized",
        )

    is_username_valid = payload.username == admin_username
    is_password_valid = verify_password(payload.password, admin_password_hash)
    if not (is_username_valid and is_password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    login_rate_limiter.reset_client(client_ip)

    settings = get_settings()
    token, expires_at = create_access_token(
        subject=admin_username,
        secret_key=settings.jwt_secret,
        expire_hours=settings.jwt_expire_hours,
    )
    return _ok(
        {
            "token": token,
            "expires_at": expires_at.isoformat(),
            "username": admin_username,
        }
    )


@router.get("/me")
def me(current_admin: str = Depends(get_current_admin_username)) -> dict[str, object]:
    return _ok({"username": current_admin})
