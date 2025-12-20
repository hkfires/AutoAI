# tests/test_config.py
"""Tests for application configuration."""

import pytest
from pydantic import ValidationError


class TestSettings:
    """Settings configuration tests."""

    def test_valid_config(self, monkeypatch):
        """Test Settings with valid configuration."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        from app.config import Settings
        s = Settings(_env_file=None)
        assert s.database_url == "sqlite+aiosqlite:///./data/autoai.db"
        assert s.log_level == "INFO"
        assert s.admin_password == "test123"

    def test_missing_admin_password(self, monkeypatch):
        """Test ValidationError when ADMIN_PASSWORD is missing."""
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "admin_password" in str(exc_info.value)

    def test_custom_values(self, monkeypatch):
        """Test environment variables override defaults."""
        monkeypatch.setenv("ADMIN_PASSWORD", "secret")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./custom.db")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        from app.config import Settings
        s = Settings(_env_file=None)
        assert s.database_url == "sqlite+aiosqlite:///./custom.db"
        assert s.log_level == "DEBUG"

    def test_invalid_log_level(self, monkeypatch):
        """Test ValidationError for invalid LOG_LEVEL."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "log_level" in str(exc_info.value)

    def test_empty_admin_password(self, monkeypatch):
        """Test ValidationError when ADMIN_PASSWORD is empty string."""
        monkeypatch.setenv("ADMIN_PASSWORD", "")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "admin_password" in str(exc_info.value)

    def test_whitespace_admin_password(self, monkeypatch):
        """Test ValidationError when ADMIN_PASSWORD is only whitespace."""
        monkeypatch.setenv("ADMIN_PASSWORD", "   ")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "admin_password" in str(exc_info.value)

    def test_admin_password_hidden_from_repr(self, monkeypatch):
        """Test admin_password is not visible in repr output."""
        monkeypatch.setenv("ADMIN_PASSWORD", "supersecret")
        from app.config import Settings
        s = Settings(_env_file=None)
        repr_str = repr(s)
        assert "supersecret" not in repr_str

    def test_log_level_case_insensitive(self, monkeypatch):
        """Test log_level accepts lowercase and converts to uppercase."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        monkeypatch.setenv("LOG_LEVEL", "debug")
        from app.config import Settings
        s = Settings(_env_file=None)
        assert s.log_level == "DEBUG"

    def test_no_openai_config_attributes(self, monkeypatch):
        """Test that OpenAI config attributes are removed."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        from app.config import Settings
        s = Settings(_env_file=None)
        assert not hasattr(s, 'openai_api_key')
        assert not hasattr(s, 'openai_base_url')

    def test_invalid_database_url_format(self, monkeypatch):
        """Test ValidationError for invalid DATABASE_URL format."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        monkeypatch.setenv("DATABASE_URL", "invalid-url-no-protocol")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "database_url" in str(exc_info.value)

    def test_empty_database_url(self, monkeypatch):
        """Test ValidationError when DATABASE_URL is empty."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        monkeypatch.setenv("DATABASE_URL", "")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)
        assert "database_url" in str(exc_info.value)

    def test_get_settings_returns_singleton(self, monkeypatch):
        """Test get_settings() returns the same instance on repeated calls."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        from app.config import get_settings
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
