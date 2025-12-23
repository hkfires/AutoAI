# Story 2.5: 任务管理 Web 界面

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 用户,
I want 通过 Web 界面管理定时任务,
So that 我可以方便地配置 API 信息、定时规则和消息内容。

## Acceptance Criteria

1. **Given** 用户访问管理界面
   **When** 打开首页
   **Then** 显示所有任务列表，包含：名称、调度规则、启用状态、最后执行时间

2. **Given** 用户点击"新建任务"
   **When** 填写任务表单
   **Then** 可以配置：
   - 任务名称
   - OpenAI API 端点地址
   - API 密钥（输入框类型为 password）
   - 调度类型（间隔/固定时间）
   - 间隔分钟数 或 固定时间
   - 消息内容
   - 启用/禁用开关

3. **Given** 用户提交任务表单
   **When** 表单验证通过
   **Then** 任务保存到数据库
   **And** 调度器立即加载新任务
   **And** 页面跳转到任务列表并显示成功消息

4. **Given** 用户编辑现有任务
   **When** 修改配置并保存
   **Then** 更新数据库中的任务配置
   **And** 调度器重新加载该任务的调度规则

5. **Given** 用户删除任务
   **When** 确认删除
   **Then** 从数据库删除任务及其执行日志
   **And** 调度器移除该任务的调度

6. **And** 界面使用 Jinja2 模板服务端渲染
7. **And** 界面简洁实用，无需复杂样式

## Tasks / Subtasks

