from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import SessionLocal, init_database
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

    # 挂载静态文件（生产环境）
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        from fastapi import Request
        from fastapi.responses import FileResponse
        from sqlalchemy import select
        from .models import SiteConfig

        @app.get("/{route_code}")
        async def admin_route_handler(route_code: str, request: Request):
            """处理后台管理路由码访问，重定向到登录页"""
            # 验证路由码格式（6-32位字母数字）
            if len(route_code) >= 6 and len(route_code) <= 32 and route_code.isalnum():
                with SessionLocal() as db:
                    stmt = select(SiteConfig).where(SiteConfig.key == "admin_route_code")
                    config = db.execute(stmt).scalar_one_or_none()

                    if config and config.value == route_code:
                        # 路由码正确，重定向到登录页
                        from fastapi.responses import RedirectResponse
                        return RedirectResponse(url="/admin/login", status_code=302)

            # 路由码不匹配或格式错误，返回 404
            # 这里不返回 index.html，避免泄露信息
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
