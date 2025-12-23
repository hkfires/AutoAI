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


class TestLogsPage:
    """Tests for task execution logs page."""

    @pytest.mark.asyncio
    async def test_logs_page_renders(self, client, sample_task, test_session):
        """Test that the logs page renders successfully."""
        # Create some logs
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            status="success",
            response_summary="Test response",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get(f"/tasks/{sample_task.id}/logs")

        assert response.status_code == 200
        assert "执行日志" in response.text
        assert "Sample Task" in response.text
        assert "成功" in response.text

    @pytest.mark.asyncio
    async def test_logs_page_task_not_found(self, client):
        """Test redirect when task does not exist."""
        response = await client.get("/tasks/999/logs", follow_redirects=False)

        assert response.status_code == 303
        assert "message_type=error" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_logs_page_empty(self, client, sample_task):
        """Test logs page with no execution history."""
        response = await client.get(f"/tasks/{sample_task.id}/logs")

        assert response.status_code == 200
        assert "暂无执行记录" in response.text

    @pytest.mark.asyncio
    async def test_logs_page_shows_failed_status(self, client, sample_task, test_session):
        """Test that failed logs show error message."""
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            status="failed",
            error_message="Connection timeout",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get(f"/tasks/{sample_task.id}/logs")

        assert response.status_code == 200
        assert "失败" in response.text
        assert "Connection timeout" in response.text

    @pytest.mark.asyncio
    async def test_logs_page_order_descending(self, client, sample_task, test_session):
        """Test that logs are displayed in descending order."""
        # Create logs with different times
        log1 = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
            status="success",
            response_summary="First",
        )
        log2 = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
            status="success",
            response_summary="Second",
        )
        test_session.add(log1)
        test_session.add(log2)
        await test_session.commit()

        response = await client.get(f"/tasks/{sample_task.id}/logs")

        assert response.status_code == 200
        # Second should appear before First (newest first)
        text = response.text
        second_pos = text.find("Second")
        first_pos = text.find("First")
        assert second_pos < first_pos


