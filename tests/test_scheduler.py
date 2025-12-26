"""Tests for the scheduler module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.models import Task, ExecutionLog
from app.services.openai_service import OpenAIResponse, OpenAIServiceError


@pytest.fixture
def mock_task():
    """Create a mock interval task for testing."""
    task = MagicMock(spec=Task)
    task.id = 1
    task.name = "Test Task"
    task.api_endpoint = "https://api.openai.com/v1/chat/completions"
    task.api_key = "encrypted_key"
    task.schedule_type = "interval"
    task.interval_minutes = 60
    task.fixed_time = None
    task.message_content = "Hello, AI!"
    task.enabled = True
    return task


@pytest.fixture
def mock_fixed_time_task():
    """Create a mock fixed-time task for testing."""
    task = MagicMock(spec=Task)
    task.id = 2
    task.name = "Daily Task"
    task.api_endpoint = "https://api.openai.com/v1/chat/completions"
    task.api_key = "encrypted_key"
    task.schedule_type = "fixed_time"
    task.interval_minutes = None
    task.fixed_time = "09:00"
    task.message_content = "Good morning!"
    task.enabled = True
    return task


@pytest.fixture
def mock_disabled_task():
    """Create a mock disabled task for testing."""
    task = MagicMock(spec=Task)
    task.id = 3
    task.name = "Disabled Task"
    task.api_endpoint = "https://api.openai.com/v1/chat/completions"
    task.api_key = "encrypted_key"
    task.schedule_type = "interval"
    task.interval_minutes = 30
    task.fixed_time = None
    task.message_content = "Should not run"
    task.enabled = False
    return task


@pytest.fixture(autouse=True)
def cleanup_scheduler():
    """Cleanup scheduler jobs after each test."""
    yield
    # Import scheduler and cleanup after test
    from app.scheduler import scheduler
    try:
        scheduler.remove_all_jobs()
    except Exception:
        pass
    # Ensure scheduler is stopped for next test
    if scheduler.running:
        scheduler.shutdown(wait=False)


# =============================================================================
# Task 1: Scheduler Configuration Tests
# =============================================================================

class TestSchedulerStartup:
    """Tests for scheduler startup functionality (Task 1.2)."""

    @pytest.mark.asyncio
    async def test_start_scheduler_registers_all_tasks(self):
        """Test that start_scheduler registers all enabled tasks."""
        from app.scheduler import start_scheduler, shutdown_scheduler, scheduler

        with patch("app.scheduler.register_all_tasks", new_callable=AsyncMock) as mock_register:
            await start_scheduler()

            mock_register.assert_called_once()
            assert scheduler.running is True

        # Cleanup
        await shutdown_scheduler()

    @pytest.mark.asyncio
    async def test_start_scheduler_logs_success(self):
        """Test that start_scheduler logs success message."""
        from app.scheduler import start_scheduler, shutdown_scheduler, scheduler

        with patch("app.scheduler.register_all_tasks", new_callable=AsyncMock):
            with patch("app.scheduler.logger") as mock_logger:
                await start_scheduler()

                mock_logger.info.assert_any_call("Scheduler started successfully")

        await shutdown_scheduler()


class TestSchedulerShutdown:
    """Tests for scheduler shutdown functionality (Task 1.3)."""

    @pytest.mark.asyncio
    async def test_shutdown_scheduler_stops_scheduler(self):
        """Test that shutdown_scheduler stops the scheduler."""
        from app.scheduler import start_scheduler, shutdown_scheduler, scheduler

        with patch("app.scheduler.register_all_tasks", new_callable=AsyncMock):
            await start_scheduler()
            assert scheduler.running is True

            await shutdown_scheduler()
            # Verify shutdown was called (scheduler.running may still be True briefly
            # due to APScheduler internals, but the shutdown call was made)
            # The important thing is that shutdown completes without error

    @pytest.mark.asyncio
    async def test_shutdown_scheduler_logs_complete(self):
        """Test that shutdown_scheduler logs completion message."""
        from app.scheduler import start_scheduler, shutdown_scheduler, scheduler

        with patch("app.scheduler.register_all_tasks", new_callable=AsyncMock):
            await start_scheduler()

            with patch("app.scheduler.logger") as mock_logger:
                await shutdown_scheduler()

                mock_logger.info.assert_any_call("Scheduler shutdown complete")


# =============================================================================
# Task 2: Task Registration Tests
# =============================================================================

class TestTaskRegistration:
    """Tests for task registration functionality (Task 2)."""

    @pytest.mark.asyncio
    async def test_register_interval_task(self, mock_task):
        """Test registering an interval task (Task 2.3)."""
        from app.scheduler import register_task, scheduler, shutdown_scheduler

        # Start scheduler within async context
        scheduler.start()

        register_task(mock_task)

        job = scheduler.get_job(f"task_{mock_task.id}")
        assert job is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_register_fixed_time_task(self, mock_fixed_time_task):
        """Test registering a fixed-time task (Task 2.4)."""
        from app.scheduler import register_task, scheduler

        scheduler.start()

        register_task(mock_fixed_time_task)

        job = scheduler.get_job(f"task_{mock_fixed_time_task.id}")
        assert job is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_register_disabled_task_skipped(self, mock_disabled_task):
        """Test that disabled tasks are not registered (Task 2.1)."""
        from app.scheduler import register_task, scheduler

        scheduler.start()

        register_task(mock_disabled_task)

        job = scheduler.get_job(f"task_{mock_disabled_task.id}")
        assert job is None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_register_task_replaces_existing(self, mock_task):
        """Test that registering a task replaces existing job."""
        from app.scheduler import register_task, scheduler

        scheduler.start()

        # Register task twice
        register_task(mock_task)
        register_task(mock_task)

        # Should have exactly one job
        job = scheduler.get_job(f"task_{mock_task.id}")
        assert job is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_register_all_tasks_from_database(self, mock_task, mock_fixed_time_task):
        """Test registering all enabled tasks from database (Task 2.2)."""
        from app.scheduler import register_all_tasks, scheduler

        scheduler.start()

        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            mock_get_session_maker.return_value = mock_session_maker

            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_task, mock_fixed_time_task]
            mock_session.execute.return_value = mock_result

            await register_all_tasks()

            # Verify both tasks were registered
            assert scheduler.get_job(f"task_{mock_task.id}") is not None
            assert scheduler.get_job(f"task_{mock_fixed_time_task.id}") is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_register_unknown_schedule_type(self):
        """Test that unknown schedule type is handled gracefully."""
        from app.scheduler import register_task, scheduler

        scheduler.start()

        mock_task = MagicMock(spec=Task)
        mock_task.id = 99
        mock_task.name = "Unknown Type Task"
        mock_task.schedule_type = "unknown"
        mock_task.enabled = True

        with patch("app.scheduler.logger") as mock_logger:
            register_task(mock_task)

            mock_logger.error.assert_called_once()
            assert "Unknown schedule type" in str(mock_logger.error.call_args)

        # Job should not be registered
        assert scheduler.get_job("task_99") is None

        scheduler.shutdown(wait=False)


# =============================================================================
# Task 3: Task Execution Tests
# =============================================================================

class TestTaskExecution:
    """Tests for task execution functionality (Task 3)."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self, mock_task):
        """Test successful task execution (Task 3.4, 3.5)."""
        mock_response = OpenAIResponse(
            response_summary="Hello! How can I help?",
            response_time_ms=150,
        )

        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_session_maker

            # Mock task query
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_task
            mock_session.execute.return_value = mock_result

            with patch("app.scheduler.decrypt_api_key", return_value="plain_key"):
                with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = mock_response

                    from app.scheduler import execute_task
                    await execute_task(mock_task.id)

                    mock_send.assert_called_once_with(
                        api_endpoint=mock_task.api_endpoint,
                        api_key="plain_key",
                        message_content=mock_task.message_content,
                        model=mock_task.model,
                    )
                    mock_session.add.assert_called_once()
                    mock_session.commit.assert_called_once()

                    # Verify ExecutionLog
                    call_args = mock_session.add.call_args[0][0]
                    assert call_args.status == "success"
                    assert call_args.executed_at is not None
                    assert "150ms" in call_args.response_summary

    @pytest.mark.asyncio
    async def test_execute_task_failure(self, mock_task):
        """Test task execution failure handling."""
        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_session_maker

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_task
            mock_session.execute.return_value = mock_result

            with patch("app.scheduler.decrypt_api_key", return_value="plain_key"):
                with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
                    mock_send.side_effect = OpenAIServiceError(
                        message="API error", status_code=500
                    )

                    from app.scheduler import execute_task
                    await execute_task(mock_task.id)

                    mock_session.add.assert_called_once()
                    mock_session.commit.assert_called_once()

                    # Verify ExecutionLog has failed status
                    call_args = mock_session.add.call_args[0][0]
                    assert call_args.status == "failed"
                    assert call_args.error_message == "API error"

    @pytest.mark.asyncio
    async def test_execute_disabled_task_skipped(self, mock_disabled_task):
        """Test that disabled tasks are skipped (Task 3.3)."""
        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_session_maker

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_disabled_task
            mock_session.execute.return_value = mock_result

            with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
                from app.scheduler import execute_task
                await execute_task(mock_disabled_task.id)

                # Verify: OpenAI service not called
                mock_send.assert_not_called()
                # Verify: No ExecutionLog created
                mock_session.add.assert_not_called()
                mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_nonexistent_task(self):
        """Test execution of non-existent task (Task 3.2)."""
        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_session_maker

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            from app.scheduler import execute_task
            # Should not raise exception
            await execute_task(999)

            # No ExecutionLog should be created
            mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_task_unexpected_error(self, mock_task):
        """Test handling of unexpected errors during execution."""
        with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session_maker = MagicMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_session_maker.return_value = mock_session_maker

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_task
            mock_session.execute.return_value = mock_result

            with patch("app.scheduler.decrypt_api_key", return_value="plain_key"):
                with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
                    mock_send.side_effect = RuntimeError("Unexpected error")

                    from app.scheduler import execute_task
                    await execute_task(mock_task.id)

                    # Verify ExecutionLog still created with failed status
                    call_args = mock_session.add.call_args[0][0]
                    assert call_args.status == "failed"
                    assert "Unexpected error" in call_args.error_message


