"""Web routes for task management UI.

Server-side rendered pages using Jinja2 templates.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select, desc, func, case
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_session
from app.models import Task, ExecutionLog
from app.schemas import TaskCreate, TaskUpdate
from app.services import task_service
from app.scheduler import add_job, remove_job, reschedule_job
from app.web.auth import render_template, require_auth_web

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


async def get_dashboard_stats(session: AsyncSession) -> dict:
    """Get dashboard statistics for the task list page."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Query for task counts
    task_query = select(
        func.count(Task.id).label("total"),
        func.sum(case((Task.enabled == True, 1), else_=0)).label("enabled"),
    )

    # Query for today's execution stats
    exec_query = select(
        func.count(ExecutionLog.id).label("count"),
        func.sum(case((ExecutionLog.status == "success", 1), else_=0)).label("success"),
    ).where(ExecutionLog.executed_at >= today_start)

    # Execute both queries in parallel
    task_result, exec_result = await asyncio.gather(
        session.execute(task_query),
        session.execute(exec_query),
    )

    task_stats = task_result.one()
    exec_stats = exec_result.one()

    # Calculate success rate (format in backend to avoid frontend division by zero)
    today_count = exec_stats.count or 0
    today_success = exec_stats.success or 0
    success_rate = f"{int(today_success / today_count * 100)}%" if today_count > 0 else "--"

    return {
        "total_tasks": task_stats.total or 0,
        "enabled_tasks": int(task_stats.enabled or 0),
        "today_executions": today_count,
        "today_success_rate": success_rate,
    }


@router.get("/")
async def list_tasks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
    message: Optional[str] = None,
    message_type: str = "success",
):
    """Display task list page with dashboard stats."""
    # Get dashboard statistics
    stats = await get_dashboard_stats(session)

    # Use window function to get each task's latest execution (both time and status)
    # Performance Note: For large datasets, consider adding index on (task_id, executed_at DESC)
    last_exec_subquery = (
        select(
            ExecutionLog.task_id,
            ExecutionLog.executed_at.label("last_executed_at"),
            ExecutionLog.status.label("last_status"),
            func.row_number().over(
                partition_by=ExecutionLog.task_id,
                order_by=ExecutionLog.executed_at.desc()
            ).label("rn")
        )
        .subquery()
    )

    # Only take rn=1 (most recent execution per task)
    latest_exec = (
        select(
            last_exec_subquery.c.task_id,
            last_exec_subquery.c.last_executed_at,
            last_exec_subquery.c.last_status,
        )
        .where(last_exec_subquery.c.rn == 1)
        .subquery()
    )

    # Get all tasks with last execution time and status in single query
    result = await session.execute(
        select(Task, latest_exec.c.last_executed_at, latest_exec.c.last_status)
        .outerjoin(latest_exec, Task.id == latest_exec.c.task_id)
        .order_by(Task.id)
    )
    rows = result.all()

    # Build task list
    task_list = []
    for task, last_executed_at, last_status in rows:
        task_dict = {
            "id": task.id,
            "name": task.name,
            "schedule_type": task.schedule_type,
            "interval_minutes": task.interval_minutes,
            "fixed_time": task.fixed_time,
            "enabled": task.enabled,
            "last_executed_at": last_executed_at.strftime("%Y-%m-%d %H:%M")
                               if last_executed_at else None,
            "last_execution_status": last_status,  # 'success', 'failed', or None
        }
        task_list.append(task_dict)

    return render_template(
        request,
        "tasks/list.html",
        {"tasks": task_list, "stats": stats, "message": message, "message_type": message_type},
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


async def get_log_stats(session: AsyncSession, task_id: int) -> dict:
    """Get execution statistics for a specific task."""
    # Total and success count
    stats_query = select(
        func.count(ExecutionLog.id).label("total"),
        func.sum(case((ExecutionLog.status == "success", 1), else_=0)).label("success"),
    ).where(ExecutionLog.task_id == task_id)

    stats_result = await session.execute(stats_query)
    stats = stats_result.one()

    total = stats.total or 0
    success = int(stats.success or 0)
    success_rate = f"{int(success / total * 100)}%" if total > 0 else "--"

    # Last 7 days stats
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_query = select(
        func.count(ExecutionLog.id).label("count"),
        func.sum(case((ExecutionLog.status == "success", 1), else_=0)).label("success"),
    ).where(
        ExecutionLog.task_id == task_id,
        ExecutionLog.executed_at >= seven_days_ago,
    )

    recent_result = await session.execute(recent_query)
    recent = recent_result.one()

    recent_count = recent.count or 0
    recent_success = int(recent.success or 0)
    recent_trend = f"共执行 {recent_count} 次，成功 {recent_success} 次" if recent_count > 0 else "暂无执行记录"

    return {
        "total_executions": total,
        "success_rate": success_rate,
        "recent_trend": recent_trend,
    }


@router.get("/tasks/{task_id}/logs")
async def view_task_logs(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),
    status: Optional[str] = None,  # success | failed | None
    start_date: Optional[str] = None,  # YYYY-MM-DD
    end_date: Optional[str] = None,  # YYYY-MM-DD
    page: int = 1,
):
    """Display task execution logs with filtering and pagination."""
    task = await session.get(Task, task_id)
    if task is None:
        return RedirectResponse(url="/?message=任务不存在&message_type=error", status_code=303)

    # Build base query
    query = select(ExecutionLog).where(ExecutionLog.task_id == task_id)

    # Apply status filter
    if status in ("success", "failed"):
        query = query.where(ExecutionLog.status == status)

    # Apply date range filter
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.where(ExecutionLog.executed_at >= start_dt)
        except ValueError:
            pass  # Invalid date format, ignore

    if end_date:
        try:
            # End date is inclusive, so add 1 day
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = end_dt + timedelta(days=1)
            query = query.where(ExecutionLog.executed_at < end_dt)
        except ValueError:
            pass

    # Count total for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await session.execute(count_query)).scalar() or 0

    # Pagination
    page_size = 20
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    offset = (page - 1) * page_size

    # Get paginated logs
    result = await session.execute(
        query.order_by(desc(ExecutionLog.executed_at))
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    # Get statistics
    log_stats = await get_log_stats(session, task_id)

    return render_template(
        request,
        "tasks/logs.html",
        {
            "task": task,
            "logs": logs,
            "stats": log_stats,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "filters": {
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            },
        },
    )
