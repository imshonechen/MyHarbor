"""
测试备份导出和导入功能
"""
import io
import json

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal, init_database
from app.main import create_app
from app.models import Site, SiteConfig
from app.routers.auth import login_rate_limiter
from app.services.bootstrap import ensure_default_site_config


def _reset_admin_config() -> None:
    init_database()
    login_rate_limiter.clear()
    with SessionLocal() as db:
        db.execute(delete(SiteConfig))
        db.execute(delete(Site))
        db.commit()
        ensure_default_site_config(db)


def _get_auth_token(client: TestClient) -> str:
    """获取认证 token"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return response.json()["data"]["token"]


def test_backup_endpoints_require_authentication() -> None:
    """备份接口需要认证"""
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        # 导出备份
        response = client.get("/api/backup/export")
        assert response.status_code == 401

        # 导入备份
        response = client.post("/api/backup/import")
        assert response.status_code == 401


def test_export_backup_returns_json_file() -> None:
    """导出备份返回 JSON 文件"""
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        token = _get_auth_token(client)
        response = client.get(
            "/api/backup/export",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")

        # 验证 JSON 格式
        backup_data = response.json()
        assert "version" in backup_data
        assert "exported_at" in backup_data
        assert "sites" in backup_data
        assert "config" in backup_data
        assert isinstance(backup_data["sites"], list)
        assert isinstance(backup_data["config"], dict)


def test_import_backup_with_skip_strategy() -> None:
    """导入备份（skip 策略）跳过已存在的站点"""
    _reset_admin_config()
    app = create_app()

    # 创建一个已存在的站点
    with SessionLocal() as db:
        existing_site = Site(
            name="Existing Site",
            url="https://existing.com",
            is_public=True,
            sort_order=1,
            status="unknown"
        )
        db.add(existing_site)
        db.commit()

    # 准备备份数据
    backup_data = {
        "version": "1.0",
        "exported_at": "2026-02-19T10:00:00Z",
        "sites": [
            {
                "name": "Existing Site",
                "url": "https://existing.com",
                "logo": None,
                "description": "Should be skipped",
                "tags": "test",
                "is_public": True,
                "sort_order": 1
            },
            {
                "name": "New Site",
                "url": "https://newsite.com",
                "logo": None,
                "description": "Should be created",
                "tags": "new",
                "is_public": True,
                "sort_order": 2
            }
        ],
        "config": {}
    }

    with TestClient(app) as client:
        token = _get_auth_token(client)
        file_content = json.dumps(backup_data).encode("utf-8")
        files = {"file": ("backup.json", io.BytesIO(file_content), "application/json")}
        data = {"strategy": "skip"}

        response = client.post(
            "/api/backup/import",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["total"] == 2
        assert result["data"]["created"] == 1
        assert result["data"]["skipped"] == 1
        assert result["data"]["updated"] == 0


def test_import_backup_with_overwrite_strategy() -> None:
    """导入备份（overwrite 策略）覆盖已存在的站点"""
    _reset_admin_config()
    app = create_app()

    # 创建一个已存在的站点
    with SessionLocal() as db:
        existing_site = Site(
            name="Old Name",
            url="https://existing.com",
            description="Old description",
            is_public=True,
            sort_order=1,
            status="unknown"
        )
        db.add(existing_site)
        db.commit()

    # 准备备份数据
    backup_data = {
        "version": "1.0",
        "exported_at": "2026-02-19T10:00:00Z",
        "sites": [
            {
                "name": "Updated Name",
                "url": "https://existing.com",
                "logo": None,
                "description": "Updated description",
                "tags": "updated",
                "is_public": False,
                "sort_order": 10
            }
        ],
        "config": {}
    }

    with TestClient(app) as client:
        token = _get_auth_token(client)
        file_content = json.dumps(backup_data).encode("utf-8")
        files = {"file": ("backup.json", io.BytesIO(file_content), "application/json")}
        data = {"strategy": "overwrite"}

        response = client.post(
            "/api/backup/import",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["total"] == 1
        assert result["data"]["created"] == 0
        assert result["data"]["updated"] == 1
        assert result["data"]["skipped"] == 0

    # 验证站点已更新
    with SessionLocal() as db:
        updated_site = db.query(Site).filter_by(url="https://existing.com").first()
        assert updated_site.name == "Updated Name"
        assert updated_site.description == "Updated description"
        assert updated_site.is_public is False


def test_import_backup_rejects_invalid_json() -> None:
    """导入备份拒绝无效的 JSON"""
    _reset_admin_config()
    app = create_app()

    with TestClient(app) as client:
        token = _get_auth_token(client)
        files = {"file": ("backup.json", io.BytesIO(b"invalid json"), "application/json")}
        data = {"strategy": "skip"}

        response = client.post(
            "/api/backup/import",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 400
        assert "invalid JSON" in response.json()["detail"]


def test_import_backup_rejects_invalid_strategy() -> None:
    """导入备份拒绝无效的策略"""
    _reset_admin_config()
    app = create_app()

    backup_data = {"version": "1.0", "sites": [], "config": {}}
    file_content = json.dumps(backup_data).encode("utf-8")

    with TestClient(app) as client:
        token = _get_auth_token(client)
        files = {"file": ("backup.json", io.BytesIO(file_content), "application/json")}
        data = {"strategy": "invalid"}

        response = client.post(
            "/api/backup/import",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 400
        assert "strategy must be" in response.json()["detail"]
