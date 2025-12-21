"""Task Service Layer.

Provides CRUD operations for Task entities with API key encryption.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.utils.security import encrypt_api_key


async def create_task(session: AsyncSession, task_data: TaskCreate) -> Task:
    """Create a new task with encrypted API key.

    Args:
        session: Async database session.
        task_data: Validated task creation data.

    Returns:
        Created Task instance.
    """
    # Encrypt API key before storage
    encrypted_key = encrypt_api_key(task_data.api_key)

    task = Task(
        name=task_data.name,
        api_endpoint=task_data.api_endpoint,
        api_key=encrypted_key,  # Store encrypted
        schedule_type=task_data.schedule_type,
        interval_minutes=task_data.interval_minutes,
        fixed_time=task_data.fixed_time,
        message_content=task_data.message_content,
        enabled=task_data.enabled,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: int) -> Task | None:
    """Get a task by ID.

    Args:
        session: Async database session.
        task_id: Task ID.

    Returns:
        Task if found, None otherwise.
    """
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks(session: AsyncSession) -> list[Task]:
    """Get all tasks.

    Args:
        session: Async database session.

    Returns:
        List of all Task instances.
    """
    result = await session.execute(select(Task).order_by(Task.id))
    return list(result.scalars().all())


async def update_task(
    session: AsyncSession, task: Task, task_data: TaskUpdate
) -> Task:
    """Update an existing task.

    Only non-None fields in task_data are updated.
    API key is encrypted if provided.

    Args:
        session: Async database session.
        task: Existing Task instance to update.
        task_data: Validated update data.

    Returns:
        Updated Task instance.
    """
    update_data = task_data.model_dump(exclude_unset=True)

    # Encrypt API key if being updated
    if "api_key" in update_data and update_data["api_key"] is not None:
        update_data["api_key"] = encrypt_api_key(update_data["api_key"])

    for field, value in update_data.items():
        setattr(task, field, value)

    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    """Delete a task.

    Args:
        session: Async database session.
        task: Task instance to delete.
    """
    await session.delete(task)
    await session.commit()
