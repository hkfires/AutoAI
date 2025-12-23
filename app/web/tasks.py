"""Web routes for task management UI.

Server-side rendered pages using Jinja2 templates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select, desc, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from loguru import logger

from app.database import get_session
from app.models import Task, ExecutionLog
from app.schemas import TaskCreate, TaskUpdate
from app.services import task_service
from app.scheduler import add_job, remove_job, reschedule_job
from app.web.auth import render_template, require_auth_web

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def list_tasks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
    message: Optional[str] = None,
    message_type: str = "success",
):
    """Display task list page."""
    # Subquery to get max executed_at per task (single query, avoids N+1)
    last_exec_subquery = (
        select(
            ExecutionLog.task_id,
            func.max(ExecutionLog.executed_at).label("last_executed_at")
        )
        .group_by(ExecutionLog.task_id)
        .subquery()
    )

    # Get all tasks with last execution time in single query
    result = await session.execute(
        select(Task, last_exec_subquery.c.last_executed_at)
        .outerjoin(last_exec_subquery, Task.id == last_exec_subquery.c.task_id)
        .order_by(Task.id)
    )
    rows = result.all()

    # Build task list
    task_list = []
    for task, last_executed_at in rows:
        task_dict = {
            "id": task.id,
            "name": task.name,
            "schedule_type": task.schedule_type,
            "interval_minutes": task.interval_minutes,
            "fixed_time": task.fixed_time,
            "enabled": task.enabled,
            "last_executed_at": last_executed_at.strftime("%Y-%m-%d %H:%M")
                               if last_executed_at else None,
        }
        task_list.append(task_dict)

    return render_template(
        request,
        "tasks/list.html",
        {"tasks": task_list, "message": message, "message_type": message_type},
    )


@router.get("/tasks/new")
async def new_task_form(request: Request, _: bool = Depends(require_auth_web)):
    """Display new task form."""
    return render_template(
        request,
        "tasks/form.html",
        {"task": None, "action_url": "/tasks/new"},
    )


@router.post("/tasks/new")
async def create_task(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
    name: str = Form(...),
    api_endpoint: str = Form(...),
    api_key: str = Form(...),
    schedule_type: str = Form(...),
    interval_minutes: Optional[int] = Form(None),
    fixed_time: Optional[str] = Form(None),
    message_content: str = Form(...),
    enabled: Optional[str] = Form(None),
):
    """Handle new task form submission."""
    # Build form data dict to preserve on error
    form_data = {
        "name": name,
        "api_endpoint": api_endpoint,
        "schedule_type": schedule_type,
        "interval_minutes": interval_minutes,
        "fixed_time": fixed_time,
        "message_content": message_content,
        "enabled": enabled == "true",
    }

    try:
        # Build TaskCreate schema
        task_data = TaskCreate(
            name=name,
            api_endpoint=api_endpoint,
            api_key=api_key,
            schedule_type=schedule_type,
            interval_minutes=interval_minutes,
            fixed_time=fixed_time,
            message_content=message_content,
            enabled=enabled == "true",
        )

        # Create task
        task = await task_service.create_task(session, task_data)
        logger.info(f"Created task {task.id}: {task.name}")

        # Register with scheduler (wrapped in try-except to handle failures)
        try:
            add_job(task)
        except Exception as e:
            logger.error(f"Failed to register task {task.id} with scheduler: {e}")
            # Task is saved, will be registered on next startup

        return RedirectResponse(url="/?message=任务创建成功", status_code=303)

    except (ValueError, ValidationError) as e:
        error_msg = str(e) if isinstance(e, ValueError) else str(e.errors())
        return render_template(
            request,
            "tasks/form.html",
            {"task": form_data, "action_url": "/tasks/new",
             "message": error_msg, "message_type": "error"},
            status_code=400,
        )

    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"Database error creating task: {e}")
        await session.rollback()
        return render_template(
            request,
            "tasks/form.html",
            {"task": form_data, "action_url": "/tasks/new",
             "message": "数据库错误，请检查任务名称是否重复", "message_type": "error"},
            status_code=400,
        )


@router.get("/tasks/{task_id}/edit")
async def edit_task_form(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
):
    """Display edit task form."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        return RedirectResponse(url="/?message=任务不存在&message_type=error", status_code=303)

    return render_template(
        request,
        "tasks/form.html",
        {"task": task, "action_url": f"/tasks/{task_id}/edit"},
    )


