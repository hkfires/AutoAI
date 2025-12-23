# tests/test_auth.py
"""Tests for authentication routes and session management."""

import os
import time
import pytest
import pytest_asyncio
from unittest.mock import patch
from cryptography.fernet import Fernet
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
    # Import after env is set
    from app.main import app as fastapi_app
    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# === Login Page Tests (AC#2, AC#3) ===


@pytest.mark.asyncio
async def test_login_page_renders(client):
    """Test GET /login returns login page."""
    response = await client.get("/login")
    assert response.status_code == 200
    assert "AutoAI 登录" in response.text
    assert "管理员密码" in response.text
    assert 'name="password"' in response.text


@pytest.mark.asyncio
async def test_login_page_redirects_if_authenticated(client):
    """Test authenticated user is redirected from login page."""
    from app.web.auth import create_session_token

    token = create_session_token()
    # Set cookie on client level to avoid deprecation warning
    client.cookies.set("session", token)
    response = await client.get("/login")
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    client.cookies.clear()


# === Login Success Tests (AC#2) ===


@pytest.mark.asyncio
async def test_login_success_redirects_to_home(client):
    """Test successful login redirects to home page."""
    response = await client.post(
        "/login",
        data={"password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@pytest.mark.asyncio
async def test_login_success_sets_session_cookie(client):
    """Test successful login sets session cookie."""
    response = await client.post(
        "/login",
        data={"password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert "session" in response.cookies
    assert response.cookies["session"]  # Cookie has a value


# === Login Failure Tests (AC#3) ===


@pytest.mark.asyncio
async def test_login_failure_wrong_password(client):
    """Test login with wrong password shows error."""
    response = await client.post(
        "/login",
        data={"password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "密码错误" in response.text


@pytest.mark.asyncio
async def test_login_failure_stays_on_login_page(client):
    """Test failed login stays on login page."""
    response = await client.post(
        "/login",
        data={"password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "AutoAI 登录" in response.text
    assert 'name="password"' in response.text


@pytest.mark.asyncio
async def test_login_failure_no_session_cookie(client):
    """Test failed login does not set session cookie."""
    response = await client.post(
        "/login",
        data={"password": "wrongpassword"},
    )
    assert "session" not in response.cookies


# === Logout Tests (AC#4) ===


@pytest.mark.asyncio
async def test_logout_redirects_to_login(client):
    """Test logout redirects to login page."""
    from app.web.auth import create_session_token

    token = create_session_token()
    # Set cookie on client level to avoid deprecation warning
    client.cookies.set("session", token)
    response = await client.post(
        "/logout",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    client.cookies.clear()


@pytest.mark.asyncio
async def test_logout_clears_session_cookie(client):
    """Test logout clears the session cookie."""
    from app.web.auth import create_session_token

    token = create_session_token()
    # Set cookie on client level to avoid deprecation warning
    client.cookies.set("session", token)
    response = await client.post(
        "/logout",
        follow_redirects=False,
    )
    # Cookie should be deleted (empty or max-age=0)
    set_cookie = response.headers.get("set-cookie", "")
    assert "session=" in set_cookie
    # Cookie deletion typically sets max-age=0 or expires in past
    assert 'max-age=0' in set_cookie.lower() or 'expires=' in set_cookie.lower()
    client.cookies.clear()


# === Session Validation Tests (AC#5, AC#6) ===


def test_verify_session_token_valid():
    """Test valid session token is verified correctly."""
    from app.web.auth import create_session_token, verify_session_token

    token = create_session_token()
    assert verify_session_token(token) is True


def test_verify_session_token_invalid():
    """Test invalid session token is rejected."""
    from app.web.auth import verify_session_token

    assert verify_session_token("invalid-token") is False
    assert verify_session_token("") is False
    assert verify_session_token(None) is False


def test_verify_session_token_tampered():
    """Test tampered session token is rejected."""
    from app.web.auth import create_session_token, verify_session_token

    token = create_session_token()
    # Tamper with the token
    tampered = token[:-5] + "XXXXX"
    assert verify_session_token(tampered) is False


def test_session_token_expired():
    """Test expired session token is rejected."""
    from app.web.auth import get_serializer, verify_session_token, SESSION_MAX_AGE

    # Create a token with a past timestamp by mocking time
    serializer = get_serializer()
    token = serializer.dumps({"authenticated": True})

    # Mock loads to simulate expired token
    with patch.object(serializer, 'loads') as mock_loads:
        from itsdangerous import SignatureExpired
        mock_loads.side_effect = SignatureExpired("Token expired")

        # Need to patch get_serializer to return our mocked serializer
        with patch('app.web.auth.get_serializer', return_value=serializer):
            assert verify_session_token(token) is False


def test_get_current_user_authenticated():
    """Test get_current_user returns True for valid session."""
    from app.web.auth import create_session_token, get_current_user

    token = create_session_token()
    assert get_current_user(session=token) is True


def test_get_current_user_not_authenticated():
    """Test get_current_user returns False for no session."""
    from app.web.auth import get_current_user

    assert get_current_user(session=None) is False
    assert get_current_user(session="") is False


# === Auth Dependency Tests (Story 3.2) ===


def test_require_auth_web_raises_on_no_session():
    """Test require_auth_web raises AuthRedirectException when not authenticated."""
    from app.web.auth import require_auth_web, AuthRedirectException

    with pytest.raises(AuthRedirectException):
        require_auth_web(session=None)


def test_require_auth_web_raises_on_invalid_session():
    """Test require_auth_web raises AuthRedirectException for invalid session."""
    from app.web.auth import require_auth_web, AuthRedirectException

    with pytest.raises(AuthRedirectException):
        require_auth_web(session="invalid-token")


def test_require_auth_web_passes_with_valid_session():
    """Test require_auth_web returns True for valid session."""
    from app.web.auth import require_auth_web, create_session_token

    token = create_session_token()
    result = require_auth_web(session=token)
    assert result is True


def test_require_auth_api_raises_on_no_session():
    """Test require_auth_api raises HTTPException 401 when not authenticated."""
    from fastapi import HTTPException
    from app.web.auth import require_auth_api

    with pytest.raises(HTTPException) as exc_info:
        require_auth_api(session=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_require_auth_api_raises_on_invalid_session():
    """Test require_auth_api raises HTTPException 401 for invalid session."""
    from fastapi import HTTPException
    from app.web.auth import require_auth_api

    with pytest.raises(HTTPException) as exc_info:
        require_auth_api(session="invalid-token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_require_auth_api_passes_with_valid_session():
    """Test require_auth_api returns True for valid session."""
    from app.web.auth import require_auth_api, create_session_token

    token = create_session_token()
    result = require_auth_api(session=token)
    assert result is True


@pytest.mark.asyncio
async def test_auth_redirect_exception_handler(client):
    """Test AuthRedirectException is handled by redirecting to /login."""
    # Access a protected page without authentication
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


# === Web Route Protection Tests (Story 3.2 AC#1) ===


@pytest.mark.asyncio
async def test_task_list_redirects_when_unauthenticated(client):
    """Test / redirects to /login when not authenticated."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_new_task_form_redirects_when_unauthenticated(client):
    """Test /tasks/new redirects to /login when not authenticated."""
    response = await client.get("/tasks/new", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_edit_task_form_redirects_when_unauthenticated(client):
    """Test /tasks/{id}/edit redirects to /login when not authenticated."""
    response = await client.get("/tasks/1/edit", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_task_logs_redirects_when_unauthenticated(client):
    """Test /tasks/{id}/logs redirects to /login when not authenticated."""
    response = await client.get("/tasks/1/logs", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


# === Authenticated Web Access Tests (Story 3.2 AC#3) ===


@pytest.mark.asyncio
async def test_task_list_accessible_when_authenticated(client):
    """Test / does not redirect to /login when authenticated.

    Authentication passes, response is not a redirect to login.
    Database errors (500) are acceptable since we're testing auth, not DB.
    SQLAlchemy errors indicate auth passed and we reached the database layer.
    """
    from app.web.auth import create_session_token
    from sqlalchemy.exc import OperationalError

    token = create_session_token()
    client.cookies.set("session", token)
    try:
        response = await client.get("/", follow_redirects=False)
        # Should not redirect to login when authenticated
        is_login_redirect = (
            response.status_code == 302 and
            response.headers.get("location") == "/login"
        )
        assert not is_login_redirect, "Should not redirect to login when authenticated"
    except OperationalError:
        # Database errors mean auth passed successfully - we reached DB layer
        pass
    finally:
        client.cookies.clear()


@pytest.mark.asyncio
async def test_new_task_form_accessible_when_authenticated(client):
    """Test /tasks/new does not redirect to /login when authenticated."""
    from app.web.auth import create_session_token

    token = create_session_token()
    client.cookies.set("session", token)
    try:
        response = await client.get("/tasks/new", follow_redirects=False)
        # Should not redirect to login when authenticated
        is_login_redirect = (
            response.status_code == 302 and
            response.headers.get("location") == "/login"
        )
        assert not is_login_redirect, "Should not redirect to login when authenticated"
    finally:
        client.cookies.clear()


# === Web POST Route Protection Tests (Story 3.2 AC#1) ===


@pytest.mark.asyncio
async def test_create_task_post_redirects_when_unauthenticated(client):
    """Test POST /tasks/new redirects to /login when not authenticated."""
    response = await client.post(
        "/tasks/new",
        data={
            "name": "Test",
            "api_endpoint": "https://api.example.com",
            "api_key": "sk-test123",
            "schedule_type": "interval",
            "interval_minutes": "60",
            "message_content": "Hello",
            "enabled": "true",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_update_task_post_redirects_when_unauthenticated(client):
    """Test POST /tasks/{id}/edit redirects to /login when not authenticated."""
    response = await client.post(
        "/tasks/1/edit",
        data={
            "name": "Updated",
            "api_endpoint": "https://api.example.com",
            "schedule_type": "interval",
            "interval_minutes": "60",
            "message_content": "Hello",
            "enabled": "true",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_delete_task_post_redirects_when_unauthenticated(client):
    """Test POST /tasks/{id}/delete redirects to /login when not authenticated."""
    response = await client.post("/tasks/1/delete", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
