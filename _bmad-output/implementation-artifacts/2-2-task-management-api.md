# Story 2.2: 任务管理 API

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 前端开发者,
I want 通过 REST API 管理任务,
So that Web UI 可以进行任务的增删改查操作。

## Acceptance Criteria

1. **Given** 数据模型已创建
   **When** 调用任务管理 API
   **Then** 支持以下端点：

   | 端点 | 方法 | 功能 |
   |------|------|------|
   | `/api/tasks` | GET | 获取所有任务列表 |
   | `/api/tasks` | POST | 创建新任务 |
   | `/api/tasks/{id}` | GET | 获取单个任务详情 |
   | `/api/tasks/{id}` | PUT | 更新任务配置 |
   | `/api/tasks/{id}` | DELETE | 删除任务 |

2. **And** API 响应使用 JSON 格式，字段使用 snake_case

3. **And** 创建成功返回 201，删除成功返回 204

4. **And** 任务不存在时返回 404

5. **And** API 密钥在响应中脱敏显示（如 `sk-...***`）

6. **And** 使用 Pydantic schemas 验证请求和响应

7. **And** 创建任务时 API 密钥使用 Fernet 加密存储

8. **And** 更新任务时验证调度逻辑一致性

## Tasks / Subtasks

- [x] Task 1: 实现 CRUD 服务层函数 (AC: #1, #7)
  - [x] 1.1 在 `app/services/` 创建 `task_service.py`
  - [x] 1.2 实现 `create_task()` - 加密 API 密钥后存储
  - [x] 1.3 实现 `get_task()` - 按 ID 获取单个任务
  - [x] 1.4 实现 `get_tasks()` - 获取所有任务列表
  - [x] 1.5 实现 `update_task()` - 部分更新，处理 API 密钥加密
  - [x] 1.6 实现 `delete_task()` - 删除任务

- [x] Task 2: 实现 API 端点 (AC: #1, #2, #3, #4)
  - [x] 2.1 在 `app/api/tasks.py` 实现 `POST /api/tasks` - 创建任务
  - [x] 2.2 实现 `GET /api/tasks` - 获取任务列表
  - [x] 2.3 实现 `GET /api/tasks/{task_id}` - 获取单个任务
  - [x] 2.4 实现 `PUT /api/tasks/{task_id}` - 更新任务
  - [x] 2.5 实现 `DELETE /api/tasks/{task_id}` - 删除任务

- [x] Task 3: 实现更新验证逻辑 (AC: #8)
  - [x] 3.1 在 PUT 端点实现调度逻辑验证
  - [x] 3.2 确保更新后的调度配置保持一致性

- [x] Task 4: 编写 API 测试 (AC: 全部)
  - [x] 4.1 在 `tests/test_api_tasks.py` 创建测试文件
  - [x] 4.2 测试创建任务（成功、验证失败）
  - [x] 4.3 测试获取任务列表
  - [x] 4.4 测试获取单个任务（成功、404）
  - [x] 4.5 测试更新任务（成功、404、部分更新）
  - [x] 4.6 测试删除任务（成功、404）
  - [x] 4.7 测试 API 密钥脱敏响应

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **异步架构** - 所有数据库操作使用 async/await
2. **命名规范** - snake_case（API 字段、变量名）
3. **HTTP 状态码** - 创建 201、删除 204、不存在 404
4. **错误格式** - FastAPI 标准格式 `{"detail": "..."}`
5. **分层架构** - API 层调用 Service 层

**相关需求支持：**
- FR1-5: 任务配置（端点、密钥、调度规则、消息、启用状态）
- NFR1: API 密钥加密存储
- NFR3: 响应中敏感信息脱敏

### Technical Requirements

**项目现有代码基础（Story 2.1 已完成）：**

1. **ORM 模型** - `app/models.py` 已有 Task 和 ExecutionLog 模型
2. **Pydantic Schemas** - `app/schemas.py` 已有：
   - `TaskCreate` - 创建请求
   - `TaskUpdate` - 更新请求（所有字段可选）
   - `TaskResponse` - 响应（api_key 自动脱敏）
   - `ExecutionLogResponse` - 日志响应
3. **加密工具** - `app/utils/security.py` 已有：
   - `encrypt_api_key()` - 加密 API 密钥
   - `decrypt_api_key()` - 解密 API 密钥
   - `mask_api_key()` - 脱敏显示
4. **数据库会话** - `app/database.py` 提供 `get_session()` 异步上下文管理器
5. **API 路由** - `app/api/tasks.py` 已有 router 占位符

**服务层实现模式：**

```python
# app/services/task_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.utils.security import encrypt_api_key, decrypt_api_key


async def create_task(session: AsyncSession, task_data: TaskCreate) -> Task:
    """Create a new task with encrypted API key."""
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
    """Get a task by ID."""
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks(session: AsyncSession) -> list[Task]:
    """Get all tasks."""
    result = await session.execute(select(Task).order_by(Task.id))
    return list(result.scalars().all())


async def update_task(
    session: AsyncSession, task: Task, task_data: TaskUpdate
) -> Task:
    """Update an existing task.

    Only non-None fields in task_data are updated.
    API key is encrypted if provided.
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
    """Delete a task."""
    await session.delete(task)
    await session.commit()
```

**API 端点实现模式：**

```python
# app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new task."""
    task = await task_service.create_task(session, task_data)
    return task


@router.get("", response_model=list[TaskResponse])
async def get_tasks(session: AsyncSession = Depends(get_session)):
    """Get all tasks."""
    return await task_service.get_tasks(session)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
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
):
    """Update an existing task."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate schedule configuration consistency
    # Need to merge existing values with update data
    update_dict = task_data.model_dump(exclude_unset=True)
    new_schedule_type = update_dict.get("schedule_type", task.schedule_type)
    new_interval = update_dict.get("interval_minutes", task.interval_minutes)
    new_fixed_time = update_dict.get("fixed_time", task.fixed_time)

    if new_schedule_type == "interval" and new_interval is None:
        raise HTTPException(
            status_code=400,
            detail="interval_minutes is required when schedule_type is 'interval'"
        )
    if new_schedule_type == "fixed_time" and new_fixed_time is None:
        raise HTTPException(
            status_code=400,
            detail="fixed_time is required when schedule_type is 'fixed_time'"
        )

    return await task_service.update_task(session, task, task_data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a task."""
    task = await task_service.get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await task_service.delete_task(session, task)
    return None
```

**关键实现细节：**

1. **依赖注入** - 使用 `Depends(get_session)` 获取数据库会话
2. **TaskResponse 自动脱敏** - Pydantic schema 已配置 `@field_validator("api_key")` 自动调用 `mask_api_key()`
3. **部分更新** - `model_dump(exclude_unset=True)` 只返回用户提供的字段
4. **调度验证** - PUT 端点需要合并现有值和更新值后验证一致性
5. **API 密钥保留** - 当 `api_key` 字段未提供时，保留数据库中现有的加密密钥。`exclude_unset=True` 确保只更新用户明确提供的字段
6. **DELETE 返回 None** - HTTP 204 No Content 表示操作成功但无响应体。FastAPI 在 204 响应中忽略返回值，返回 `None` 是惯例写法
7. **路由路径规范** - `prefix="/api/tasks"` + `@router.post("")` 等同于 `POST /api/tasks`，这是 FastAPI 推荐的模式

### Library/Framework Requirements

**已安装依赖（无需新增）：**
| 库 | 版本 | 用途 |
|----|------|------|
| fastapi | >=0.104.0 | Web 框架 |
| sqlalchemy | >=2.0.0 | 异步 ORM |
| pydantic | >=2.0.0 | 请求/响应验证 |
| cryptography | >=41.0.0 | API 密钥加密 |

### File Structure Requirements

**需要创建的文件：**
```
app/
├── services/
│   ├── __init__.py          # 需要更新导出
│   └── task_service.py      # 新建：任务 CRUD 服务
└── api/
    └── tasks.py              # 修改：实现 API 端点

tests/
└── test_api_tasks.py         # 新建：API 测试
```

**需要修改的文件：**
- `app/api/tasks.py` - 实现 5 个 CRUD 端点
- `app/services/__init__.py` - 导出 task_service

**`app/services/__init__.py` 更新示例：**

```python
# app/services/__init__.py
"""Business Services Package."""

from app.services import task_service  # noqa: F401

__all__ = ["task_service"]
```

### Testing Requirements

**API 测试策略：**

使用 FastAPI 的 `TestClient` 或 `httpx.AsyncClient` 测试 API 端点。

**测试隔离说明：** 每个测试 fixture 创建新的内存数据库引擎（`sqlite+aiosqlite:///:memory:`），测试结束后自动销毁，确保测试之间完全隔离。

**Fixture 注意事项：** `override_get_session()` 使用 `yield test_session` 直接返回已创建的会话实例，避免重复创建会话导致的生命周期问题。

```python
# tests/test_api_tasks.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_session, Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
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


@pytest.fixture
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


# Test data
VALID_TASK_DATA = {
    "name": "Test Task",
    "api_endpoint": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-test1234567890abcdef",
    "schedule_type": "interval",
    "interval_minutes": 60,
    "message_content": "Hello, AI!",
    "enabled": True,
}


@pytest.mark.asyncio
async def test_create_task_success(client):
    """Test creating a task successfully."""
    response = await client.post("/api/tasks", json=VALID_TASK_DATA)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"
    assert "id" in data
    # API key should be masked
    assert data["api_key"] == "sk-t...cdef"


@pytest.mark.asyncio
async def test_create_task_validation_error(client):
    """Test creating a task with invalid data."""
    invalid_data = {**VALID_TASK_DATA, "schedule_type": "interval", "interval_minutes": None}
    response = await client.post("/api/tasks", json=invalid_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_tasks_empty(client):
    """Test getting tasks when none exist."""
    response = await client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    """Test getting a non-existent task."""
    response = await client.get("/api/tasks/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


@pytest.mark.asyncio
async def test_update_task_not_found(client):
    """Test updating a non-existent task."""
    response = await client.put("/api/tasks/999", json={"name": "Updated"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_success(client):
    """Test deleting a task."""
    # Create first
    create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
    task_id = create_response.json()["id"]

    # Delete
    response = await client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_update_schedule_validation(client):
    """Test updating schedule type requires corresponding field."""
    # Create with interval
    create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
    task_id = create_response.json()["id"]

    # Try to change to fixed_time without fixed_time value
    response = await client.put(
        f"/api/tasks/{task_id}",
        json={"schedule_type": "fixed_time"}
    )
    assert response.status_code == 400
    assert "fixed_time is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_task_encrypts_new_api_key(client, test_session):
    """Test that updating API key properly encrypts the new value."""
    from app.models import Task
    from sqlalchemy import select

    # Create task
    create_response = await client.post("/api/tasks", json=VALID_TASK_DATA)
    task_id = create_response.json()["id"]

    # Update with new API key
    new_key = "sk-new-secret-key-67890"
    await client.put(f"/api/tasks/{task_id}", json={"api_key": new_key})

    # Verify database stores encrypted value (not plain text)
    result = await test_session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one()
    assert task.api_key != new_key  # Should be encrypted
    assert task.api_key != VALID_TASK_DATA["api_key"]  # Should be different from original
```

**测试清单：**

| 测试场景 | 预期状态码 | 验证点 |
|----------|------------|--------|
| 创建任务成功 | 201 | 返回完整任务，api_key 脱敏 |
| 创建任务验证失败 | 422 | 缺少必填字段 |
| 获取任务列表 | 200 | 返回数组 |
| 获取单个任务成功 | 200 | 返回任务详情 |
| 获取不存在任务 | 404 | `{"detail": "Task not found"}` |
| 更新任务成功 | 200 | 返回更新后任务 |
| 更新不存在任务 | 404 | `{"detail": "Task not found"}` |
| 更新调度配置不一致 | 400 | 验证错误信息 |
| 删除任务成功 | 204 | 无响应体 |
| 删除不存在任务 | 404 | `{"detail": "Task not found"}` |
| 测试更新 API 密钥加密 | 200 | 数据库存储新加密值 |

### Previous Story Intelligence

**来自 Story 2.1 的经验教训：**

1. **懒加载模式** - 使用 `get_settings()` 而非直接导入 `settings` 实例
2. **数据库会话** - 使用 `get_session()` 异步生成器，配合 `Depends()` 注入
3. **TaskResponse 脱敏** - 已配置 `field_validator`，从模型创建响应时自动调用 `mask_api_key()`
4. **加密存储** - 必须在服务层调用 `encrypt_api_key()` 后再存储到数据库

### Git Intelligence Summary

**最近提交：**
- `354a2c3 2-1-task-log-data-model` - 数据模型完成
- `8a7d4a9 1-3-docker-containerization` - Docker 配置
- `bd92736 1-2-environment-config-management` - 环境配置
- `cc6ab50 1-1-project-structure-init` - 项目结构初始化

**可参考的代码模式：**
- `app/database.py:69-73` - `get_session()` 异步生成器模式
- `app/utils/security.py:48-57` - `encrypt_api_key()` 加密模式
- `app/schemas.py:118-122` - `TaskResponse.mask_key()` 脱敏模式

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：** Story 2.1（任务与日志数据模型）已完成
**后续故事：**
- Story 2.3（OpenAI API 服务）将使用任务数据
- Story 2.4（定时调度引擎）将通过 API 获取任务配置
- Story 2.5（任务管理 Web UI）将调用这些 API 端点

### Common LLM Pitfalls to Avoid

1. **不要忘记加密 API 密钥** - 创建和更新时都需要调用 `encrypt_api_key()`
2. **不要在 API 响应中返回明文密钥** - TaskResponse 自动脱敏，但要确保使用正确的 schema
3. **不要使用同步数据库操作** - 所有 session 操作必须 await
4. **不要忘记 404 检查** - GET/PUT/DELETE 单个资源时必须检查是否存在
5. **不要忽略调度逻辑验证** - PUT 端点需要合并现有值后验证
6. **不要使用 `response_model=list` 语法** - 使用 `response_model=list[TaskResponse]`
7. **不要在 DELETE 端点返回内容** - 使用 `status_code=204` 并返回 `None`
8. **不要直接使用 session 而是用 Depends** - FastAPI 依赖注入确保正确的生命周期管理

### 并发与扩展说明

**并发更新处理：** SQLite 使用 WAL 模式支持并发读，但写操作会序列化。对于单用户 MVP，这已足够。如需支持高并发，考虑使用 PostgreSQL 的 MVCC。

**批量操作：** 当前 API 设计为单任务操作。如需批量创建/删除，可在 Phase 2 考虑添加 `/api/tasks/batch` 端点。

### Windows 兼容性说明

- 测试使用内存数据库 `sqlite+aiosqlite:///:memory:`
- 文件路径使用 `pathlib.Path` 确保跨平台兼容
- 异步测试需要 `pytest-asyncio` 插件

### References

**源文档：**
- _bmad-output/architecture.md (API Naming Conventions, HTTP Status Codes)
- _bmad-output/prd.md (FR1-5: 任务配置)
- _bmad-output/epics.md (Story 2.2: 任务管理 API)
- _bmad-output/implementation-artifacts/2-1-task-log-data-model.md (前置故事)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无调试问题。

### Completion Notes List

1. **Task 1 完成** - 创建 `app/services/task_service.py`，实现 5 个 CRUD 函数：
   - `create_task()`: 加密 API 密钥后创建任务
   - `get_task()`: 按 ID 获取任务
   - `get_tasks()`: 获取所有任务列表
   - `update_task()`: 部分更新，处理 API 密钥加密
   - `delete_task()`: 删除任务

2. **Task 2 完成** - 在 `app/api/tasks.py` 实现 5 个 REST API 端点：
   - `POST /api/tasks` (201 Created)
   - `GET /api/tasks` (200 OK)
   - `GET /api/tasks/{task_id}` (200 OK / 404 Not Found)
   - `PUT /api/tasks/{task_id}` (200 OK / 400 Bad Request / 404 Not Found)
   - `DELETE /api/tasks/{task_id}` (204 No Content / 404 Not Found)

3. **Task 3 完成** - PUT 端点实现调度逻辑验证：
   - 合并现有值和更新值后验证一致性
   - `schedule_type=interval` 时要求 `interval_minutes`
   - `schedule_type=fixed_time` 时要求 `fixed_time`

4. **Task 4 完成** - 创建 `tests/test_api_tasks.py`，包含 21 个测试用例：
   - 5 个创建任务测试
   - 2 个获取任务列表测试
   - 2 个获取单个任务测试
   - 7 个更新任务测试
   - 2 个删除任务测试
   - 3 个 API 密钥脱敏测试

5. **全部测试通过** - 70 个测试全部通过，无回归问题

6. **Code Review 修复** - 修复了 6 个审查问题：
   - [HIGH] AC #8 调度验证逻辑增强：切换 schedule_type 时自动清除不再需要的字段
   - [HIGH] 测试脱敏格式验证增强：使用正则表达式验证 `前4字符...后4字符` 格式
   - [HIGH] 添加 Pydantic 字段长度验证：name(100), api_endpoint(500), api_key(500)
   - [MEDIUM] 移动测试加密密钥到 conftest.py session fixture
   - [MEDIUM] 添加 API 密钥保留测试和调度字段清除测试
   - [MEDIUM] 更新 File List 包含所有修改文件

### File List

**新建文件:**
- `app/services/task_service.py` - 任务 CRUD 服务层

**修改文件:**
- `app/services/__init__.py` - 导出 task_service
- `app/api/tasks.py` - 实现 API 端点
- `app/schemas.py` - 添加字段长度验证 [Code Review Fix]
- `tests/conftest.py` - 移动测试加密密钥设置 [Code Review Fix]
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Sprint 状态更新

**新建测试文件:**
- `tests/test_api_tasks.py` - 23 个 API 端点测试（含 Code Review 新增测试）