@router.post("/tasks/{task_id}/edit")
async def update_task(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
    name: str = Form(...),
    api_endpoint: str = Form(...),
    api_key: Optional[str] = Form(None),
    schedule_type: str = Form(...),
    interval_minutes: Optional[int] = Form(None),
    fixed_time: Optional[str] = Form(None),
    message_content: str = Form(...),
    enabled: Optional[str] = Form(None),
):
    """Handle edit task form submission."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        return RedirectResponse(url="/?message=任务不存在&message_type=error", status_code=303)

    # Build form data dict to preserve on error
    form_data = {
        "id": task_id,
        "name": name,
        "api_endpoint": api_endpoint,
        "schedule_type": schedule_type,
        "interval_minutes": interval_minutes,
        "fixed_time": fixed_time,
        "message_content": message_content,
        "enabled": enabled == "true",
    }

    try:
        # Build update data (only include api_key if provided)
        update_dict = {
            "name": name,
            "api_endpoint": api_endpoint,
            "schedule_type": schedule_type,
            "interval_minutes": interval_minutes if schedule_type == "interval" else None,
            "fixed_time": fixed_time if schedule_type == "fixed_time" else None,
            "message_content": message_content,
            "enabled": enabled == "true",
        }

        # Only update API key if new value provided
        if api_key and api_key.strip():
            update_dict["api_key"] = api_key

        task_data = TaskUpdate(**update_dict)

        # Update task
        updated_task = await task_service.update_task(session, task, task_data)
        logger.info(f"Updated task {task_id}: {updated_task.name}")

        # Reschedule with scheduler (wrapped in try-except)
        try:
            reschedule_job(updated_task)
        except Exception as e:
            logger.error(f"Failed to reschedule task {task_id}: {e}")

        return RedirectResponse(url="/?message=任务更新成功", status_code=303)

    except (ValueError, ValidationError) as e:
        error_msg = str(e) if isinstance(e, ValueError) else str(e.errors())
        return render_template(
            request,
            "tasks/form.html",
            {"task": form_data, "action_url": f"/tasks/{task_id}/edit",
             "message": error_msg, "message_type": "error"},
            status_code=400,
        )

    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"Database error updating task {task_id}: {e}")
        await session.rollback()
        return render_template(
            request,
            "tasks/form.html",
            {"task": form_data, "action_url": f"/tasks/{task_id}/edit",
             "message": "数据库错误，请重试", "message_type": "error"},
            status_code=400,
        )


@router.post("/tasks/{task_id}/delete")
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
):
    """Handle task deletion."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        return RedirectResponse(url="/?message=任务不存在&message_type=error", status_code=303)

    task_name = task.name

    # Remove from scheduler first
    remove_job(task_id)

    # Delete from database (cascade deletes logs)
    await task_service.delete_task(session, task)
    logger.info(f"Deleted task {task_id}: {task_name}")

    return RedirectResponse(url=f"/?message=任务「{task_name}」已删除", status_code=303)


@router.get("/tasks/{task_id}/logs")
async def view_task_logs(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
):
    """Display task execution logs page."""
    # Get task
    task = await session.get(Task, task_id)
    if task is None:
        return RedirectResponse(
            url="/?message=任务不存在&message_type=error",
            status_code=303
        )

    # Get logs (newest first, limit 50)
    result = await session.execute(
        select(ExecutionLog)
        .where(ExecutionLog.task_id == task_id)
        .order_by(desc(ExecutionLog.executed_at))
        .limit(50)
    )
    logs = result.scalars().all()

    return render_template(
        request,
        "tasks/logs.html",
        {"task": task, "logs": logs},
    )