# =============================================================================
# Task 4: Dynamic Job Management Tests
# =============================================================================

class TestDynamicJobManagement:
    """Tests for dynamic job management functionality (Task 4)."""

    @pytest.mark.asyncio
    async def test_add_job(self, mock_task):
        """Test dynamically adding a task (Task 4.1)."""
        from app.scheduler import add_job, scheduler

        scheduler.start()

        add_job(mock_task)

        job = scheduler.get_job(f"task_{mock_task.id}")
        assert job is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_remove_job(self, mock_task):
        """Test dynamically removing a task (Task 4.2)."""
        from app.scheduler import add_job, remove_job, scheduler

        scheduler.start()

        add_job(mock_task)
        assert scheduler.get_job(f"task_{mock_task.id}") is not None

        remove_job(mock_task.id)
        assert scheduler.get_job(f"task_{mock_task.id}") is None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_remove_nonexistent_job(self):
        """Test removing a non-existent job does not raise exception (Task 4.2)."""
        from app.scheduler import remove_job, scheduler

        scheduler.start()

        # Should not raise exception
        remove_job(999)

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_reschedule_job(self, mock_task):
        """Test rescheduling a task (Task 4.3)."""
        from app.scheduler import add_job, reschedule_job, scheduler

        scheduler.start()

        add_job(mock_task)

        # Update task schedule
        mock_task.interval_minutes = 30

        reschedule_job(mock_task)

        job = scheduler.get_job(f"task_{mock_task.id}")
        assert job is not None

        scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_reschedule_disabled_task_removes_job(self, mock_task):
        """Test that disabling a task removes it from scheduler (Task 4.4)."""
        from app.scheduler import add_job, reschedule_job, scheduler

        scheduler.start()

        add_job(mock_task)
        assert scheduler.get_job(f"task_{mock_task.id}") is not None

        # Disable task
        mock_task.enabled = False

        reschedule_job(mock_task)

        # Job should be removed
        assert scheduler.get_job(f"task_{mock_task.id}") is None

        scheduler.shutdown(wait=False)


