from __future__ import annotations

from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    project_name: str = Field("LMS Lite", env="PROJECT_NAME")
    database_url: str = Field("sqlite:///./lms.db", env="DATABASE_URL")
    secret_key: str = Field("change_this_in_prod", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(60 * 24 * 7, env="REFRESH_TOKEN_EXPIRE_MINUTES")
    environment: str = Field("development", env="ENVIRONMENT")
    cors_origins: List[str] = Field(default_factory=list, env="CORS_ORIGINS")
    require_https: bool = Field(False, env="REQUIRE_HTTPS")
    rate_limit_requests: int = Field(120, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, env="RATE_LIMIT_WINDOW_SECONDS")
    login_attempts_limit: int = Field(5, env="LOGIN_ATTEMPTS_LIMIT")
    login_attempts_window_seconds: int = Field(300, env="LOGIN_ATTEMPTS_WINDOW_SECONDS")
    max_request_size: int = Field(1048576, env="MAX_REQUEST_SIZE")

    @validator("cors_origins", pre=True)
    def split_cors(cls, value: str | List[str] | None):
        if value is None:
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
