"""APScheduler Configuration and Task Management.

Implements scheduled task execution using APScheduler with AsyncIOScheduler.
Provides task registration, execution, and dynamic job management.
"""

import asyncio
from datetime import datetime, timezone

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlalchemy import select

from app.database import get_session_maker
from app.models import Task, ExecutionLog
from app.services.openai_service import send_message, OpenAIServiceError
from app.utils.security import decrypt_api_key, mask_api_key

# Global scheduler instance with asyncio support
scheduler = AsyncIOScheduler()

# Maximum concurrent instances per job (effectively unlimited for fire-and-forget mode)
MAX_CONCURRENT_INSTANCES = 999999

# Track pending immediate executions for cleanup
_pending_immediate_tasks: set[asyncio.Task] = set()


async def start_scheduler() -> None:
    """Start the scheduler and register all enabled tasks.

    This function should be called during application startup.
    It loads all enabled tasks from the database and starts the scheduler.
    """
    # Register all enabled tasks from database
    await register_all_tasks()

    # Start the scheduler (synchronous call)
    scheduler.start()
    logger.info("Scheduler started successfully")


async def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully.

    This function should be called during application shutdown.
    Uses wait=False for async compatibility.
    """
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shutdown complete")


async def register_all_tasks() -> None:
    """Load and register all enabled tasks from database.

    Queries the database for all tasks with enabled=True and
    registers each one with the scheduler.
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Task).where(Task.enabled == True)  # noqa: E712
        )
        tasks = result.scalars().all()

        for task in tasks:
            register_task(task)

        logger.info(f"Registered {len(tasks)} enabled tasks")


def register_task(task: Task) -> None:
    """Register a single task with the scheduler.

    Args:
        task: The Task model instance to register.

    If the task is disabled, it will be skipped.
    If a job with the same ID exists, it will be replaced.
    """
    job_id = f"task_{task.id}"

    # Remove existing job if present
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        pass  # Job doesn't exist, continue

    if not task.enabled:
        logger.debug(f"Task {task.id} is disabled, skipping registration")
        return

    # Create trigger based on schedule type
    if task.schedule_type == "interval":
        total_seconds = (task.interval_minutes or 0) * 60 + (task.interval_seconds or 0)
        trigger = IntervalTrigger(seconds=total_seconds)
        # Format schedule description
        mins, secs = divmod(total_seconds, 60)
        if mins and secs:
            schedule_desc = f"every {mins}m {secs}s"
        elif mins:
            schedule_desc = f"every {mins} minutes"
        else:
            schedule_desc = f"every {secs} seconds"
    elif task.schedule_type == "fixed_time":
        hour, minute = map(int, task.fixed_time.split(":"))
        trigger = CronTrigger(hour=hour, minute=minute)
        schedule_desc = f"daily at {task.fixed_time}"
    else:
        logger.error(f"Unknown schedule type: {task.schedule_type}")
        return

    scheduler.add_job(
        execute_task,
        trigger=trigger,
        id=job_id,
        args=[task.id],
        replace_existing=True,
        coalesce=True,
        max_instances=MAX_CONCURRENT_INSTANCES,
    )

    logger.info(f"Registered task {task.id} ({task.name}): {schedule_desc}")


async def execute_task(task_id: int) -> None:
    """Execute a scheduled task.

    Args:
        task_id: The ID of the task to execute.

    This function:
    1. Loads the task from the database
    2. Checks if the task is still enabled
    3. Calls the OpenAI API with the task's message
    4. Records the execution result in ExecutionLog
    """
    logger.info(f"Executing task {task_id}")

    session_maker = get_session_maker()
    async with session_maker() as session:
        # Get task from database
        result = await session.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if task is None:
            logger.error(f"Task {task_id} not found in database")
            return

        # Check if task is still enabled
        if not task.enabled:
            logger.info(f"Task {task_id} is disabled, skipping execution")
            return  # Don't create ExecutionLog, just return

        # Execute the task
        masked_key = mask_api_key(task.api_key)
        logger.info(f"Calling OpenAI API for task {task_id} (key: {masked_key})")

        # Must set executed_at field (model has no default value)
        execution_log = ExecutionLog(
            task_id=task_id,
            executed_at=datetime.now(timezone.utc),
        )

        try:
            # Decrypt API key and call OpenAI service
            plain_api_key = decrypt_api_key(task.api_key)
            response = await send_message(
                api_endpoint=task.api_endpoint,
                api_key=plain_api_key,
                message_content=task.message_content,
                model=task.model,
            )

            # Success - record result
            execution_log.status = "success"
            execution_log.response_summary = (
                f"{response.response_summary} (耗时: {response.response_time_ms}ms)"
            )
            logger.info(
                f"Task {task_id} executed successfully in {response.response_time_ms}ms"
            )

        except OpenAIServiceError as e:
            # Failed - record error
            execution_log.status = "failed"
            execution_log.error_message = str(e.message)
            logger.error(f"Task {task_id} failed: {e.message}")

        except Exception as e:
            # Unexpected error
            execution_log.status = "failed"
            execution_log.error_message = f"Unexpected error: {str(e)}"
            logger.exception(f"Task {task_id} failed with unexpected error")

        # Save execution log
        session.add(execution_log)
        await session.commit()
        logger.debug(f"Saved execution log for task {task_id}")


def add_job(task: Task) -> None:
    """Dynamically add a new task to the scheduler.

    Args:
        task: The Task model instance to add.
    """
    register_task(task)

    # Immediately execute interval tasks when they are created
    if task.enabled and task.schedule_type == "interval":
        logger.info(f"[IMMEDIATE] Executing interval task {task.id} ({task.name})")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning(
                f"No event loop running, cannot immediately execute task {task.id}"
            )
            return

        # Create task with exception handling and cleanup
        async def execute_with_cleanup():
            try:
                await execute_task(task.id)
            except Exception as e:
                logger.exception(f"Immediate execution failed for task {task.id}: {e}")
            finally:
                current_task = asyncio.current_task()
                if current_task:
                    _pending_immediate_tasks.discard(current_task)

        task_ref = loop.create_task(execute_with_cleanup())
        _pending_immediate_tasks.add(task_ref)


def remove_job(task_id: int) -> None:
    """Dynamically remove a task from the scheduler.

    Args:
        task_id: The ID of the task to remove.
    """
    job_id = f"task_{task_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed task {task_id} from scheduler")
    except JobLookupError:
        logger.debug(f"Task {task_id} not found in scheduler")


def reschedule_job(task: Task) -> None:
    """Update a task's schedule in the scheduler.

    Args:
        task: The Task model instance with updated schedule.

    This function removes the existing job and re-registers it
    with the new schedule. If the task is disabled, the job
    will be removed.
    """
    register_task(task)  # register_task handles removal and re-registration

    # Immediately execute interval tasks when they are updated
    if task.enabled and task.schedule_type == "interval":
        logger.info(f"[IMMEDIATE] Executing interval task {task.id} ({task.name})")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning(
                f"No event loop running, cannot immediately execute task {task.id}"
            )
            return

        # Create task with exception handling and cleanup
        async def execute_with_cleanup():
            try:
                await execute_task(task.id)
            except Exception as e:
                logger.exception(f"Immediate execution failed for task {task.id}: {e}")
            finally:
                current_task = asyncio.current_task()
                if current_task:
                    _pending_immediate_tasks.discard(current_task)

        task_ref = loop.create_task(execute_with_cleanup())
        _pending_immediate_tasks.add(task_ref)
