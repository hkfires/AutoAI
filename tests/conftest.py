# tests/conftest.py
"""Pytest fixtures for the test suite."""

import os
import sys
import pytest
from typing import Iterator

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Test encryption key - set BEFORE any app modules are imported
TEST_ENCRYPTION_KEY = "NtlS-P5C7yXWWGEIsw5aX1p50X1_lrbGnVEMZNPt1Gw="


@pytest.fixture(autouse=True, scope="session")
def setup_test_encryption_key():
    """Set up encryption key for all tests at session start."""
    os.environ["ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY
    yield
    # Cleanup not strictly necessary but good practice
    if "ENCRYPTION_KEY" in os.environ:
        del os.environ["ENCRYPTION_KEY"]


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset the settings singleton before and after each test.

    This ensures each test gets a fresh Settings instance.
    """
    # Reset before test
    if 'app.config' in sys.modules:
        import app.config
        app.config._settings = None

    yield

    # Reset after test
    if 'app.config' in sys.modules:
        import app.config
        app.config._settings = None
