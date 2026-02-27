from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

import httpx
from sqlalchemy.orm import Session

from ..models import Site, SiteStatusLog


@dataclass
class SiteCheckResult:
    site_id: int
    status: str
    response_time: int | None
    checked_at: datetime


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def check_site_url(url: str, timeout_seconds: int = 5) -> tuple[str, int | None]:
    """
    检测站点 URL 是否在线。

    判断逻辑：
    - 2xx/3xx: online（正常访问/重定向）
    - 4xx: online（服务器在线但拒绝访问，如 403/401/404）
    - 5xx: offline（服务器错误）
    - 异常/超时: offline（无法连接）
    """
    start_at = perf_counter()
    try:
        # 对于内网地址（如路由器），禁用SSL证书验证
        verify_ssl = not (url.startswith('https://192.168.') or
                         url.startswith('https://10.') or
                         url.startswith('https://172.'))

        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, verify=verify_ssl) as client:
            response = client.get(url)
        elapsed_ms = int((perf_counter() - start_at) * 1000)
        # 4xx 表示服务器在线但拒绝访问（如 Cloudflare 防护、需要登录等）
        # 只有 5xx 或连接异常才算 offline
        status = "online" if response.status_code < 500 else "offline"
        return status, elapsed_ms
    except Exception as e:
        # 记录异常信息以便调试
        import logging
        logging.warning(f"Failed to check {url}: {type(e).__name__}: {str(e)}")
        return "offline", None


def check_single_site(db: Session, site: Site, timeout_seconds: int = 5) -> SiteCheckResult:
    status, response_time = check_site_url(site.url, timeout_seconds=timeout_seconds)
    checked_at = utcnow()

    site.status = status
    site.last_check_time = checked_at
    db.add(
        SiteStatusLog(
            site_id=site.id,
            status=status,
            response_time=response_time,
            checked_at=checked_at,
        )
    )
    return SiteCheckResult(
        site_id=site.id,
        status=status,
        response_time=response_time,
        checked_at=checked_at,
    )


def check_all_sites(db: Session, sites: list[Site], timeout_seconds: int = 5) -> list[SiteCheckResult]:
    return [check_single_site(db, site, timeout_seconds=timeout_seconds) for site in sites]

