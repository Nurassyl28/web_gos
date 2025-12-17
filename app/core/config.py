from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    project_name: str = Field("LMS Lite", env="PROJECT_NAME")
    database_url: str = Field("sqlite:///./lms.db", env="DATABASE_URL")
    secret_key: str = Field("change_this_in_prod", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    environment: str = Field("development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