class TestDashboardStats:
    """Tests for dashboard statistics (Story 3.3)."""

    @pytest.mark.asyncio
    async def test_dashboard_stats_returned_in_response(self, client, sample_task):
        """Test that dashboard stats are included in the task list response."""
        response = await client.get("/")

        assert response.status_code == 200
        # Check for dashboard stat cards in the HTML
        assert "总任务数" in response.text
        assert "已启用" in response.text
        assert "今日执行" in response.text
        assert "今日成功率" in response.text
        # Verify dashboard card structure
        assert "dashboard-card" in response.text
        assert "card-value" in response.text

    @pytest.mark.asyncio
    async def test_dashboard_stats_with_no_tasks(self, client):
        """Test dashboard stats when there are no tasks."""
        response = await client.get("/")

        assert response.status_code == 200
        # Should show 0 for all stats
        # The stats should be present even with no tasks

    @pytest.mark.asyncio
    async def test_dashboard_today_executions_count(self, client, sample_task, test_session):
        """Test that today's execution count is calculated correctly."""
        # Create execution logs - some today, some not today
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's logs
        log_today1 = ExecutionLog(
            task_id=sample_task.id,
            executed_at=today_start.replace(hour=10),
            status="success",
            response_summary="Today 1",
        )
        log_today2 = ExecutionLog(
            task_id=sample_task.id,
            executed_at=today_start.replace(hour=11),
            status="failed",
            error_message="Error",
        )
        # Yesterday's log (should not be counted)
        from datetime import timedelta
        log_yesterday = ExecutionLog(
            task_id=sample_task.id,
            executed_at=today_start - timedelta(days=1),
            status="success",
            response_summary="Yesterday",
        )

        test_session.add_all([log_today1, log_today2, log_yesterday])
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # Should show 2 executions today (not 3)
        # Find the "今日执行" card and verify it shows "2"
        assert '>2<' in response.text or '>2</div>' in response.text

    @pytest.mark.asyncio
    async def test_dashboard_today_success_rate(self, client, sample_task, test_session):
        """Test that today's success rate is calculated correctly."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Create 3 successful and 1 failed execution today
        logs = [
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=9), status="success", response_summary="OK"),
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=10), status="success", response_summary="OK"),
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=11), status="success", response_summary="OK"),
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=12), status="failed", error_message="Err"),
        ]
        test_session.add_all(logs)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # Success rate should be 75% (3/4)
        assert "75%" in response.text

    @pytest.mark.asyncio
    async def test_dashboard_success_rate_no_executions(self, client, sample_task):
        """Test that success rate shows '--' when no executions today."""
        response = await client.get("/")

        assert response.status_code == 200
        # Should show "--" for success rate when no executions
        assert "--" in response.text

    @pytest.mark.asyncio
    async def test_dashboard_stats_enabled_tasks_count(self, client, test_session):
        """Test that enabled tasks count is correct."""
        from app.utils.security import encrypt_api_key

        # Create 3 tasks: 2 enabled, 1 disabled
        tasks = [
            Task(name="Task 1", api_endpoint="https://api.openai.com/v1/chat/completions",
                 api_key=encrypt_api_key("sk-test1"), schedule_type="interval",
                 interval_minutes=60, message_content="Hi", enabled=True),
            Task(name="Task 2", api_endpoint="https://api.openai.com/v1/chat/completions",
                 api_key=encrypt_api_key("sk-test2"), schedule_type="interval",
                 interval_minutes=60, message_content="Hi", enabled=True),
            Task(name="Task 3", api_endpoint="https://api.openai.com/v1/chat/completions",
                 api_key=encrypt_api_key("sk-test3"), schedule_type="interval",
                 interval_minutes=60, message_content="Hi", enabled=False),
        ]
        test_session.add_all(tasks)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # The response should contain stats showing 3 total, 2 enabled
        # Verify total tasks shows 3
        text = response.text
        # Find dashboard cards and verify values
        assert '>3<' in text or '>3</div>' in text  # total_tasks = 3
        assert '>2<' in text or '>2</div>' in text  # enabled_tasks = 2

    @pytest.mark.asyncio
    async def test_dashboard_boundary_midnight_utc(self, client, sample_task, test_session):
        """Test that boundary at 00:00:00 UTC is included in today's stats."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Create log exactly at midnight (should be counted)
        log_midnight = ExecutionLog(
            task_id=sample_task.id,
            executed_at=today_start,  # Exactly 00:00:00
            status="success",
            response_summary="Midnight",
        )
        test_session.add(log_midnight)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # Should count the midnight execution (success rate 100%)
        assert "100%" in response.text

    @pytest.mark.asyncio
    async def test_dashboard_zero_percent_success_rate(self, client, sample_task, test_session):
        """Test 0% success rate when all executions fail."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        logs = [
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=9), status="failed", error_message="Err"),
            ExecutionLog(task_id=sample_task.id, executed_at=today_start.replace(hour=10), status="failed", error_message="Err"),
        ]
        test_session.add_all(logs)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        assert "0%" in response.text


class TestTaskLastExecutionStatus:
    """Tests for task last execution status and schedule formatting (Story 3.3)."""

    @pytest.mark.asyncio
    async def test_task_list_shows_last_execution_status_success(self, client, sample_task, test_session):
        """Test that task list shows 'success' status for last successful execution."""
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime.now(timezone.utc),
            status="success",
            response_summary="OK",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        assert "status-success" in response.text

    @pytest.mark.asyncio
    async def test_task_list_shows_last_execution_status_failed(self, client, sample_task, test_session):
        """Test that task list shows 'failed' status for last failed execution."""
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime.now(timezone.utc),
            status="failed",
            error_message="Error",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        assert "status-failed" in response.text

    @pytest.mark.asyncio
    async def test_task_list_shows_never_executed(self, client, sample_task):
        """Test that task list shows 'never executed' status when no executions."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "status-never" in response.text

    @pytest.mark.asyncio
    async def test_failed_task_row_has_warning_class(self, client, sample_task, test_session):
        """Test that failed task row has warning highlight class."""
        log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=datetime.now(timezone.utc),
            status="failed",
            error_message="Error",
        )
        test_session.add(log)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        assert "row-warning" in response.text

    @pytest.mark.asyncio
    async def test_schedule_format_minutes(self, client, sample_task):
        """Test schedule displays in minutes format."""
        # sample_task has interval_minutes=60
        response = await client.get("/")

        assert response.status_code == 200
        # 60 minutes should display as "每 1 小时" (divisible by 60)
        assert "1 小时" in response.text

    @pytest.mark.asyncio
    async def test_schedule_format_hours(self, client, test_session):
        """Test schedule displays in hours format when >= 60 minutes and divisible by 60."""
        from app.utils.security import encrypt_api_key

        task = Task(
            name="Hourly Task",
            api_endpoint="https://api.openai.com/v1/chat/completions",
            api_key=encrypt_api_key("sk-test"),
            schedule_type="interval",
            interval_minutes=120,  # 2 hours
            message_content="Hi",
            enabled=True,
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # 120 minutes should display as "每 2 小时"
        assert "2 小时" in response.text

    @pytest.mark.asyncio
    async def test_schedule_format_non_hour_interval(self, client, test_session):
        """Test schedule displays in minutes format when not divisible by 60."""
        from app.utils.security import encrypt_api_key

        task = Task(
            name="90 Min Task",
            api_endpoint="https://api.openai.com/v1/chat/completions",
            api_key=encrypt_api_key("sk-test"),
            schedule_type="interval",
            interval_minutes=90,  # 1.5 hours - should show as minutes
            message_content="Hi",
            enabled=True,
        )
        test_session.add(task)
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # 90 minutes should display as "每 90 分钟" (not divisible by 60)
        assert "90 分钟" in response.text

    @pytest.mark.asyncio
    async def test_last_status_uses_most_recent_execution(self, client, sample_task, test_session):
        """Test that last status shows the MOST RECENT execution, not older ones."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        # Older log - failed
        old_log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=now - timedelta(hours=2),
            status="failed",
            error_message="Old error",
        )
        # Newer log - success
        new_log = ExecutionLog(
            task_id=sample_task.id,
            executed_at=now,
            status="success",
            response_summary="OK",
        )
        test_session.add_all([old_log, new_log])
        await test_session.commit()

        response = await client.get("/")

        assert response.status_code == 200
        # Should show success (most recent), not failed
        assert "status-success" in response.text