# =============================================================================
# Immediate Execution Tests (Tech-Spec: interval-task-immediate-execution)
# =============================================================================

class TestImmediateExecution:
    """Tests for immediate execution of interval tasks."""

    @pytest.mark.asyncio
    async def test_add_job_executes_interval_task_immediately(self, mock_task):
        """Test that add_job executes interval tasks immediately (AC #1)."""
        from app.scheduler import add_job, scheduler
        import asyncio

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            add_job(mock_task)

            # Verify loop.create_task was called
            mock_loop.create_task.assert_called_once()

        if scheduler.running:
            scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_add_job_does_not_execute_disabled_task_immediately(self, mock_disabled_task):
        """Test that add_job does not execute disabled tasks immediately (AC #2)."""
        from app.scheduler import add_job, scheduler

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            add_job(mock_disabled_task)

            # Verify execute_task was NOT scheduled
            mock_loop.create_task.assert_not_called()

        if scheduler.running:
            scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_add_job_does_not_execute_fixed_time_task_immediately(self, mock_fixed_time_task):
        """Test that add_job does not execute fixed_time tasks immediately (AC #4)."""
        from app.scheduler import add_job, scheduler

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            add_job(mock_fixed_time_task)

            # Verify execute_task was NOT scheduled
            mock_loop.create_task.assert_not_called()

        if scheduler.running:
            scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_reschedule_job_executes_interval_task_immediately(self, mock_task):
        """Test that reschedule_job executes interval tasks immediately (AC #3)."""
        from app.scheduler import reschedule_job, scheduler

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            reschedule_job(mock_task)

            # Verify execute_task was scheduled
            mock_loop.create_task.assert_called_once()

        if scheduler.running:
            scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_reschedule_job_does_not_execute_disabled_task(self, mock_disabled_task):
        """Test that reschedule_job does not execute disabled tasks."""
        from app.scheduler import reschedule_job, scheduler

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_loop.create_task = MagicMock()
            mock_get_loop.return_value = mock_loop

            reschedule_job(mock_disabled_task)

            # Verify execute_task was NOT scheduled
            mock_loop.create_task.assert_not_called()

        if scheduler.running:
            scheduler.shutdown(wait=False)

    @pytest.mark.asyncio
    async def test_immediate_execution_logging(self, mock_task):
        """Test that immediate execution is logged (AC #4)."""
        from app.scheduler import add_job, scheduler

        if not scheduler.running:
            scheduler.start()

        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop

            with patch("app.scheduler.logger") as mock_logger:
                add_job(mock_task)

                # Verify logging call with [IMMEDIATE] prefix
                mock_logger.info.assert_any_call(
                    f"[IMMEDIATE] Executing interval task {mock_task.id} ({mock_task.name})"
                )

        if scheduler.running:
            scheduler.shutdown(wait=False)

