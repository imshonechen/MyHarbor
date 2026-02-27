from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

PBKDF2_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 120_000
JWT_ALGORITHM = "HS256"


class TokenError(Exception):
    """Base token validation error."""


class TokenExpiredError(TokenError):
    """Token has expired."""


class TokenInvalidError(TokenError):
    """Token is invalid."""


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"{PBKDF2_PREFIX}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        prefix, salt, expected_digest = password_hash.split("$", 2)
    except ValueError:
        return False

    if prefix != PBKDF2_PREFIX:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(
    subject: str,
    secret_key: str,
    expire_hours: int = 24,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    expire_at = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=expire_hours))
    payload = {"sub": subject, "exp": expire_at}
    token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    return token, expire_at


def decode_access_token(token: str, secret_key: str) -> str:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidError("invalid token") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenInvalidError("invalid subject")
    return subject
