from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MyHarbor API"
    app_host: str = "0.0.0.0"
    app_port: int = 24041
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/myharbor.db"
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
