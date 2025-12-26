"""Task API Endpoint Tests.

Tests for Task CRUD REST API endpoints.
"""

import re

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_session, Base


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


# Test data
VALID_TASK_DATA = {
    "name": "Test Task",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-test1234567890abcdef",
    "schedule_type": "interval",
    "interval_minutes": 60,
    "message_content": "Hello, AI!",
    "model": "gemini-claude-sonnet-4-5",
    "enabled": True,
}

VALID_FIXED_TIME_TASK = {
    "name": "Fixed Time Task",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-fixedtime1234567890",
    "schedule_type": "fixed_time",
    "fixed_time": "09:30",
    "message_content": "Good morning!",
    "model": "gpt-4",
    "enabled": True,
}


class TestCreateTask:
    """Tests for POST /api/tasks endpoint."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, client):
        """Test creating a task successfully."""
        response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert "id" in data
        # API key should be masked in format: first4...last4
        assert re.match(r"^.{4}\.\.\..{4}$", data["api_key"]), \
            f"API key not properly masked: {data['api_key']}"
        assert data["schedule_type"] == "interval"
        assert data["interval_minutes"] == 60

    @pytest.mark.asyncio
    async def test_create_fixed_time_task_success(self, client):
        """Test creating a fixed_time task successfully."""
        response = await client.post("/api/tasks", json=VALID_FIXED_TIME_TASK)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Fixed Time Task"
        assert data["schedule_type"] == "fixed_time"
        assert data["fixed_time"] == "09:30"

    @pytest.mark.asyncio
    async def test_create_task_missing_interval(self, client):
        """Test creating interval task without interval_minutes fails."""
        invalid_data = {
            **VALID_TASK_DATA,
            "schedule_type": "interval",
            "interval_minutes": None
        }
        response = await client.post("/api/tasks", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_task_missing_fixed_time(self, client):
        """Test creating fixed_time task without fixed_time fails."""
        invalid_data = {
            "name": "Test Task",
            "api_endpoint": "https://api.example.com",
            "api_key": "sk-test1234567890abcdef",
            "schedule_type": "fixed_time",
            "message_content": "Hello!",
            "model": "gpt-4",
            "enabled": True,
        }
        response = await client.post("/api/tasks", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_task_invalid_fixed_time_format(self, client):
        """Test creating task with invalid fixed_time format fails."""
        invalid_data = {
            **VALID_FIXED_TIME_TASK,
            "fixed_time": "25:00"  # Invalid hour
        }
        response = await client.post("/api/tasks", json=invalid_data)
        assert response.status_code == 422


class TestGetTasks:
    """Tests for GET /api/tasks endpoint."""

    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, client):
        """Test getting tasks when none exist."""
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_tasks_with_data(self, client):
        """Test getting tasks when tasks exist."""
        # Create two tasks
        await client.post("/api/tasks", json=VALID_TASK_DATA)
        await client.post("/api/tasks", json=VALID_FIXED_TIME_TASK)

        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # API keys should be masked in format: first4...last4
        for task in data:
            assert re.match(r"^.{4}\.\.\..{4}$", task["api_key"]), \
                f"API key not properly masked: {task['api_key']}"


class TestGetTask:
    """Tests for GET /api/tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_success(self, client):
        """Test getting a task by ID."""
        # Create task first
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client):
        """Test getting a non-existent task."""
        response = await client.get("/api/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestUpdateTask:
    """Tests for PUT /api/tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_task_success(self, client):
        """Test updating a task successfully."""
        # Create task first
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Update name
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"name": "Updated Task Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task Name"
        # Other fields unchanged
        assert data["interval_minutes"] == 60

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, client):
        """Test updating a non-existent task."""
        response = await client.put("/api/tasks/999", json={"name": "Updated"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task_partial(self, client):
        """Test partial update of a task."""
        # Create task
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Update only enabled field
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"enabled": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["name"] == "Test Task"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_schedule_validation(self, client):
        """Test updating schedule type requires corresponding field."""
        # Create with interval
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Try to change to fixed_time without fixed_time value
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"schedule_type": "fixed_time"}
        )
        assert response.status_code == 400
        assert "fixed_time is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_to_interval_without_minutes(self, client):
        """Test updating to interval type without interval_minutes fails."""
        # Create with fixed_time
        create_response = await client.post("/api/tasks", json=VALID_FIXED_TIME_TASK)
        task_id = create_response.json()["id"]

        # Try to change to interval without interval_minutes
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"schedule_type": "interval"}
        )
        assert response.status_code == 400
        assert "interval_minutes or interval_seconds must be greater than 0" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_schedule_type_with_value(self, client):
        """Test updating schedule type with corresponding value succeeds."""
        # Create with interval
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Change to fixed_time with fixed_time value
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"schedule_type": "fixed_time", "fixed_time": "14:00"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_type"] == "fixed_time"
        assert data["fixed_time"] == "14:00"

    @pytest.mark.asyncio
    async def test_update_task_encrypts_new_api_key(self, client, test_session):
        """Test that updating API key properly encrypts the new value."""
        from app.models import Task
        from sqlalchemy import select

        # Create task
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Update with new API key
        new_key = "sk-new-secret-key-67890"
        await client.put(f"/api/tasks/{task_id}", json={"api_key": new_key})

        # Verify database stores encrypted value (not plain text)
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        assert task.api_key != new_key  # Should be encrypted
        assert task.api_key != VALID_TASK_DATA["api_key"]  # Different from original

    @pytest.mark.asyncio
    async def test_update_task_preserves_api_key_when_not_provided(self, client, test_session):
        """Test that updating without api_key preserves the original encrypted key."""
        from app.models import Task
        from sqlalchemy import select

        # Create task
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Get original encrypted key from database
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        original_encrypted_key = task.api_key

        # Update without providing api_key
        await client.put(f"/api/tasks/{task_id}", json={"name": "Updated Name"})

        # Refresh session to get updated data (expire_all is sync method)
        test_session.expire_all()
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        updated_task = result.scalar_one()

        # Verify original encrypted key is preserved
        assert updated_task.api_key == original_encrypted_key
        assert updated_task.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_schedule_type_clears_unused_field(self, client):
        """Test that changing schedule_type clears the unused schedule field."""
        # Create with interval
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]
        assert create_response.json()["interval_minutes"] == 60

        # Change to fixed_time - should clear interval_minutes
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"schedule_type": "fixed_time", "fixed_time": "14:00"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_type"] == "fixed_time"
        assert data["fixed_time"] == "14:00"
        assert data["interval_minutes"] is None  # Should be cleared


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{task_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client):
        """Test deleting a task."""
        # Create first
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Delete
        response = await client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, client):
        """Test deleting a non-existent task."""
        response = await client.delete("/api/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestApiKeyMasking:
    """Tests for API key masking in responses."""

    @pytest.mark.asyncio
    async def test_create_response_masks_key(self, client):
        """Test that create response masks API key in correct format."""
        response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        assert response.status_code == 201
        data = response.json()
        # API key should be masked in format: first4...last4
        assert re.match(r"^.{4}\.\.\..{4}$", data["api_key"]), \
            f"API key not properly masked: {data['api_key']}"
        # Plain text API key should NOT appear in response
        assert VALID_TASK_DATA["api_key"] not in str(data)

    @pytest.mark.asyncio
    async def test_get_response_masks_key(self, client):
        """Test that get response masks API key."""
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert re.match(r"^.{4}\.\.\..{4}$", data["api_key"]), \
            f"API key not properly masked: {data['api_key']}"

    @pytest.mark.asyncio
    async def test_update_response_masks_key(self, client):
        """Test that update response masks API key."""
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        new_key = "sk-newkey1234567890xyz"
        response = await client.put(
            f"/api/tasks/{task_id}",
            json={"api_key": new_key}
        )
        assert response.status_code == 200
        data = response.json()
        # New key should be masked
        assert re.match(r"^.{4}\.\.\..{4}$", data["api_key"]), \
            f"API key not properly masked: {data['api_key']}"
        # Plain text key should NOT appear
        assert new_key not in str(data)


# =============================================================================
# Immediate Execution Tests for API Endpoints
# =============================================================================

class TestAPIImmediateExecution:
    """Tests for immediate execution via API endpoints (AC #5)."""

    @pytest.mark.asyncio
    async def test_create_interval_task_executes_immediately(self, client):
        """Test that creating an interval task via API executes immediately."""
        from unittest.mock import patch, MagicMock

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            response = await client.post("/api/tasks", json=VALID_TASK_DATA)
            assert response.status_code == 201

            # Verify immediate execution was triggered
            mock_loop.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_interval_task_executes_immediately(self, client):
        """Test that updating an interval task via API executes immediately."""
        from unittest.mock import patch, MagicMock

        # Create task first
        create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
        task_id = create_response.json()["id"]

        # Update task
        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            response = await client.put(
                f"/api/tasks/{task_id}",
                json={"interval_minutes": 45}
            )
            assert response.status_code == 200

            # Verify immediate execution was triggered
            mock_loop.create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_fixed_time_task_not_executed_immediately(self, client):
        """Test that creating a fixed_time task via API does not execute immediately."""
        from unittest.mock import patch, MagicMock

        fixed_time_data = {
            "name": "API Fixed Time Task",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
            "api_key": "sk-test1234567890abcdef",
            "schedule_type": "fixed_time",
            "fixed_time": "09:00",
            "message_content": "Test message",
            "model": "gpt-4",
            "enabled": True,
        }

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            response = await client.post("/api/tasks", json=fixed_time_data)
            assert response.status_code == 201

            # Verify immediate execution was NOT triggered
            mock_loop.create_task.assert_not_called()

