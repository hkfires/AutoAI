# tests/test_health.py
"""Tests for health check endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestHealthEndpoint:
    """Health check endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_healthy(self, monkeypatch):
        """Test /health endpoint returns status healthy."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_health_endpoint_content_type(self, monkeypatch):
        """Test /health endpoint returns JSON content type."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_health_endpoint_method_not_allowed(self, monkeypatch):
        """Test /health endpoint rejects POST requests."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/health")

        assert response.status_code == 405
