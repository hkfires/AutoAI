"""Application Configuration using pydantic-settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/autoai.db"

    # Logging
    log_level: str = "INFO"

    # Admin (required, hidden from repr/logs)
    admin_password: str = Field(..., repr=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log_level is one of the standard Python logging levels."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database_url has a valid SQLAlchemy-like format."""
        if not v or not v.strip():
            raise ValueError('database_url cannot be empty')
        # Basic format check: should contain :// for connection string
        if '://' not in v:
            raise ValueError('database_url must be a valid connection string (e.g., sqlite+aiosqlite:///./data/app.db)')
        return v

    @field_validator('admin_password')
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        """Validate admin_password is not empty."""
        if not v or not v.strip():
            raise ValueError('admin_password cannot be empty')
        return v


# Lazy-loaded settings singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the settings singleton, creating it on first access.

    This lazy-loading pattern allows tests to configure environment
    before settings are instantiated.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
