# tests/conftest.py
"""Pytest fixtures for the test suite."""

import sys
import pytest
from typing import Iterator

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


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
