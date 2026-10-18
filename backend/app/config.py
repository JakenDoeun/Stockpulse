from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "StockPulse API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"

    # SQLite for local development; set a postgresql+psycopg2:// URL (credentials via env only) in production.
    database_url: str = "sqlite:///./data/stockpulse.db"

    # Comma-separated browser origins allowed to call the API. Empty = same-origin only.
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _production_guards(self):
        if self.app_env == "production":
            if self.database_url.startswith("sqlite"):
                raise ValueError("APP_ENV=production requires DATABASE_URL to point at PostgreSQL, not SQLite.")
            if "*" in self.cors_origin_list:
                raise ValueError("APP_ENV=production does not allow CORS_ORIGINS=*; list the frontend origins.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
