from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    config_file = Path(__file__).resolve()

    # Repo layout: <repo_root>/backend/app/config.py
    # Docker layout: /app/app/config.py (backend/ copied into /app)
    if config_file.parents[1].name == "backend":
        project_root = config_file.parents[2]
    else:
        project_root = config_file.parents[1]

    db_path = project_root / "data" / "myharbor.db"
    return f"sqlite:///{db_path.as_posix()}"


class Settings(BaseSettings):
    app_name: str = "MyHarbor API"
    app_host: str = "0.0.0.0"
    app_port: int = 24041
    log_level: str = "INFO"
    database_url: str = _default_database_url()
    check_timeout_seconds: int = 5
    enable_scheduler: bool = True
    jwt_secret: str = "myharbor-dev-secret-change-me"
    jwt_expire_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
