"""Task CRUD API Routes.

REST API endpoints for task management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Task, ExecutionLog
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, ExecutionLogResponse
from app.services import task_service
from app.web.auth import require_auth_api
from app.scheduler import add_job, reschedule_job
from loguru import logger

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Create a new task."""
    task = await task_service.create_task(session, task_data)

    # Register with scheduler (wrapped in try-except to handle failures)
    try:
        add_job(task)
    except Exception as e:
        logger.error(f"Failed to register task {task.id} with scheduler: {e}")
        # Task is saved, will be registered on next startup

    return task


@router.get("", response_model=list[TaskResponse])
async def get_tasks(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Get all tasks."""
    return await task_service.get_tasks(session)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Get a task by ID."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Update an existing task."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate schedule configuration consistency
    # Need to merge existing values with update data
    update_dict = task_data.model_dump(exclude_unset=True)
    new_schedule_type = update_dict.get("schedule_type", task.schedule_type)
    new_interval_minutes = update_dict.get("interval_minutes", task.interval_minutes)
    new_interval_seconds = update_dict.get("interval_seconds", task.interval_seconds)
    new_fixed_time = update_dict.get("fixed_time", task.fixed_time)

    if new_schedule_type == "interval":
        # At least one of interval_minutes or interval_seconds must be > 0
        minutes = new_interval_minutes or 0
        seconds = new_interval_seconds or 0
        if minutes <= 0 and seconds <= 0:
            raise HTTPException(
                status_code=400,
                detail="interval_minutes or interval_seconds must be greater than 0 when schedule_type is 'interval'"
            )
    if new_schedule_type == "fixed_time" and new_fixed_time is None:
        raise HTTPException(
            status_code=400,
            detail="fixed_time is required when schedule_type is 'fixed_time'"
        )

    # Clear the unused schedule field when schedule_type changes (AC #8 consistency)
    if "schedule_type" in update_dict:
        if new_schedule_type == "interval" and task.schedule_type != "interval":
            # Switching to interval: clear fixed_time
            update_dict["fixed_time"] = None
        elif new_schedule_type == "fixed_time" and task.schedule_type != "fixed_time":
            # Switching to fixed_time: clear interval_minutes and interval_seconds
            update_dict["interval_minutes"] = None
            update_dict["interval_seconds"] = None

        # Create a new TaskUpdate with the modified data
        task_data = TaskUpdate(**update_dict)

    updated_task = await task_service.update_task(session, task, task_data)

    # Re-register with scheduler
    try:
        reschedule_job(updated_task)
    except Exception as e:
        logger.error(f"Failed to reschedule task {task_id} with scheduler: {e}")
        # Task is updated, will be re-registered on next startup

    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Delete a task."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await task_service.delete_task(session, task)
    return None


@router.get("/{task_id}/logs", response_model=list[ExecutionLogResponse])
async def get_task_logs(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="Number of logs to return (1-100)"),
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),
):
    """Get execution logs for a specific task.

    Returns logs ordered by execution time (newest first).
    Default limit is 50 records, maximum is 100.
    """
    # Check task exists
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Query logs
    result = await session.execute(
        select(ExecutionLog)
        .where(ExecutionLog.task_id == task_id)
        .order_by(desc(ExecutionLog.executed_at))
        .limit(limit)
    )
    logs = result.scalars().all()

    return logs
