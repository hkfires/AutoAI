# tests/test_api_protection.py
"""Tests for API route protection (Story 3.2).

Verifies that all API endpoints require authentication and return
proper 401 responses when not authenticated.
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test encryption key - set BEFORE any app modules are imported
TEST_ENCRYPTION_KEY = "NtlS-P5C7yXWWGEIsw5aX1p50X1_lrbGnVEMZNPt1Gw="
TEST_ADMIN_PASSWORD = "test123"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
    monkeypatch.setenv("ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
    # Reset singletons
    import app.config as config_module
    config_module._settings = None
    yield
    config_module._settings = None


@pytest.fixture
def app():
    """Create test application instance."""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest_asyncio.fixture
async def unauthenticated_client(app):
    """Create async test client without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(app):
    """Create async test client with valid authentication."""
    from app.web.auth import create_session_token

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = create_session_token()
        ac.cookies.set("session", token)
        yield ac
        ac.cookies.clear()


# === API Protection Tests (AC#2) ===


@pytest.mark.asyncio
async def test_get_tasks_requires_auth(unauthenticated_client):
    """Test GET /api/tasks requires authentication."""
    response = await unauthenticated_client.get("/api/tasks")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_post_tasks_requires_auth(unauthenticated_client):
    """Test POST /api/tasks requires authentication."""
    response = await unauthenticated_client.post(
        "/api/tasks",
        json={
            "name": "Test Task",
            "api_endpoint": "https://api.example.com",
            "api_key": "test-key",
            "schedule_type": "interval",
            "interval_minutes": 60,
            "message_content": "Test message",
        }
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_task_by_id_requires_auth(unauthenticated_client):
    """Test GET /api/tasks/{id} requires authentication."""
    response = await unauthenticated_client.get("/api/tasks/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_put_task_requires_auth(unauthenticated_client):
    """Test PUT /api/tasks/{id} requires authentication."""
    response = await unauthenticated_client.put(
        "/api/tasks/1",
        json={"name": "Updated Task"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_delete_task_requires_auth(unauthenticated_client):
    """Test DELETE /api/tasks/{id} requires authentication."""
    response = await unauthenticated_client.delete("/api/tasks/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_task_logs_requires_auth(unauthenticated_client):
    """Test GET /api/tasks/{id}/logs requires authentication."""
    response = await unauthenticated_client.get("/api/tasks/1/logs")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# === Authenticated Access Tests (AC#3) ===


@pytest.mark.asyncio
async def test_get_tasks_authenticated(authenticated_client):
    """Test authenticated user can access GET /api/tasks (not blocked by auth).

    Database errors (500) are acceptable since we're testing auth, not DB.
    The key is it doesn't return 401. SQLAlchemy errors indicate auth passed
    and we reached the database layer.
    """
    from sqlalchemy.exc import OperationalError

    try:
        response = await authenticated_client.get("/api/tasks")
        # Should not return 401 when authenticated
        assert response.status_code != 401, "Should not return 401 when authenticated"
    except OperationalError:
        # Database errors mean auth passed successfully - we reached DB layer
        pass


# === Login Page No Auth Required (AC#4) ===


@pytest.mark.asyncio
async def test_login_page_no_auth_required(unauthenticated_client):
    """Test /login page does not require authentication."""
    response = await unauthenticated_client.get("/login")
    assert response.status_code == 200
    assert "AutoAI 登录" in response.text


@pytest.mark.asyncio
async def test_logout_no_auth_required(unauthenticated_client):
    """Test /logout does not require authentication (clears cookie)."""
    response = await unauthenticated_client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# === API Error Response Format (AC#5) ===


@pytest.mark.asyncio
async def test_api_401_response_format(unauthenticated_client):
    """Test 401 response has correct format: {"detail": "Not authenticated"}."""
    response = await unauthenticated_client.get("/api/tasks")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Not authenticated"
