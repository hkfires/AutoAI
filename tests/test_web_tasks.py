"""Tests for the web task management UI.

Tests server-side rendered pages and form submissions.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

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
    """Create a test client with overridden database session."""
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

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
        enabled=True,
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task


class TestListTasksPage:
    """Tests for the task list page."""

    @pytest.mark.asyncio
    async def test_list_tasks_page_renders_empty(self, client):
        """Test that the task list page renders with no tasks."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "任务列表" in response.text
        assert "暂无任务" in response.text

    @pytest.mark.asyncio
    async def test_list_tasks_page_renders_with_tasks(self, client, sample_task):
        """Test that the task list page renders with tasks."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "任务列表" in response.text
        assert "Sample Task" in response.text
        assert "60" in response.text  # interval_minutes

    @pytest.mark.asyncio
    async def test_list_tasks_shows_last_execution_time(self, client, sample_task, test_session):
        """Test that last execution time is displayed."""
        # Create execution log
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            status="success",
            response_summary="Test response",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        assert "2024-01-15 10:30" in response.text

    @pytest.mark.asyncio
    async def test_list_tasks_shows_message(self, client):
        """Test that flash messages are displayed."""
        response = await client.get("/?message=任务创建成功")

        assert response.status_code == 200
        assert "任务创建成功" in response.text


class TestNewTaskForm:
    """Tests for the new task form."""

    @pytest.mark.asyncio
    async def test_new_task_form_renders(self, client):
        """Test that the new task form renders successfully."""
        response = await client.get("/tasks/new")

        assert response.status_code == 200
        assert "新建任务" in response.text
        assert 'name="name"' in response.text
        assert 'name="api_endpoint"' in response.text
        assert 'type="password"' in response.text

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, test_session):
        """Test successful task creation via form."""
        response = await client.post(
            "/tasks/new",
            data={
                "name": "New Task",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "sk-test1234567890abcdef",
                "schedule_type": "interval",
                "interval_minutes": "60",
                "message_content": "Hello AI",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "message=" in response.headers["location"]

        # Verify task was created in database
        from sqlalchemy import select
        result = await test_session.execute(select(Task))
        tasks = result.scalars().all()
        assert len(tasks) == 1
        assert tasks[0].name == "New Task"

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, client):
        """Test that validation errors are displayed."""
        # Missing interval_minutes for interval schedule
        response = await client.post(
            "/tasks/new",
            data={
                "name": "Test Task",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "sk-test123",
                "schedule_type": "interval",
                "message_content": "Hello AI",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 400
        # Check for form re-render (should contain the form)
        assert 'name="name"' in response.text


class TestEditTaskForm:
    """Tests for the edit task form."""

    @pytest.mark.asyncio
    async def test_edit_task_form_renders(self, client, sample_task):
        """Test that the edit form renders with task data."""
        response = await client.get(f"/tasks/{sample_task.id}/edit")

        assert response.status_code == 200
        assert "编辑任务" in response.text
        assert "Sample Task" in response.text
        assert "留空保持原值" in response.text

    @pytest.mark.asyncio
    async def test_edit_task_not_found(self, client):
        """Test that edit redirects for non-existent task."""
        response = await client.get("/tasks/999/edit", follow_redirects=False)

        assert response.status_code == 303
        assert "message_type=error" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_update_task_success(self, client, sample_task, test_session):
        """Test successful task update via form."""
        response = await client.post(
            f"/tasks/{sample_task.id}/edit",
            data={
                "name": "Updated Task",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "schedule_type": "interval",
                "interval_minutes": "30",
                "message_content": "Updated message",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "message=" in response.headers["location"]

        # Refresh and verify update
        await test_session.refresh(sample_task)
        assert sample_task.name == "Updated Task"
        assert sample_task.interval_minutes == 30

    @pytest.mark.asyncio
    async def test_update_task_preserves_api_key_when_empty(self, client, sample_task, test_session):
        """Test that API key is preserved when field is empty."""
        original_key = sample_task.api_key

        response = await client.post(
            f"/tasks/{sample_task.id}/edit",
            data={
                "name": "Updated Task",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "",  # Empty - should preserve original
                "schedule_type": "interval",
                "interval_minutes": "30",
                "message_content": "Updated message",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        # Refresh and verify key was preserved
        await test_session.refresh(sample_task)
        assert sample_task.api_key == original_key


class TestDeleteTask:
    """Tests for task deletion."""

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client, sample_task, test_session):
        """Test successful task deletion."""
        task_id = sample_task.id

        response = await client.post(
            f"/tasks/{task_id}/delete",
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "message=" in response.headers["location"]
        # URL-encoded check: "Sample Task" or URL-encoded form
        location = response.headers["location"]
        assert "Sample" in location or "Sample%20Task" in location

        # Verify task was deleted
        from sqlalchemy import select
        result = await test_session.execute(select(Task).where(Task.id == task_id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, client):
        """Test delete redirects for non-existent task."""
        response = await client.post(
            "/tasks/999/delete",
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "message_type=error" in response.headers["location"]


class TestScheduleTypeToggle:
    """Tests for schedule type field toggling."""

    @pytest.mark.asyncio
    async def test_form_has_schedule_toggle_javascript(self, client):
        """Test that form includes JavaScript for toggling schedule fields."""
        response = await client.get("/tasks/new")

        assert response.status_code == 200
        assert "toggleScheduleFields" in response.text
        assert "interval-group" in response.text
        assert "fixed-time-group" in response.text

    @pytest.mark.asyncio
    async def test_create_fixed_time_task(self, client, test_session):
        """Test creating a task with fixed_time schedule."""
        response = await client.post(
            "/tasks/new",
            data={
                "name": "Daily Task",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "api_key": "sk-test1234567890abcdef",
                "schedule_type": "fixed_time",
                "fixed_time": "09:00",
                "message_content": "Good morning!",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        # Verify task was created with correct schedule
        from sqlalchemy import select
        result = await test_session.execute(select(Task))
        tasks = result.scalars().all()
        assert len(tasks) == 1
        assert tasks[0].schedule_type == "fixed_time"
        assert tasks[0].fixed_time == "09:00"


class TestFormDataPreservation:
    """Tests for form data preservation on validation errors."""

    @pytest.mark.asyncio
    async def test_create_task_preserves_form_data_on_error(self, client):
        """Test that form data is preserved when validation fails."""
        response = await client.post(
            "/tasks/new",
            data={
                "name": "My Test Task",
                "api_endpoint": "https://api.example.com",
                "api_key": "sk-test123",
                "schedule_type": "interval",
                # Missing interval_minutes - should fail validation
                "message_content": "Test message",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 400
        # Form data should be preserved in the response
        assert "My Test Task" in response.text
        assert "https://api.example.com" in response.text
        assert "Test message" in response.text

    @pytest.mark.asyncio
    async def test_update_task_preserves_form_data_on_error(self, client, sample_task):
        """Test that form data is preserved when update validation fails."""
        # Use an invalid fixed_time format to trigger validation error
        response = await client.post(
            f"/tasks/{sample_task.id}/edit",
            data={
                "name": "Updated Name",
                "api_endpoint": "https://api.example.com",
                "schedule_type": "fixed_time",
                "fixed_time": "invalid",  # Invalid format - should fail validation
                "message_content": "Updated message",
                "enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 400
        # Form data should be preserved
        assert "Updated Name" in response.text
        assert "Updated message" in response.text


class TestDatabaseErrorHandling:
    """Tests for database error handling."""

    @pytest.mark.asyncio
    async def test_database_error_returns_form_with_error(self, client, test_session):
        """Test that database errors are handled gracefully."""
        from unittest.mock import patch, AsyncMock
        from sqlalchemy.exc import IntegrityError

        with patch("app.web.tasks.task_service.create_task") as mock_create:
            mock_create.side_effect = IntegrityError(
                statement="INSERT",
                params={},
                orig=Exception("UNIQUE constraint failed")
            )

            response = await client.post(
                "/tasks/new",
                data={
                    "name": "Test Task",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "api_key": "sk-test1234567890abcdef",
                    "schedule_type": "interval",
                    "interval_minutes": "60",
                    "message_content": "Hello",
                    "enabled": "true",
                },
                follow_redirects=False,
            )

            assert response.status_code == 400
            # Check that form is re-rendered with error message
            assert 'name="name"' in response.text
            assert "alert-error" in response.text


class TestSchedulerErrorHandling:
    """Tests for scheduler error handling."""

    @pytest.mark.asyncio
    async def test_scheduler_failure_does_not_prevent_task_creation(self, client, test_session):
        """Test that scheduler failure doesn't prevent task from being saved."""
        from unittest.mock import patch

        with patch("app.web.tasks.add_job") as mock_add_job:
            mock_add_job.side_effect = Exception("Scheduler error")

            response = await client.post(
                "/tasks/new",
                data={
                    "name": "Test Task",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "api_key": "sk-test1234567890abcdef",
                    "schedule_type": "interval",
                    "interval_minutes": "60",
                    "message_content": "Hello",
                    "enabled": "true",
                },
                follow_redirects=False,
            )

            # Task should still be created successfully
            assert response.status_code == 303
            assert "message=" in response.headers["location"]

            # Verify task was saved to database
            from sqlalchemy import select
            result = await test_session.execute(select(Task))
            tasks = result.scalars().all()
            assert len(tasks) == 1
            assert tasks[0].name == "Test Task"

    @pytest.mark.asyncio
    async def test_reschedule_failure_does_not_prevent_task_update(self, client, sample_task, test_session):
        """Test that reschedule failure doesn't prevent task update."""
        from unittest.mock import patch

        with patch("app.web.tasks.reschedule_job") as mock_reschedule:
            mock_reschedule.side_effect = Exception("Reschedule error")

            response = await client.post(
                f"/tasks/{sample_task.id}/edit",
                data={
                    "name": "Updated Task",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "schedule_type": "interval",
                    "interval_minutes": "30",
                    "message_content": "Updated message",
                    "enabled": "true",
                },
                follow_redirects=False,
            )

            # Update should still succeed
            assert response.status_code == 303

            # Verify task was updated in database
            await test_session.refresh(sample_task)
            assert sample_task.name == "Updated Task"
            assert sample_task.interval_minutes == 30
