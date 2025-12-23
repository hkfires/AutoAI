"""Security Utility Functions.

Provides encryption/decryption for sensitive data storage
and masking for safe display in logs and responses.
"""

import secrets

from cryptography.fernet import Fernet

from app.config import get_settings

# Lazy-loaded Fernet instance
_fernet: Fernet | None = None


def mask_api_key(key: str) -> str:
    """Mask API key for safe display in logs and responses.

    Args:
        key: The API key to mask.

    Returns:
        Masked key showing first 4 and last 4 characters,
        or '***' if key is too short.
    """
    if len(key) > 8:
        return f"{key[:4]}...{key[-4:]}"
    return "***"


def get_fernet() -> Fernet:
    """Get Fernet encryptor instance (lazy-loaded singleton).

    Returns:
        Configured Fernet instance.

    Raises:
        ValueError: If ENCRYPTION_KEY is not configured.
    """
    global _fernet
    if _fernet is None:
        settings = get_settings()
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY not configured")
        _fernet = Fernet(settings.encryption_key.encode())
    return _fernet


def encrypt_api_key(plain_text: str) -> str:
    """Encrypt API key for database storage.

    Args:
        plain_text: The plain text API key.

    Returns:
        Encrypted string (base64-encoded).
    """
    return get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_api_key(encrypted_text: str) -> str:
    """Decrypt API key from database storage.

    Args:
        encrypted_text: The encrypted API key.

    Returns:
        Decrypted plain text API key.
    """
    return get_fernet().decrypt(encrypted_text.encode()).decode()


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify password matches using timing-safe comparison.

    Uses secrets.compare_digest to prevent timing attacks.

    Args:
        plain_password: User-provided password to verify.
        stored_password: Password from environment variable.

    Returns:
        True if passwords match, False otherwise.
    """
    return secrets.compare_digest(plain_password, stored_password)