- [x] Task 1: 创建 Jinja2 模板基础设施 (AC: #6)
  - [x] 1.1 创建 `templates/` 目录结构
  - [x] 1.2 创建 `templates/base.html` 基础布局模板（包含简洁 CSS）
  - [x] 1.3 在 `main.py` 配置 Jinja2 模板引擎
  - [x] 1.4 配置静态文件目录（如需要）

- [x] Task 2: 实现任务列表页面 (AC: #1)
  - [x] 2.1 创建 `templates/tasks/list.html` 任务列表模板
  - [x] 2.2 创建 `app/web/tasks.py` Web 路由模块
  - [x] 2.3 实现 `GET /` 首页路由，渲染任务列表
  - [x] 2.4 显示任务名称、调度规则、启用状态
  - [x] 2.5 查询并显示最后执行时间（从 ExecutionLog）
  - [x] 2.6 添加"新建任务"、"编辑"、"删除"操作按钮（日志按钮移至 Story 2.6）

- [x] Task 3: 实现任务创建页面 (AC: #2, #3)
  - [x] 3.1 创建 `templates/tasks/form.html` 任务表单模板
  - [x] 3.2 实现 `GET /tasks/new` 显示新建表单
  - [x] 3.3 实现 `POST /tasks/new` 处理表单提交
  - [x] 3.4 表单字段：name, api_endpoint, api_key(password), schedule_type, interval_minutes, fixed_time, message_content, enabled
  - [x] 3.5 使用 JavaScript 动态显示/隐藏间隔或固定时间字段
  - [x] 3.6 调用现有 `task_service.create_task()` 保存任务
  - [x] 3.7 调用 `scheduler.add_job()` 注册到调度器
  - [x] 3.8 重定向到列表页并显示成功消息（Flash Message）

- [x] Task 4: 实现任务编辑页面 (AC: #4)
  - [x] 4.1 实现 `GET /tasks/{id}/edit` 显示编辑表单（复用 form.html）
  - [x] 4.2 实现 `POST /tasks/{id}/edit` 处理更新
  - [x] 4.3 API 密钥字段可选更新（留空则保持原值）
  - [x] 4.4 调用 `task_service.update_task()` 更新数据库
  - [x] 4.5 调用 `scheduler.reschedule_job()` 更新调度器
  - [x] 4.6 重定向到列表页并显示成功消息

- [x] Task 5: 实现任务删除功能 (AC: #5)
  - [x] 5.1 实现 `POST /tasks/{id}/delete` 处理删除
  - [x] 5.2 调用 `task_service.delete_task()` 删除任务（级联删除日志）
  - [x] 5.3 调用 `scheduler.remove_job()` 从调度器移除
  - [x] 5.4 重定向到列表页并显示成功消息
  - [x] 5.5 可选：添加 JavaScript 确认对话框

- [x] Task 6: 编写测试 (AC: 全部)
  - [x] 6.1 创建 `tests/test_web_tasks.py`
  - [x] 6.2 测试首页渲染任务列表
  - [x] 6.3 测试新建任务表单提交
  - [x] 6.4 测试编辑任务表单提交
  - [x] 6.5 测试删除任务
  - [x] 6.6 测试表单验证错误处理

## Dev Notes

### Critical Implementation Notes

> **日志页面路由说明：** 任务列表模板中包含"查看日志"按钮（链接到 `/tasks/{id}/logs`），该路由的完整实现是 **Story 2.6** 的范围。本 Story 中可选择：
> 1. 暂时移除日志按钮（推荐）
> 2. 或添加占位路由返回"功能开发中"页面

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **模板引擎** - Jinja2 服务端渲染，FastAPI 原生支持
2. **简洁 UI** - Template-Based UI，无需前后端分离
3. **异步架构** - 所有路由使用 async/await
4. **命名规范** - snake_case（函数、变量、文件）
5. **日志系统** - 使用 loguru 记录操作

**相关需求支持：**
- FR1-FR5: 任务配置（API 端点、密钥、定时规则、消息内容、启用状态）
- 架构决策: Template-Based UI: Jinja2 服务端渲染

### Technical Requirements

**项目现有代码基础（Story 2.1-2.4 已完成）：**

1. **API 路由** - `app/api/tasks.py` 已有完整 CRUD API
2. **服务层** - `app/services/task_service.py` 提供任务 CRUD 操作
3. **调度器** - `app/scheduler.py` 提供 `add_job()`, `remove_job()`, `reschedule_job()`
4. **数据模型** - `app/models.py` 定义了 Task 和 ExecutionLog
5. **Pydantic Schemas** - `app/schemas.py` 已有验证逻辑
6. **已安装依赖** - jinja2>=3.1.0, python-multipart>=0.0.6 已在 requirements.txt
7. **数据库依赖** - `app/database.py` 需提供 `get_session` 依赖注入函数

**关键代码位置：**

| 模块 | 文件路径 | 用途 |
|------|----------|------|
| 任务服务 | `app/services/task_service.py` | CRUD 操作 |
| 调度器 | `app/scheduler.py` | 任务注册/更新/删除 |
| 数据模型 | `app/models.py` | Task, ExecutionLog ORM |
| Schemas | `app/schemas.py` | TaskCreate, TaskUpdate 验证 |
| 数据库 | `app/database.py` | get_session 依赖注入 |
| 主入口 | `app/main.py` | FastAPI 应用配置 |

**get_session 依赖注入（如未存在需添加到 database.py）：**

```python
# app/database.py 添加
from typing import AsyncGenerator

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for async database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session
```

### Jinja2 Template Configuration

**在 main.py 中配置模板引擎：**

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# 配置模板目录
templates = Jinja2Templates(directory="templates")

# 可选：配置静态文件
# app.mount("/static", StaticFiles(directory="static"), name="static")
```

**模板目录结构：**

```
templates/
├── base.html           # 基础布局模板
└── tasks/
    ├── list.html       # 任务列表页面
    └── form.html       # 新建/编辑表单（复用）
```

**创建目录命令（Windows/Unix）：**
```bash
# Unix/Mac/Git Bash
mkdir -p templates/tasks

# Windows CMD
mkdir templates\tasks
```

### Base Template Pattern

**templates/base.html 基础布局：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AutoAI{% endblock %}</title>
    <style>
        /* 简洁实用的基础样式 */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               line-height: 1.6; padding: 20px; max-width: 1200px; margin: 0 auto; }
        h1 { margin-bottom: 20px; color: #333; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: 600; }
        tr:hover { background-color: #f5f5f5; }
        .btn { display: inline-block; padding: 8px 16px; margin: 2px; border: none;
               border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-secondary { background-color: #6c757d; color: white; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .form-group textarea { min-height: 100px; resize: vertical; }
        .alert { padding: 12px 20px; margin-bottom: 20px; border-radius: 4px; }
        .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status-enabled { color: #28a745; }
        .status-disabled { color: #dc3545; }
        .hidden { display: none; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <nav style="margin-bottom: 20px;">
        <a href="/" style="font-size: 1.5em; text-decoration: none; color: #333;">🤖 AutoAI</a>
    </nav>

    {% if message %}
    <div class="alert alert-{{ message_type|default('success') }}">{{ message }}</div>
    {% endif %}

    {% block content %}{% endblock %}

    {% block scripts %}{% endblock %}
</body>
</html>
```

### Task List Template Pattern

**templates/tasks/list.html 任务列表：**

```html
{% extends "base.html" %}

{% block title %}任务列表 - AutoAI{% endblock %}

{% block content %}
<h1>任务列表</h1>

<a href="/tasks/new" class="btn btn-primary" style="margin-bottom: 20px;">+ 新建任务</a>

<table>
    <thead>
        <tr>
            <th>任务名称</th>
            <th>调度规则</th>
            <th>状态</th>
            <th>最后执行</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody>
        {% for task in tasks %}
        <tr>
            <td>{{ task.name }}</td>
            <td>
                {% if task.schedule_type == 'interval' %}
                    每 {{ task.interval_minutes }} 分钟
                {% else %}
                    每天 {{ task.fixed_time }}
                {% endif %}
            </td>
            <td>
                {% if task.enabled %}
                    <span class="status-enabled">✓ 启用</span>
                {% else %}
                    <span class="status-disabled">✗ 禁用</span>
                {% endif %}
            </td>
            <td>{{ task.last_executed_at or '从未执行' }}</td>
            <td>
                <a href="/tasks/{{ task.id }}/edit" class="btn btn-secondary">编辑</a>
                <a href="/tasks/{{ task.id }}/logs" class="btn btn-secondary">日志</a>
                <form action="/tasks/{{ task.id }}/delete" method="POST" style="display: inline;">
                    <button type="submit" class="btn btn-danger"
                            onclick="return confirm('确定要删除任务「{{ task.name }}」吗？')">删除</button>
                </form>
            </td>
        </tr>
        {% else %}
        <tr>
            <td colspan="5" style="text-align: center; color: #666;">暂无任务，点击"新建任务"创建第一个</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

### Task Form Template Pattern

**templates/tasks/form.html 表单（新建/编辑复用）：**

```html
{% extends "base.html" %}

{% block title %}{% if task %}编辑任务{% else %}新建任务{% endif %} - AutoAI{% endblock %}

{% block content %}
<h1>{% if task %}编辑任务{% else %}新建任务{% endif %}</h1>

<form method="POST" action="{{ action_url }}">
    <div class="form-group">
        <label for="name">任务名称 *</label>
        <input type="text" id="name" name="name" value="{{ task.name if task else '' }}" required
               maxlength="100" placeholder="例如：每日问候">
    </div>

    <div class="form-group">
        <label for="api_endpoint">API 端点地址 *</label>
        <input type="url" id="api_endpoint" name="api_endpoint"
               value="{{ task.api_endpoint if task else 'https://api.openai.com/v1/chat/completions' }}"
               required maxlength="500">
    </div>

    <div class="form-group">
        <label for="api_key">API 密钥 {% if task %}(留空保持原值){% else %}*{% endif %}</label>
        <input type="password" id="api_key" name="api_key"
               placeholder="sk-..." maxlength="500" {% if not task %}required{% endif %}>
    </div>

    <div class="form-group">
        <label for="schedule_type">调度类型 *</label>
        <select id="schedule_type" name="schedule_type" required onchange="toggleScheduleFields()">
            <option value="interval" {% if not task or task.schedule_type == 'interval' %}selected{% endif %}>
                间隔模式
            </option>
            <option value="fixed_time" {% if task and task.schedule_type == 'fixed_time' %}selected{% endif %}>
                固定时间模式
            </option>
        </select>
    </div>

    <div class="form-group" id="interval-group">
        <label for="interval_minutes">间隔分钟数</label>
        <input type="number" id="interval_minutes" name="interval_minutes"
               value="{{ task.interval_minutes if task else 60 }}" min="1" placeholder="60">
    </div>

    <div class="form-group hidden" id="fixed-time-group">
        <label for="fixed_time">固定时间 (HH:MM)</label>
        <input type="time" id="fixed_time" name="fixed_time"
               value="{{ task.fixed_time if task else '09:00' }}">
    </div>

    <div class="form-group">
        <label for="message_content">消息内容 *</label>
        <textarea id="message_content" name="message_content" required
                  placeholder="输入要发送给 AI 的消息...">{{ task.message_content if task else '' }}</textarea>
    </div>

    <div class="form-group">
        <label>
            <input type="checkbox" name="enabled" value="true"
                   {% if not task or task.enabled %}checked{% endif %}>
            启用任务
        </label>
    </div>

    <div style="margin-top: 20px;">
        <button type="submit" class="btn btn-primary">保存</button>
        <a href="/" class="btn btn-secondary">取消</a>
    </div>
</form>
{% endblock %}

{% block scripts %}
<script>
function toggleScheduleFields() {
    const scheduleType = document.getElementById('schedule_type').value;
    const intervalGroup = document.getElementById('interval-group');
    const fixedTimeGroup = document.getElementById('fixed-time-group');

    if (scheduleType === 'interval') {
        intervalGroup.classList.remove('hidden');
        fixedTimeGroup.classList.add('hidden');
        document.getElementById('interval_minutes').required = true;
        document.getElementById('fixed_time').required = false;
    } else {
        intervalGroup.classList.add('hidden');
        fixedTimeGroup.classList.remove('hidden');
        document.getElementById('interval_minutes').required = false;
        document.getElementById('fixed_time').required = true;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', toggleScheduleFields);
</script>
{% endblock %}
```

### Web Routes Implementation Pattern

**app/web/tasks.py Web 路由实现：**

```python
"""Web routes for task management UI.

Server-side rendered pages using Jinja2 templates.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_session
from app.models import Task, ExecutionLog
from app.schemas import TaskCreate, TaskUpdate
from app.services import task_service
from app.scheduler import add_job, remove_job, reschedule_job

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def list_tasks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    message: Optional[str] = None,
    message_type: str = "success",
):
    """Display task list page."""
    # Get all tasks
    result = await session.execute(select(Task).order_by(Task.id))
    tasks = result.scalars().all()

    # Get last execution time for each task
    task_list = []
    for task in tasks:
        last_log = await session.execute(
            select(ExecutionLog)
            .where(ExecutionLog.task_id == task.id)
            .order_by(desc(ExecutionLog.executed_at))
            .limit(1)
        )
        last_log_obj = last_log.scalar_one_or_none()

        task_dict = {
            "id": task.id,
            "name": task.name,
            "schedule_type": task.schedule_type,
            "interval_minutes": task.interval_minutes,
            "fixed_time": task.fixed_time,
            "enabled": task.enabled,
            "last_executed_at": last_log_obj.executed_at.strftime("%Y-%m-%d %H:%M")
                               if last_log_obj else None,
        }
        task_list.append(task_dict)

    return templates.TemplateResponse(
        "tasks/list.html",
        {"request": request, "tasks": task_list, "message": message, "message_type": message_type},
    )


@router.get("/tasks/new")
async def new_task_form(request: Request):
    """Display new task form."""
    return templates.TemplateResponse(
        "tasks/form.html",
        {"request": request, "task": None, "action_url": "/tasks/new"},
    )


@router.post("/tasks/new")
async def create_task(
    request: Request,
    session: AsyncSession = Depends(get_session),
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

        # Register with scheduler
        add_job(task)

        return RedirectResponse(url="/?message=任务创建成功", status_code=303)

    except (ValueError, ValidationError) as e:
        error_msg = str(e) if isinstance(e, ValueError) else str(e.errors())
        return templates.TemplateResponse(
            "tasks/form.html",
            {"request": request, "task": None, "action_url": "/tasks/new",
             "message": error_msg, "message_type": "error"},
            status_code=400,
        )


@router.get("/tasks/{task_id}/edit")
async def edit_task_form(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Display edit task form."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        return RedirectResponse(url="/?message=任务不存在&message_type=error", status_code=303)

    return templates.TemplateResponse(
        "tasks/form.html",
        {"request": request, "task": task, "action_url": f"/tasks/{task_id}/edit"},
    )


@router.post("/tasks/{task_id}/edit")
async def update_task(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
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

        # Reschedule with scheduler
        reschedule_job(updated_task)

        return RedirectResponse(url="/?message=任务更新成功", status_code=303)

    except (ValueError, ValidationError) as e:
        error_msg = str(e) if isinstance(e, ValueError) else str(e.errors())
        return templates.TemplateResponse(
            "tasks/form.html",
            {"request": request, "task": task, "action_url": f"/tasks/{task_id}/edit",
             "message": error_msg, "message_type": "error"},
            status_code=400,
        )


@router.post("/tasks/{task_id}/delete")
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
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
```

### Main.py Integration Pattern

**在 app/main.py 中注册 Web 路由：**

```python
# 在现有导入后添加
from app.web.tasks import router as web_tasks_router

# 在 app.include_router(tasks_router) 后添加
app.include_router(web_tasks_router)
```

**完整的 main.py 修改：**

```diff
 from app.api.tasks import router as tasks_router
+from app.web.tasks import router as web_tasks_router

 # Register API routers
 app.include_router(tasks_router)
+app.include_router(web_tasks_router)
```

### Library/Framework Requirements

**已安装依赖（无需新增）：**

| 库 | 版本 | 用途 |
|----|------|------|
| fastapi | >=0.104.0 | Web 框架 + 模板支持 |
| jinja2 | >=3.1.0 | 模板引擎 |
| python-multipart | >=0.0.6 | 表单解析 |

### File Structure Requirements

**需要创建的文件：**
```
templates/
├── base.html              # 新建：基础布局模板
└── tasks/
    ├── list.html          # 新建：任务列表页面
    └── form.html          # 新建：新建/编辑表单

app/
├── web/                   # 新建：Web 路由目录
│   ├── __init__.py        # 新建：包初始化（空文件或简单导入）
│   └── tasks.py           # 新建：任务管理 Web 路由
└── main.py               # 修改：注册 Web 路由

tests/
└── test_web_tasks.py      # 新建：Web 路由测试
```

**app/web/__init__.py 内容：**
```python
"""Web routes package for server-side rendered pages."""
```

### Testing Requirements

**测试策略：**

使用 pytest + httpx.AsyncClient 测试 Web 页面渲染和表单提交。

```python
# tests/test_web_tasks.py
"""Tests for the web task management UI."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models import Task


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_tasks_page_renders(client):
    """Test that the task list page renders successfully."""
    with patch("app.web.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        mock_get_session.return_value = mock_session

        response = await client.get("/")

        assert response.status_code == 200
        assert "任务列表" in response.text


@pytest.mark.asyncio
async def test_new_task_form_renders(client):
    """Test that the new task form renders successfully."""
    response = await client.get("/tasks/new")

    assert response.status_code == 200
    assert "新建任务" in response.text
    assert "name" in response.text
    assert "api_endpoint" in response.text


@pytest.mark.asyncio
async def test_create_task_success(client):
    """Test successful task creation via form."""
    with patch("app.web.tasks.task_service") as mock_service:
        with patch("app.web.tasks.add_job") as mock_add_job:
            mock_task = MagicMock(id=1, name="Test Task")
            mock_service.create_task = AsyncMock(return_value=mock_task)

            response = await client.post(
                "/tasks/new",
                data={
                    "name": "Test Task",
                    "api_endpoint": "https://api.openai.com/v1/chat/completions",
                    "api_key": "sk-test",
                    "schedule_type": "interval",
                    "interval_minutes": "60",
                    "message_content": "Hello",
                    "enabled": "true",
                },
                follow_redirects=False,
            )

            assert response.status_code == 303
            assert "message=任务创建成功" in response.headers["location"]
            mock_add_job.assert_called_once()
```

### Previous Story Intelligence

**来自 Story 2.4 的经验教训：**

1. **调度器函数** - `add_job()`, `remove_job()`, `reschedule_job()` 已实现
2. **服务层** - `task_service` 处理数据库操作和加密
3. **异步模式** - 所有数据库操作必须 async/await
4. **日志记录** - 使用 loguru 记录操作日志
5. **测试模式** - 使用 patch 和 AsyncMock 模拟依赖

**调用调度器的正确模式：**

```python
from app.scheduler import add_job, remove_job, reschedule_job

# 创建任务后注册到调度器
add_job(task)

# 更新任务后重新调度
reschedule_job(task)

# 删除任务前从调度器移除
remove_job(task_id)
```

### Git Intelligence Summary

**最近提交：**
- `cf4fc81 2-4-scheduled-execution-engine` - 调度器完成
- `e7ef942 2-3-openai-api-service` - OpenAI 服务完成
- `7728101 2-2-task-management-api` - 任务管理 API 完成

**可参考的代码模式：**
- `app/api/tasks.py` - API 路由模式（依赖注入、错误处理）
- `app/services/task_service.py` - 服务层调用模式
- `app/scheduler.py` - 调度器集成模式

### Latest Technical Information

**FastAPI Jinja2 模板（最新稳定版）：**

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": "value"}
    )
```

**表单处理（python-multipart 必需）：**

```python
from fastapi import Form

@app.post("/submit")
async def submit_form(
    name: str = Form(...),
    optional_field: Optional[str] = Form(None),
):
    return {"name": name}
```

**重定向模式（PRG - Post/Redirect/Get）：**

```python
from fastapi.responses import RedirectResponse

# POST 后重定向到 GET，防止表单重复提交
return RedirectResponse(url="/tasks?message=success", status_code=303)
```

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：**
- Story 2.1（任务与日志数据模型）✅ 已完成
- Story 2.2（任务管理 API）✅ 已完成
- Story 2.3（OpenAI API 调用服务）✅ 已完成
- Story 2.4（定时调度引擎）✅ 已完成

**后续故事：**
- Story 2.6（执行日志查看）将展示执行历史界面

### Common LLM Pitfalls to Avoid

1. **不要忘记 `request` 参数** - Jinja2 模板必须包含 `request` 在上下文中
2. **不要使用 status_code=302** - POST 后重定向应使用 303（See Other）
3. **不要忘记处理 checkbox** - HTML checkbox 未选中时不发送值，需要检查 `enabled == "true"`
4. **不要忘记 Form(...) 依赖** - 需要 python-multipart 库支持表单解析
5. **不要在模板中直接显示加密的 API 密钥** - 编辑时密钥字段应为空，提示"留空保持原值"
6. **不要忘记调用调度器函数** - 创建/更新/删除任务后必须同步调度器状态
7. **不要忘记创建 `app/web/__init__.py`** - 确保 Web 模块可被导入
8. **不要使用绝对路径重定向** - 使用相对路径或 url_for
9. **不要忘记表单验证错误处理** - 验证失败时重新渲染表单并显示错误，捕获 `ValueError` 和 `ValidationError`
10. **不要在 GET 请求中修改数据** - 删除操作应使用 POST 方法
11. **注意 URL 中文编码** - 重定向 URL 中的中文字符可能需要 URL 编码（现代浏览器通常自动处理）
12. **确保 get_session 依赖存在** - `app/database.py` 必须导出 `get_session` 异步生成器函数

### References

**源文档：**
- _bmad-output/architecture.md (Template-Based UI, Jinja2 Pattern)
- _bmad-output/prd.md (FR1-FR5: 任务配置)
- _bmad-output/epics.md (Story 2.5: 任务管理 Web 界面)
- _bmad-output/implementation-artifacts/2-4-scheduled-execution-engine.md (调度器集成)

**外部文档：**
- FastAPI Templates: https://fastapi.tiangolo.com/advanced/templates/
- Jinja2 文档: https://jinja.palletsprojects.com/en/3.1.x/

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无调试问题

### Completion Notes List

1. **Task 1 完成** - 创建了 Jinja2 模板基础设施：
   - 创建 `templates/` 目录结构
   - 创建 `templates/base.html` 基础布局模板（包含简洁 CSS 样式）
   - 在 `app/main.py` 注册 Web 路由
   - 无需静态文件目录（CSS 内嵌在 base.html）

2. **Task 2 完成** - 实现任务列表页面：
   - 创建 `templates/tasks/list.html` 显示任务列表
   - 创建 `app/web/tasks.py` Web 路由模块
   - 实现 `GET /` 路由渲染任务列表
   - 显示任务名称、调度规则、启用状态、最后执行时间
   - 按 Dev Notes 建议，移除日志按钮（Story 2.6 范围）

3. **Task 3 完成** - 实现任务创建页面：
   - 创建 `templates/tasks/form.html` 复用表单
   - 实现 `GET /tasks/new` 和 `POST /tasks/new` 路由
   - JavaScript 动态切换间隔/固定时间字段
   - 集成 task_service 和 scheduler

4. **Task 4 完成** - 实现任务编辑页面：
   - 复用 form.html 模板
   - API 密钥留空保持原值逻辑
   - 调用 reschedule_job() 更新调度器

5. **Task 5 完成** - 实现任务删除功能：
   - POST 删除（非 GET，符合 REST 最佳实践）
   - JavaScript confirm() 确认对话框
   - 先从调度器移除，再删除数据库

6. **Task 6 完成** - 编写 15 个测试用例：
   - 测试覆盖所有 CRUD 操作
   - 测试表单验证错误处理
   - 测试 API 密钥保留逻辑
   - 全部 127 个测试通过（原 112 + 新增 15）

7. **技术决策**：
   - 使用新版 TemplateResponse API（request 作为第一参数）避免弃用警告
   - 使用 status_code=303 进行 POST 后重定向（PRG 模式）
   - 表单验证失败返回 400 状态码并重新渲染表单

### File List

**新建文件：**
- templates/base.html
- templates/tasks/list.html
- templates/tasks/form.html
- app/web/__init__.py
- app/web/tasks.py
- tests/test_web_tasks.py

**修改文件：**
- app/main.py（添加 Web 路由注册）

### Change Log

- 2025-12-23: 完成 Story 2.5 任务管理 Web 界面实现
  - 实现 Jinja2 模板系统和 Web 路由
  - 支持任务 CRUD 操作的 Web 界面
  - 15 个新测试用例，127 个测试全部通过

- 2025-12-23: 代码审查修复 (Reviewer: Amelia)
  - [H1] 修复 N+1 查询问题：使用子查询优化 list_tasks()
  - [H2] 添加调度器失败处理：try-except 包装 add_job/reschedule_job
  - [H3] 修复表单验证保留用户输入：验证失败时返回 form_data
  - [M1] 添加数据库错误捕获：IntegrityError, SQLAlchemyError
  - [M4] 新增 5 个测试：表单数据保留、数据库错误、调度器错误处理
  - 132 个测试全部通过

### Senior Developer Review (AI)

**审查日期:** 2025-12-23
**审查员:** Amelia (Dev Agent)

**发现问题:**
- 3 HIGH (已修复)
- 4 MEDIUM (3 已修复, 1 存档)
- 4 LOW (存档)

**已修复:**
1. N+1 查询优化为单次子查询
2. 调度器错误不再阻塞任务保存
3. 表单验证失败保留用户输入
4. 数据库错误优雅处理
5. 新增完整测试覆盖

**存档问题 (LOW/可接受):**
- URL 参数传递消息 (MVP 可接受)
- 无 CSRF 保护 (内部工具可接受)
- Unicode URL 编码 (现代浏览器兼容)
- 缺少安全响应头 (MVP 可接受)

