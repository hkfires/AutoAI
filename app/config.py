"""Application Configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/autoai.db"

    # Logging
    log_level: str = "INFO"

    # Admin (required - no default value)
    admin_password: str

    # OpenAI (will be configured in later stories)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
