import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "GuardAI Enterprise"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./guardai.db"

    # Policy
    POLICY_FILE: str = "policy.json"

    # Cache & Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    SECRET_KEY: str = "guardai-enterprise-secret-key-change-in-production-32bytes!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    RATE_LIMIT_PER_MINUTE: int = 120

    # LLM Providers (pluggable API Keys)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    AWS_BEDROCK_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()