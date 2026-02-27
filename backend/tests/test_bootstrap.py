from sqlalchemy import delete, select

from app.database import SessionLocal, init_database
from app.models import SiteConfig
from app.services.bootstrap import DEFAULT_CONFIG_VALUES, ensure_default_site_config


def _read_all_configs() -> dict[str, str]:
    with SessionLocal() as db:
        rows = db.execute(select(SiteConfig)).scalars().all()
        return {row.key: row.value for row in rows}


def test_default_site_config_is_created_when_table_is_empty() -> None:
    init_database()

    with SessionLocal() as db:
        db.execute(delete(SiteConfig))
        db.commit()
        inserted, route_code = ensure_default_site_config(db)

    assert inserted is True
    assert len(route_code) == 8
    assert route_code.isalnum()

    config = _read_all_configs()
    expected_keys = set(DEFAULT_CONFIG_VALUES.keys()) | {"admin_password", "admin_route_code"}
    assert set(config.keys()) == expected_keys
    assert config["admin_route_code"] == route_code
    assert config["admin_password"] != "admin123"
    assert config["admin_password"].startswith("pbkdf2_sha256$")
    assert config["check_interval"] == "5"


def test_default_site_config_initialization_is_idempotent() -> None:
    init_database()

    with SessionLocal() as db:
        db.execute(delete(SiteConfig))
        db.commit()
        inserted_first, route_first = ensure_default_site_config(db)
        inserted_second, route_second = ensure_default_site_config(db)

    assert inserted_first is True
    assert inserted_second is False
    assert route_first == route_second
    assert len(_read_all_configs()) == len(DEFAULT_CONFIG_VALUES) + 2

