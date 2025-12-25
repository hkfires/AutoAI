"""Tests for the execution logs API.

Tests for GET /api/tasks/{task_id}/logs endpoint.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_session, Base
from app.models import Task, ExecutionLog


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def reset_security_singleton():
    """Reset the Fernet singleton before and after each test."""
    import app.utils.security as security
    security._fernet = None
    yield
    security._fernet = None


@pytest_asyncio.fixture
async def test_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Import models to register with Base.metadata
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_session):
    """Create a test client with overridden database session and authentication."""
    from app.web.auth import create_session_token

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        # Add authentication cookie for all requests
        token = create_session_token()
        ac.cookies.set("session", token)
        yield ac
        ac.cookies.clear()

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_task(test_session):
    """Create a sample task in the database."""
    from app.utils.security import encrypt_api_key

    task = Task(
        name="Sample Task",
        api_endpoint="https://api.openai.com/v1/chat/completions",
        api_key=encrypt_api_key("sk-sample1234567890"),
        schedule_type="interval",
        interval_minutes=60,
        message_content="Hello AI",
        model="gemini-claude-sonnet-4-5",
        enabled=True,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_task_with_logs(test_session, sample_task):
    """Create a sample task with execution logs."""
    # Create multiple logs with different statuses
    logs = [
        ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2025, 12, 23, 10, 0, 0, tzinfo=timezone.utc),
            status="success",
            response_summary="Response 1",
            error_message=None,
        ),
        ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2025, 12, 23, 11, 0, 0, tzinfo=timezone.utc),
            status="failed",
            response_summary=None,
            error_message="Connection timeout",
        ),
        ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
            status="success",
            response_summary="Response 3",
            error_message=None,
        ),
    ]
    for log in logs:
        test_session.add(log)
    await test_session.commit()
    return sample_task


class TestGetTaskLogs:
    """Tests for GET /api/tasks/{task_id}/logs endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_logs_success(self, client, sample_task_with_logs):
        """Test getting logs for a task returns correct data."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by executed_at descending (newest first)
        assert data[0]["status"] == "success"
        assert "12:00" in data[0]["executed_at"]

    @pytest.mark.asyncio
    async def test_get_task_logs_task_not_found(self, client):
        """Test 404 when task does not exist."""
        response = await client.get("/api/tasks/999/logs")

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_task_logs_empty(self, client, sample_task):
        """Test empty log list."""
        response = await client.get(f"/api/tasks/{sample_task.id}/logs")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_task_logs_with_limit(self, client, sample_task_with_logs):
        """Test logs API respects limit parameter."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_task_logs_order_descending(self, client, sample_task_with_logs):
        """Test logs are returned in descending order by executed_at."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs")

        assert response.status_code == 200
        data = response.json()
        # Latest log should be first (12:00)
        assert "12:00" in data[0]["executed_at"]
        assert "11:00" in data[1]["executed_at"]
        assert "10:00" in data[2]["executed_at"]

    @pytest.mark.asyncio
    async def test_get_task_logs_failed_status_has_error(self, client, sample_task_with_logs):
        """Test logs with failed status include error message."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs")

        assert response.status_code == 200
        data = response.json()
        # Find the failed log
        failed_log = next(log for log in data if log["status"] == "failed")
        assert failed_log["error_message"] == "Connection timeout"
        assert failed_log["response_summary"] is None

    @pytest.mark.asyncio
    async def test_get_task_logs_success_status_has_summary(self, client, sample_task_with_logs):
        """Test logs with success status include response summary."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs")

        assert response.status_code == 200
        data = response.json()
        # Find a successful log
        success_log = next(log for log in data if log["status"] == "success")
        assert success_log["response_summary"] is not None
        assert success_log["error_message"] is None

    @pytest.mark.asyncio
    async def test_get_task_logs_response_format(self, client, sample_task_with_logs):
        """Test that response matches ExecutionLogResponse schema."""
        response = await client.get(f"/api/tasks/{sample_task_with_logs.id}/logs")

        assert response.status_code == 200
        data = response.json()
        log = data[0]
        # Check all expected fields are present
        assert "id" in log
        assert "task_id" in log
        assert "executed_at" in log
        assert "status" in log
        assert "response_summary" in log
        assert "error_message" in log

    @pytest.mark.asyncio
    async def test_get_task_logs_limit_zero_rejected(self, client, sample_task):
        """Test that limit=0 is rejected with 422."""
        response = await client.get(f"/api/tasks/{sample_task.id}/logs?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_task_logs_limit_negative_rejected(self, client, sample_task):
        """Test that negative limit is rejected with 422."""
        response = await client.get(f"/api/tasks/{sample_task.id}/logs?limit=-1")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_task_logs_limit_exceeds_max_rejected(self, client, sample_task):
        """Test that limit > 100 is rejected with 422."""
        response = await client.get(f"/api/tasks/{sample_task.id}/logs?limit=101")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_task_logs_limit_max_allowed(self, client, sample_task):
        """Test that limit=100 is accepted."""
        response = await client.get(f"/api/tasks/{sample_task.id}/logs?limit=100")

        assert response.status_code == 200
