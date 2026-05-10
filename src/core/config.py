import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    project_name: str = "Task Manager"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    timezone: str = "Europe/Kiev"

    database_url: str = "postgresql+asyncpg://task_manager:task_manager@localhost:5432/task_manager"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    bot_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return ["*"]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                loaded = json.loads(stripped)
                if not isinstance(loaded, list):
                    msg = "CORS_ORIGINS JSON value must be a list"
                    raise ValueError(msg)
                return [str(item) for item in loaded]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(item) for item in value]
        msg = "CORS_ORIGINS must be a list, JSON list, or comma separated string"
        raise ValueError(msg)

    @property
    def bot_enabled(self) -> bool:
        return bool(self.bot_token and ":" in self.bot_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
