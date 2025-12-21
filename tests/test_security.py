"""Tests for security utility functions."""

import os
import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def setup_encryption_key(monkeypatch):
    """Set up a valid encryption key for tests."""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", test_key)
    monkeypatch.setenv("ADMIN_PASSWORD", "test123")
    # Reset fernet singleton
    import app.utils.security as security_module
    security_module._fernet = None
    yield
    security_module._fernet = None


def test_mask_api_key_long():
    """Test masking a long API key shows first 4 and last 4 chars."""
    from app.utils.security import mask_api_key

    result = mask_api_key("sk-1234567890abcdef")
    assert result == "sk-1...cdef"


def test_mask_api_key_exactly_9_chars():
    """Test masking key with exactly 9 characters."""
    from app.utils.security import mask_api_key

    result = mask_api_key("123456789")
    assert result == "1234...6789"


def test_mask_api_key_short():
    """Test masking a short API key returns ***."""
    from app.utils.security import mask_api_key

    assert mask_api_key("short") == "***"
    assert mask_api_key("12345678") == "***"  # Exactly 8 chars
    assert mask_api_key("") == "***"


def test_encrypt_decrypt_roundtrip():
    """Test that encrypt/decrypt roundtrip preserves original value."""
    from app.utils.security import encrypt_api_key, decrypt_api_key

    original = "sk-test-api-key-12345"
    encrypted = encrypt_api_key(original)
    decrypted = decrypt_api_key(encrypted)

    assert decrypted == original
    assert encrypted != original


def test_encrypted_value_is_different_each_time():
    """Test that encrypting same value produces different ciphertext."""
    from app.utils.security import encrypt_api_key

    original = "sk-test-api-key"
    encrypted1 = encrypt_api_key(original)
    encrypted2 = encrypt_api_key(original)

    # Fernet includes a timestamp, so encryptions should differ
    assert encrypted1 != encrypted2


def test_get_fernet_returns_same_instance():
    """Test that get_fernet returns a singleton instance."""
    from app.utils.security import get_fernet

    fernet1 = get_fernet()
    fernet2 = get_fernet()

    assert fernet1 is fernet2


def test_get_fernet_raises_without_key(monkeypatch):
    """Test that get_fernet raises ValueError when key not configured."""
    import app.utils.security as security_module
    import app.config as config_module

    # Reset singletons
    security_module._fernet = None
    config_module._settings = None

    # Remove encryption key
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError, match="ENCRYPTION_KEY not configured"):
        security_module.get_fernet()
