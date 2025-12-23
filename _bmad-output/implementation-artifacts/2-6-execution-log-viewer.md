# Story 2.6: 执行日志查看

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 用户,
I want 查看任务的执行历史,
So that 我可以确认任务是否正常运行。

## Acceptance Criteria

1. **Given** 用户在任务列表点击"查看日志"
   **When** 进入日志页面
   **Then** 显示该任务的执行历史列表，包含：
   - 执行时间
   - 状态（成功/失败，用颜色区分）
   - 响应摘要（成功时）
   - 错误信息（失败时）

2. **And** 日志按执行时间倒序排列（最新在前）

3. **And** 默认显示最近 50 条记录

4. **And** API 端点 `/api/tasks/{id}/logs` 返回日志数据

## Tasks / Subtasks

- [x] Task 1: 实现日志查看 API 端点 (AC: #4)
  - [x] 1.1 在 `app/api/tasks.py` 添加 `GET /api/tasks/{task_id}/logs` 端点
  - [x] 1.2 使用已存在的 `ExecutionLogResponse` schema（`app/schemas.py:130-141`）
  - [x] 1.3 查询 ExecutionLog 按 `executed_at` 倒序排列
  - [x] 1.4 默认限制返回 50 条记录（可选支持 `limit` 查询参数）
  - [x] 1.5 任务不存在时返回 404

- [x] Task 2: 实现日志查看 Web 页面 (AC: #1, #2, #3)
  - [x] 2.1 创建 `templates/tasks/logs.html` 日志列表模板
  - [x] 2.2 在 `app/web/tasks.py` 添加 `GET /tasks/{task_id}/logs` 路由
  - [x] 2.3 显示执行时间（格式化为本地时间）
  - [x] 2.4 状态使用颜色区分：成功(绿色)、失败(红色)
  - [x] 2.5 成功时显示响应摘要，失败时显示错误信息
  - [x] 2.6 日志按执行时间倒序排列
  - [x] 2.7 限制显示最近 50 条记录

- [x] Task 3: 在任务列表页添加日志按钮 (AC: #1)
  - [x] 3.1 在 `templates/tasks/list.html` 操作列添加"日志"按钮
  - [x] 3.2 按钮链接到 `/tasks/{task_id}/logs`
  - [x] 3.3 使用 `btn btn-secondary` 样式，放在"编辑"按钮之后

- [x] Task 4: 编写测试 (AC: 全部)
  - [x] 4.1 创建/更新 `tests/test_api_logs.py` 测试 API 端点
  - [x] 4.2 测试日志 API 返回正确格式和排序
  - [x] 4.3 测试任务不存在时返回 404
  - [x] 4.4 测试日志页面渲染
  - [x] 4.5 测试空日志列表显示

## Dev Notes

### Critical Implementation Notes

> **前置条件：** Story 2.5 已完成任务管理 Web 界面，本 Story 在此基础上添加日志查看功能。
>
> **重要：** Story 2.5 完成时移除了日志按钮（属于本 Story 范围），因此 Task 3 必须在 `list.html` 中添加日志按钮。

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **模板引擎** - Jinja2 服务端渲染（延续 Story 2.5 模式）
2. **异步架构** - 所有路由和数据库操作使用 async/await
3. **命名规范** - snake_case（函数、变量、文件、API 字段）
4. **日志系统** - 使用 loguru 记录操作
5. **API 响应格式** - 直接返回数据，snake_case JSON 字段

**相关需求支持：**
- FR9: 记录每次执行的结果（成功/失败）
- FR12: 用户可以查看任务执行日志（Phase 2，但基础功能在 MVP 实现）

### Technical Requirements

**项目现有代码基础（Story 2.1-2.5 已完成）：**

1. **数据模型** - `app/models.py` 定义了 ExecutionLog：
   - `id`: 主键
   - `task_id`: 外键关联 Task
   - `executed_at`: 执行时间
   - `status`: 状态（`success` / `failed`）
   - `response_summary`: 响应摘要
   - `error_message`: 错误信息（可空）

2. **Web 路由** - `app/web/tasks.py` 已有任务列表和表单路由
3. **模板系统** - `templates/base.html` 基础布局已创建
4. **测试模式** - `tests/test_web_tasks.py` 提供参考模式

**关键代码位置：**

| 模块 | 文件路径 | 用途 |
|------|----------|------|
| 数据模型 | `app/models.py` | ExecutionLog ORM |
| Schemas | `app/schemas.py` | ExecutionLogResponse 已存在（:130-141） |
| API 路由 | `app/api/tasks.py` | 需添加日志 API |
| Web 路由 | `app/web/tasks.py` | 需添加日志页面路由 |
| 模板 | `templates/tasks/` | 需添加 logs.html，修改 list.html |
| 数据库 | `app/database.py` | get_session 依赖注入 |

### ExecutionLog 模型（已存在于 models.py）

```python
class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20))  # success / failed
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="execution_logs")
```

### Pydantic Schema（已存在）

**`app/schemas.py:130-141` 已包含 ExecutionLogResponse，无需修改：**

```python
class ExecutionLogResponse(BaseModel):
    """Schema for ExecutionLog API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    executed_at: datetime
    status: str  # success | failed
    response_summary: Optional[str] = None
    error_message: Optional[str] = None
```

> **注意：** 直接使用现有 schema，无需创建 ExecutionLogListResponse 包装类（API 直接返回列表）。

### API 端点实现

**在 app/api/tasks.py 中添加：**

```python
# 添加到现有 imports
from sqlalchemy import select, desc
from app.models import Task, ExecutionLog
from app.schemas import ExecutionLogResponse

@router.get("/{task_id}/logs", response_model=list[ExecutionLogResponse])
async def get_task_logs(
    task_id: int,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """Get execution logs for a specific task.

    Returns logs ordered by execution time (newest first).
    Default limit is 50 records.
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
```

### Web 页面路由实现

**在 app/web/tasks.py 中添加：**

```python
@router.get("/tasks/{task_id}/logs")
async def view_task_logs(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_session),
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

    return templates.TemplateResponse(
        request,
        "tasks/logs.html",
        {"task": task, "logs": logs},
    )
```

### 日志页面模板

**templates/tasks/logs.html：**

```html
{% extends "base.html" %}

{% block title %}执行日志 - {{ task.name }} - AutoAI{% endblock %}

{% block content %}
<h1>执行日志：{{ task.name }}</h1>

<p style="margin-bottom: 20px;">
    <a href="/" class="btn btn-secondary">&larr; 返回任务列表</a>
</p>

<table>
    <thead>
        <tr>
            <th>执行时间</th>
            <th>状态</th>
            <th>响应/错误信息</th>
        </tr>
    </thead>
    <tbody>
        {% for log in logs %}
        <tr>
            <td>{{ log.executed_at.strftime('%Y-%m-%d %H:%M:%S') }}</td>
            <td>
                {% if log.status == 'success' %}
                    <span class="status-enabled">✓ 成功</span>
                {% else %}
                    <span class="status-disabled">✗ 失败</span>
                {% endif %}
            </td>
            <td>
                {% if log.status == 'success' %}
                    {{ log.response_summary or '-' }}
                {% else %}
                    <span style="color: #dc3545;">{{ log.error_message or '未知错误' }}</span>
                {% endif %}
            </td>
        </tr>
        {% else %}
        <tr>
            <td colspan="3" style="text-align: center; color: #666;">
                暂无执行记录
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<p style="margin-top: 10px; color: #666; font-size: 0.9em;">
    显示最近 {{ logs|length }} 条记录（最多 50 条）
</p>
{% endblock %}
```

### 任务列表页更新

**在 `templates/tasks/list.html` 操作列添加日志按钮：**

找到操作列的 `<td>` 标签，在"编辑"按钮之后添加日志按钮：

```html
<td>
    <a href="/tasks/{{ task.id }}/edit" class="btn btn-secondary">编辑</a>
    <a href="/tasks/{{ task.id }}/logs" class="btn btn-secondary">日志</a>
    <form action="/tasks/{{ task.id }}/delete" method="POST" style="display: inline;">
        <button type="submit" class="btn btn-danger"
                onclick="return confirm('确定要删除任务「{{ task.name }}」吗？')">删除</button>
    </form>
</td>
```

> **位置：** 在 `<a href="/tasks/{{ task.id }}/edit"...>编辑</a>` 之后，`<form action=".../delete"...>` 之前。

### Library/Framework Requirements

**已安装依赖（无需新增）：**

| 库 | 版本 | 用途 |
|----|------|------|
| fastapi | >=0.104.0 | Web 框架 |
| jinja2 | >=3.1.0 | 模板引擎 |
| sqlalchemy | >=2.0.0 | ORM |

### File Structure Requirements

**需要创建/修改的文件：**

```
app/
├── api/
│   └── tasks.py           # 修改：添加日志 API 端点
└── web/
    └── tasks.py           # 修改：添加日志页面路由

templates/
└── tasks/
    ├── list.html          # 修改：添加日志按钮
    └── logs.html          # 新建：日志列表页面

tests/
├── test_api_logs.py       # 新建：日志 API 测试
└── test_web_tasks.py      # 修改：添加日志页面测试
```

> **注意：** `app/schemas.py` 无需修改，ExecutionLogResponse 已存在。

### Testing Requirements

**测试策略：**

使用 pytest + httpx.AsyncClient 测试 API 和 Web 页面。

**API 测试示例：**

```python
# tests/test_api_logs.py
"""Tests for the execution logs API."""

import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models import ExecutionLog


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_task_logs_success(client):
    """Test getting logs for a task returns correct data."""
    mock_task = MagicMock(id=1, name="Test Task")
    mock_log = MagicMock(
        id=1,
        task_id=1,
        executed_at=datetime(2025, 12, 23, 10, 0, 0),
        status="success",
        response_summary="OK",
        error_message=None,
    )

    with patch("app.api.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_task
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_log])))
        )
        mock_get_session.return_value = mock_session

        response = await client.get("/api/tasks/1/logs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "success"


@pytest.mark.asyncio
async def test_get_task_logs_task_not_found(client):
    """Test 404 when task does not exist."""
    with patch("app.api.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.get.return_value = None
        mock_get_session.return_value = mock_session

        response = await client.get("/api/tasks/999/logs")

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_task_logs_empty(client):
    """Test empty log list."""
    mock_task = MagicMock(id=1)

    with patch("app.api.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_task
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        mock_get_session.return_value = mock_session

        response = await client.get("/api/tasks/1/logs")

        assert response.status_code == 200
        assert response.json() == []
```

**Web 页面测试示例：**

```python
# 添加到 tests/test_web_tasks.py

@pytest.mark.asyncio
async def test_logs_page_renders(client):
    """Test that the logs page renders successfully."""
    mock_task = MagicMock(id=1, name="Test Task")
    mock_log = MagicMock(
        id=1,
        executed_at=datetime(2025, 12, 23, 10, 0, 0),
        status="success",
        response_summary="OK",
        error_message=None,
    )

    with patch("app.web.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_task
        mock_session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_log])))
        )
        mock_get_session.return_value = mock_session

        response = await client.get("/tasks/1/logs")

        assert response.status_code == 200
        assert "执行日志" in response.text
        assert "Test Task" in response.text


@pytest.mark.asyncio
async def test_logs_page_task_not_found(client):
    """Test redirect when task does not exist."""
    with patch("app.web.tasks.get_session") as mock_get_session:
        mock_session = AsyncMock()
        mock_session.get.return_value = None
        mock_get_session.return_value = mock_session

        response = await client.get("/tasks/999/logs", follow_redirects=False)

        assert response.status_code == 303
        assert "message=任务不存在" in response.headers["location"]
```

### Previous Story Intelligence

**来自 Story 2.5 的经验教训：**

1. **模板模式** - 使用 `{% extends "base.html" %}` 继承基础布局
2. **状态样式** - 复用 `.status-enabled`（绿色）和 `.status-disabled`（红色）
3. **表格格式** - 复用现有表格样式
4. **重定向模式** - 使用 status_code=303 进行 POST 后重定向
5. **模板响应** - 使用新版 API：`templates.TemplateResponse(request, "template.html", context)`
6. **错误处理** - 任务不存在时重定向并显示错误消息

**调用模式参考（来自 Story 2.5）：**

```python
# 数据库查询模式
result = await session.execute(
    select(ExecutionLog)
    .where(ExecutionLog.task_id == task_id)
    .order_by(desc(ExecutionLog.executed_at))
    .limit(50)
)
logs = result.scalars().all()

# 模板响应模式
return templates.TemplateResponse(
    request,
    "tasks/logs.html",
    {"task": task, "logs": logs},
)
```

### Git Intelligence Summary

**最近提交：**
- `25a1bd8 2-5-task-management-web-ui` - Web 界面完成
- `cf4fc81 2-4-scheduled-execution-engine` - 调度器完成

**可参考的代码模式：**
- `app/web/tasks.py` - Web 路由模式（依赖注入、模板响应、重定向）
- `templates/tasks/list.html` - 表格列表模式
- `app/api/tasks.py` - API 路由模式

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：**
- Story 2.1（任务与日志数据模型）✅ 已完成
- Story 2.2（任务管理 API）✅ 已完成
- Story 2.3（OpenAI API 调用服务）✅ 已完成
- Story 2.4（定时调度引擎）✅ 已完成
- Story 2.5（任务管理 Web 界面）✅ 已完成

**本 Story 完成后：**
- Epic 2 所有 Story 完成
- 可运行 epic-2-retrospective（可选）
- 可继续 Epic 3: Web 管理后台与认证 [Phase 2]

### Common LLM Pitfalls to Avoid

1. **不要忘记检查任务是否存在** - API 和 Web 路由都需要先验证 task_id 有效
2. **不要忘记倒序排列** - 使用 `order_by(desc(ExecutionLog.executed_at))`
3. **不要忘记限制记录数** - 使用 `.limit(50)` 防止返回过多数据
4. **不要混淆 API 和 Web 路由** - API 返回 JSON，Web 返回 HTML
5. **不要忘记导入 desc 和 ExecutionLog** - `from sqlalchemy import select, desc` 和 `from app.models import Task, ExecutionLog`
6. **Schema 已存在** - 直接导入 `from app.schemas import ExecutionLogResponse`，无需创建
7. **不要硬编码日期格式** - 在模板中使用 `.strftime()` 格式化
8. **不要忘记处理空日志列表** - 模板中使用 `{% else %}` 显示空状态
9. **API 路由前缀** - 现有 router 已有 `/api/tasks` 前缀，所以新端点路径是 `/{task_id}/logs`（不是 `/tasks/{task_id}/logs`）
10. **注意模板响应 API** - 使用新版 `TemplateResponse(request, template, context)` 避免弃用警告
11. **必须添加日志按钮** - `list.html` 中目前没有日志按钮，Task 3 必须添加

### References

**源文档：**
- _bmad-output/architecture.md (API Patterns, Naming Conventions)
- _bmad-output/epics.md (Story 2.6: 执行日志查看)
- _bmad-output/implementation-artifacts/2-5-task-management-web-ui.md (模板模式, Web 路由模式)

**外部文档：**
- FastAPI Templates: https://fastapi.tiangolo.com/advanced/templates/
- SQLAlchemy 2.0 Query: https://docs.sqlalchemy.org/en/20/orm/queryguide/

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无错误，所有测试一次通过。

### Completion Notes List

- ✅ Task 1: 实现日志查看 API 端点 `GET /api/tasks/{task_id}/logs`
  - 添加到 `app/api/tasks.py:97-122`
  - 使用已有的 `ExecutionLogResponse` schema
  - 按 `executed_at` 倒序排列，默认限制 50 条
  - 支持 `limit` 查询参数
  - 任务不存在返回 404

- ✅ Task 2: 实现日志查看 Web 页面
  - 创建 `templates/tasks/logs.html` 模板
  - 添加 `GET /tasks/{task_id}/logs` 路由到 `app/web/tasks.py:282-310`
  - 成功/失败状态用颜色区分（绿色/红色）
  - 日志按时间倒序，限制 50 条

- ✅ Task 3: 在任务列表页添加日志按钮
  - 修改 `templates/tasks/list.html:41` 添加日志按钮
  - 使用 `btn btn-secondary` 样式

- ✅ Task 4: 编写测试
  - 创建 `tests/test_api_logs.py`（12 个测试，含边界验证）
  - 添加 `TestLogsPage` 类到 `tests/test_web_tasks.py`（5 个测试）

- 全部测试通过，无回归

### File List

**新增文件：**
- `templates/tasks/logs.html` - 日志列表页面模板（含本地时区转换）
- `tests/test_api_logs.py` - 日志 API 测试

**修改文件：**
- `app/api/tasks.py` - 添加 `GET /{task_id}/logs` 端点（含 limit 参数验证）
- `app/web/tasks.py` - 添加日志页面路由
- `templates/tasks/list.html` - 添加日志按钮
- `tests/test_web_tasks.py` - 添加 TestLogsPage 测试类
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - 更新故事状态

### Code Review Fixes Applied

**审查员:** Amelia (Dev Agent) - 2025-12-23

**修复的问题：**

1. **[HIGH] limit 参数添加验证** `app/api/tasks.py:100`
   - 添加 `Query(default=50, ge=1, le=100)` 验证
   - 防止 limit=0/-1 或过大值导致的问题

2. **[MEDIUM] 时间显示转换为本地时区** `templates/tasks/logs.html`
   - 添加 JavaScript 将 UTC 时间转换为浏览器本地时间
   - 使用 `toLocaleString('zh-CN')` 格式化

3. **[MEDIUM] 添加边界测试** `tests/test_api_logs.py`
   - 新增 4 个测试验证 limit 参数边界
   - 测试 limit=0, -1, 101, 100

