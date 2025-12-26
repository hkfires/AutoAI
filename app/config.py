"""Application Configuration using pydantic-settings."""

import os
from pathlib import Path

from cryptography.fernet import Fernet
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

    # Encryption (optional, auto-generated if not set)
    encryption_key: str | None = Field(default=None, repr=False)

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


def ensure_encryption_key() -> str:
    """Ensure ENCRYPTION_KEY exists, auto-generate and write to .env if not.

    Uses file locking to prevent race conditions when multiple processes
    start simultaneously. Works on both Windows and Unix.

    Returns:
        The encryption key value.

    Raises:
        FileNotFoundError: If .env file does not exist and cannot be created safely.
    """
    import sys

    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return key

    env_path = Path(".env")

    # Check if .env exists - don't create from scratch as it needs ADMIN_PASSWORD
    if not env_path.exists():
        raise FileNotFoundError(
            "ENCRYPTION_KEY not set or .env file not found.\n"
            "For local development: Create .env from .env.example first.\n"
            "For Docker deployment: Set ENCRYPTION_KEY in .env or docker-compose.yml.\n"
            "Generate a key with: See README.md for details."
        )

    # Platform-specific file locking
    if sys.platform == "win32":
        import msvcrt

        with open(env_path, "r+", encoding="utf-8") as f:
            try:
                # Acquire exclusive lock (Windows)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

                # Re-check after acquiring lock
                f.seek(0)
                content = f.read()
                for line in content.splitlines():
                    if line.startswith("ENCRYPTION_KEY=") and line.split("=", 1)[1].strip():
                        key = line.split("=", 1)[1].strip()
                        os.environ["ENCRYPTION_KEY"] = key
                        return key

                # Generate new Fernet key
                key = Fernet.generate_key().decode()

                # Append to .env file
                f.seek(0, 2)  # Seek to end
                f.write(f"\n# Auto-generated encryption key\nENCRYPTION_KEY={key}\n")
                f.flush()

            finally:
                # Release lock (Windows)
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
    else:
        import fcntl

        with open(env_path, "r+", encoding="utf-8") as f:
            try:
                # Acquire exclusive lock (Unix)
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)

                # Re-check after acquiring lock
                f.seek(0)
                content = f.read()
                for line in content.splitlines():
                    if line.startswith("ENCRYPTION_KEY=") and line.split("=", 1)[1].strip():
                        key = line.split("=", 1)[1].strip()
                        os.environ["ENCRYPTION_KEY"] = key
                        return key

                # Generate new Fernet key
                key = Fernet.generate_key().decode()

                # Append to .env file
                f.seek(0, 2)  # Seek to end
                f.write(f"\n# Auto-generated encryption key\nENCRYPTION_KEY={key}\n")
                f.flush()

            finally:
                # Release lock (Unix)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    # Set environment variable for current process
    os.environ["ENCRYPTION_KEY"] = key

    # Reset settings singleton so it picks up the new key
    global _settings
    _settings = None

    return key
