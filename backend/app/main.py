from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import get_settings
from .database import SessionLocal, init_database
from .models import SiteConfig
from .routers.auth import router as auth_router
from .routers.backup import router as backup_router
from .routers.config import router as config_router
from .routers.health import router as health_router
from .routers.public import router as public_router
from .routers.sites import router as sites_router
from .routers.stats import router as stats_router
from .services.bootstrap import ensure_default_site_config
from .services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

ADMIN_ENTRY_COOKIE_NAME = "myharbor_admin_route_code"


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    init_database()
    with SessionLocal() as db:
        inserted, route_code = ensure_default_site_config(db)
    if inserted:
        host = "127.0.0.1" if settings.app_host == "0.0.0.0" else settings.app_host
        logger.warning(
            "Default admin config initialized. Backend URL: http://%s:%s/%s . "
            "Please change default admin password immediately.",
            host,
            settings.app_port,
            route_code,
        )
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(sites_router)
    app.include_router(public_router)
    app.include_router(stats_router)
    app.include_router(backup_router)

    static_dir = Path(__file__).parent.parent / "static"
    index_file = static_dir / "index.html"

    def _admin_not_found(clear_cookie: bool = False) -> Response:
        response = Response(status_code=404)
        if clear_cookie:
            response.delete_cookie(ADMIN_ENTRY_COOKIE_NAME, path="/admin")
        return response

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/{path:path}", include_in_schema=False)
    def admin_ui(request: Request, path: str = ""):
        if not index_file.exists():
            return _admin_not_found()

        cookie_code = request.cookies.get(ADMIN_ENTRY_COOKIE_NAME)
        if not cookie_code:
            return _admin_not_found()

        with SessionLocal() as db:
            stmt = select(SiteConfig).where(SiteConfig.key == "admin_route_code")
            config = db.execute(stmt).scalar_one_or_none()
            if not config or config.value != cookie_code:
                return _admin_not_found(clear_cookie=True)

        return FileResponse(index_file)

    @app.get("/{route_code}")
    async def admin_route_handler(route_code: str, request: Request):
        """处理后台管理路由码访问，重定向到登录页"""
        # 验证路由码格式（6-32位字母数字）
        if 6 <= len(route_code) <= 32 and route_code.isalnum():
            with SessionLocal() as db:
                stmt = select(SiteConfig).where(SiteConfig.key == "admin_route_code")
                config = db.execute(stmt).scalar_one_or_none()

                if config and config.value == route_code:
                    # 路由码正确，重定向到登录页
                    response = RedirectResponse(url="/admin/login", status_code=302)
                    response.set_cookie(
                        key=ADMIN_ENTRY_COOKIE_NAME,
                        value=route_code,
                        path="/admin",
                        httponly=True,
                        samesite="lax",
                    )
                    return response

        # 路由码不匹配或格式错误，返回 404
        # 这里不返回 index.html，避免泄露信息
        raise HTTPException(status_code=404, detail="Not Found")

    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
