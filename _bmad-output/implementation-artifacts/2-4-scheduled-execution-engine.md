# Story 2.4: 定时调度引擎

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 用户,
I want 系统按照我设定的时间自动执行任务,
So that 我无需手动触发，系统自动运行。

## Acceptance Criteria

1. **Given** 存在已启用的任务
   **When** 应用启动时
   **Then** APScheduler 加载所有已启用任务的调度规则
   **And** 间隔模式任务按 `interval_minutes` 周期执行
   **And** 固定时间模式任务在每天的 `fixed_time` 执行

2. **Given** 任务触发执行
   **When** 调度器调用任务
   **Then** 调用 OpenAI 服务发送消息
   **And** 将执行结果写入 ExecutionLog 表
   **And** 记录状态（success/failed）和响应摘要

3. **Given** 任务被禁用
   **When** 调度器检查任务状态
   **Then** 跳过该任务的执行

4. **Given** 应用重启
   **When** 调度器初始化
   **Then** 自动恢复所有已启用任务的调度

## Tasks / Subtasks

- [x] Task 1: 实现 APScheduler 调度器配置 (AC: #1, #4)
  - [x] 1.1 配置 AsyncIOScheduler 使用 SQLite 持久化（可选）或内存存储
  - [x] 1.2 实现调度器启动函数 `start_scheduler()`
  - [x] 1.3 实现调度器关闭函数 `shutdown_scheduler()`
  - [x] 1.4 在 main.py lifespan 中集成启动/关闭

- [x] Task 2: 实现任务注册机制 (AC: #1)
  - [x] 2.1 实现 `register_task(task)` 函数注册单个任务
  - [x] 2.2 实现 `register_all_tasks()` 从数据库加载所有已启用任务
  - [x] 2.3 支持间隔模式 (`interval`) 使用 `IntervalTrigger`
  - [x] 2.4 支持固定时间模式 (`fixed_time`) 使用 `CronTrigger`

- [x] Task 3: 实现任务执行函数 (AC: #2, #3)
  - [x] 3.1 创建 `execute_task(task_id)` 异步执行函数
  - [x] 3.2 从数据库获取任务配置
  - [x] 3.3 检查任务 enabled 状态，禁用则跳过
  - [x] 3.4 调用 `openai_service.send_message()` 发送消息
  - [x] 3.5 写入 ExecutionLog 记录执行结果

- [x] Task 4: 实现任务动态管理 (AC: #1, #3)
  - [x] 4.1 实现 `add_job(task)` 动态添加任务
  - [x] 4.2 实现 `remove_job(task_id)` 动态移除任务
  - [x] 4.3 实现 `reschedule_job(task)` 更新调度规则
  - [x] 4.4 任务 enabled 变更时同步调度器状态

- [x] Task 5: 编写单元测试 (AC: 全部)
  - [x] 5.1 创建 `tests/test_scheduler.py`
  - [x] 5.2 测试调度器启动/关闭
  - [x] 5.3 测试任务注册（间隔模式）
  - [x] 5.4 测试任务注册（固定时间模式）
  - [x] 5.5 测试任务执行和日志写入
  - [x] 5.6 测试禁用任务跳过
  - [x] 5.7 测试动态任务添加/移除

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **调度机制** - APScheduler 进程内调度，无需 Redis/消息队列
2. **异步架构** - 使用 AsyncIOScheduler，任务执行函数必须异步
3. **日志系统** - 使用 loguru 记录调度事件
4. **数据层** - SQLAlchemy 2.0 async 读写任务和日志
5. **命名规范** - snake_case（函数、变量、文件）

**相关需求支持：**
- FR6: 系统按照定时规则自动触发任务执行
- FR9: 系统记录每次执行的结果（成功/失败）
- NFR4: 系统支持基本错误重试机制（openai_service 已实现）
- NFR5: 系统能够在 VPS 重启后自动恢复运行

### Technical Requirements

**项目现有代码基础（Story 2.1/2.2/2.3 已完成）：**

1. **占位符文件** - `app/scheduler.py` 已存在，当前为空占位
2. **数据模型** - `app/models.py` 定义了 Task 和 ExecutionLog
3. **OpenAI 服务** - `app/services/openai_service.py` 提供 `send_message()` 函数
4. **安全工具** - `app/utils/security.py` 提供 `decrypt_api_key()` 函数
5. **已安装依赖** - apscheduler 已在 requirements.txt

**APScheduler 3.x 模式（项目使用版本）：**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# 项目现有的全局调度器实例（app/scheduler.py Line 9）
# 注意：使用现有的 scheduler 实例，不要创建新实例
from app.scheduler import scheduler

# 添加间隔任务（首次执行在 interval 后）
scheduler.add_job(
    execute_task,
    trigger=IntervalTrigger(minutes=task.interval_minutes),
    id=f"task_{task.id}",
    args=[task.id],
    replace_existing=True,
)

# 添加固定时间任务（每天 HH:MM）
hour, minute = map(int, task.fixed_time.split(":"))
scheduler.add_job(
    execute_task,
    trigger=CronTrigger(hour=hour, minute=minute),
    id=f"task_{task.id}",
    args=[task.id],
    replace_existing=True,
)
```

**首次执行时间说明：**
- **IntervalTrigger**: 默认首次执行在注册后立即触发。如需延迟首次执行，可不设置或使用 `next_run_time=None` 跳过首次立即执行
- **CronTrigger**: 在下一个匹配的时间点执行
- 本项目使用默认行为：间隔任务注册后立即执行一次，然后按间隔重复

### Scheduler Implementation Pattern

**app/scheduler.py 完整实现模式：**

**重要：基于现有代码结构实现**

现有 `app/scheduler.py` 已有全局 `scheduler` 实例，`app/database.py` 使用 `get_session_maker()` 模式。实现时必须使用这些现有模式。

```python
"""APScheduler configuration and task management."""

from datetime import datetime, timezone

from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from sqlalchemy import select

from app.database import get_session_maker
from app.models import Task, ExecutionLog
from app.services.openai_service import send_message, OpenAIServiceError
from app.utils.security import decrypt_api_key, mask_api_key

# 使用现有的全局调度器实例（保留 scheduler.py 原有的导入）
from app.scheduler import scheduler


async def start_scheduler() -> None:
    """Start the scheduler and register all enabled tasks."""
    # Register all enabled tasks from database
    await register_all_tasks()

    # Start the scheduler (同步调用)
    scheduler.start()
    logger.info("Scheduler started successfully")


async def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shutdown complete")


async def register_all_tasks() -> None:
    """Load and register all enabled tasks from database."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Task).where(Task.enabled == True)
        )
        tasks = result.scalars().all()

        for task in tasks:
            register_task(task)

        logger.info(f"Registered {len(tasks)} enabled tasks")


def register_task(task: Task) -> None:
    """Register a single task with the scheduler."""
    job_id = f"task_{task.id}"

    # Remove existing job if present
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass  # Job doesn't exist, continue

    if not task.enabled:
        logger.debug(f"Task {task.id} is disabled, skipping registration")
        return

    # Create trigger based on schedule type
    if task.schedule_type == "interval":
        trigger = IntervalTrigger(minutes=task.interval_minutes)
        schedule_desc = f"every {task.interval_minutes} minutes"
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
    )

    logger.info(f"Registered task {task.id} ({task.name}): {schedule_desc}")


async def execute_task(task_id: int) -> None:
    """Execute a scheduled task.

    Args:
        task_id: The ID of the task to execute.
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
            return  # 不创建 ExecutionLog，直接返回

        # Execute the task
        masked_key = mask_api_key(task.api_key)
        logger.info(f"Calling OpenAI API for task {task_id} (key: {masked_key})")

        # 必须设置 executed_at 字段（模型未定义默认值）
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
    """Dynamically add a new task to the scheduler."""
    register_task(task)


def remove_job(task_id: int) -> None:
    """Dynamically remove a task from the scheduler."""
    job_id = f"task_{task_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed task {task_id} from scheduler")
    except Exception:
        logger.debug(f"Task {task_id} not found in scheduler")


def reschedule_job(task: Task) -> None:
    """Update a task's schedule in the scheduler."""
    register_task(task)  # register_task handles removal and re-registration
```

### Main.py Lifespan Integration

**app/main.py 生命周期集成模式：**

**现有 main.py 代码 (Line 31-38) 需要修改：**

```diff
# 当前代码
- from app.scheduler import scheduler
+ from app.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await init_db()
-   scheduler.start()
+   await start_scheduler()

    yield

    # Shutdown
-   scheduler.shutdown()
+   await shutdown_scheduler()
```

**完整修改后的 lifespan 函数：**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config import get_settings, ensure_encryption_key
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler  # 修改导入


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting AutoAI application...")
    ensure_encryption_key()
    await init_db()
    await start_scheduler()  # 使用异步函数
    logger.info("AutoAI application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AutoAI application...")
    await shutdown_scheduler()  # 使用异步函数
    logger.info("AutoAI application shutdown complete")


app = FastAPI(lifespan=lifespan)
```

### Library/Framework Requirements

**已安装依赖（无需新增）：**

| 库 | 版本 | 用途 |
|----|------|------|
| apscheduler | >=3.10.0 | 定时调度 |
| sqlalchemy | >=2.0.0 | 异步 ORM |
| loguru | >=0.7.0 | 日志记录 |

### File Structure Requirements

**需要修改的文件：**
```
app/
├── scheduler.py           # 修改：实现调度器
└── main.py               # 修改：集成 lifespan

tests/
└── test_scheduler.py     # 新建：调度器测试
```

### Testing Requirements

**测试策略：**

使用 pytest + pytest-asyncio 测试异步调度器。Mock 数据库和 OpenAI 服务。

**重要：使用 `get_session_maker` 而非 `async_session_maker`**

测试时需要 mock `app.scheduler.get_session_maker`，与现有代码保持一致。

```python
# tests/test_scheduler.py
"""Tests for the scheduler module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.scheduler import (
    scheduler,  # 使用全局实例
    start_scheduler,
    shutdown_scheduler,
    register_task,
    execute_task,
    add_job,
    remove_job,
)
from app.models import Task, ExecutionLog
from app.services.openai_service import OpenAIResponse, OpenAIServiceError


@pytest.fixture
def mock_task():
    """Create a mock task for testing."""
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


@pytest.fixture(autouse=True)
def cleanup_scheduler():
    """Cleanup scheduler jobs after each test."""
    yield
    # Remove all jobs after test
    scheduler.remove_all_jobs()


# 测试辅助函数
def ensure_scheduler_running():
    """Ensure scheduler is running for tests."""
    if not scheduler.running:
        scheduler.start()
```

**测试清单（简化版，开发代理自行实现）：**

| # | 测试场景 | Mock 目标 | 关键验证点 |
|---|----------|-----------|------------|
| 1 | 调度器启动 | `register_all_tasks` | `scheduler.running == True` |
| 2 | 调度器关闭 | - | `scheduler.running == False` |
| 3 | 间隔任务注册 | - | `scheduler.get_job(job_id) is not None` |
| 4 | 固定时间任务注册 | - | `scheduler.get_job(job_id) is not None` |
| 5 | 禁用任务注册 | - | `scheduler.get_job(job_id) is None` |
| 6 | 任务执行成功 | `get_session_maker`, `send_message`, `decrypt_api_key` | `session.add` 和 `session.commit` 被调用，`execution_log.status == "success"` |
| 7 | 任务执行失败 | `get_session_maker`, `send_message` raises | `execution_log.status == "failed"`, `error_message` 有值 |
| 8 | 禁用任务执行 | `get_session_maker` | `send_message.assert_not_called()`, `session.add.assert_not_called()` |
| 9 | 任务不存在 | `get_session_maker` returns None | 无异常，无 `session.add` 调用 |
| 10 | 动态添加任务 | - | `scheduler.get_job(job_id) is not None` |
| 11 | 动态移除任务 | - | `scheduler.get_job(job_id) is None` |
| 12 | 移除不存在任务 | - | 无异常抛出 |

**Mock 模式示例：**

```python
# Mock get_session_maker 的正确方式
@pytest.mark.asyncio
async def test_execute_task_success(mock_task):
    """Test successful task execution."""
    mock_response = OpenAIResponse(
        response_summary="Hello! How can I help?",
        response_time_ms=150,
    )

    with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        mock_get_session_maker.return_value = mock_session_maker

        # Mock task query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_session.execute.return_value = mock_result

        with patch("app.scheduler.decrypt_api_key", return_value="plain_key"):
            with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
                mock_send.return_value = mock_response

                await execute_task(mock_task.id)

                mock_send.assert_called_once()
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

                # 验证 ExecutionLog 参数
                call_args = mock_session.add.call_args[0][0]
                assert call_args.status == "success"
                assert call_args.executed_at is not None


@pytest.mark.asyncio
async def test_execute_disabled_task_skipped(mock_task):
    """Test that disabled tasks are skipped - no ExecutionLog created."""
    mock_task.enabled = False

    with patch("app.scheduler.get_session_maker") as mock_get_session_maker:
        mock_session = AsyncMock()
        mock_session_maker = MagicMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        mock_get_session_maker.return_value = mock_session_maker

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_session.execute.return_value = mock_result

        with patch("app.scheduler.send_message", new_callable=AsyncMock) as mock_send:
            await execute_task(mock_task.id)

            # 验证：不调用 OpenAI 服务
            mock_send.assert_not_called()
            # 验证：不创建 ExecutionLog
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()
```

### Previous Story Intelligence

**来自 Story 2.3 的经验教训：**

1. **异步模式** - 所有 I/O 操作必须使用 async/await
2. **脱敏函数** - `mask_api_key()` 已在 `app/utils/security.py` 实现
3. **解密函数** - `decrypt_api_key()` 用于从数据库读取加密密钥后解密
4. **OpenAI 服务** - `send_message()` 返回 `OpenAIResponse(response_summary, response_time_ms)`
5. **错误处理** - `OpenAIServiceError` 包含 message 和 status_code

**调用 send_message() 的正确模式：**

```python
from app.utils.security import decrypt_api_key
from app.services.openai_service import send_message, OpenAIServiceError

# 从数据库获取 task 后
plain_api_key = decrypt_api_key(task.api_key)
try:
    result = await send_message(
        api_endpoint=task.api_endpoint,
        api_key=plain_api_key,
        message_content=task.message_content,
    )
    # 成功处理
    response_summary = result.response_summary
    response_time_ms = result.response_time_ms
except OpenAIServiceError as e:
    # 失败处理
    error_message = e.message
    status_code = e.status_code
```

### Git Intelligence Summary

**最近提交：**
- `e7ef942 2-3-openai-api-service` - OpenAI 服务完成
- `7728101 2-2-task-management-api` - 任务管理 API 完成
- `354a2c3 2-1-task-log-data-model` - 数据模型完成

**可参考的代码模式：**
- `app/services/openai_service.py` - 异步服务模式
- `app/utils/security.py` - 加密/解密/脱敏工具
- `app/database.py` - async_session_maker 使用模式
- `app/models.py` - Task 和 ExecutionLog 模型定义

**Story 2.3 修改的文件：**
- `app/services/openai_service.py` - OpenAI 服务实现
- `tests/test_openai_service.py` - 22 个单元测试

### Latest Technical Information

**APScheduler 3.x 异步调度器（稳定版本）：**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# 创建调度器
scheduler = AsyncIOScheduler()

# 添加间隔任务（每 60 分钟）
scheduler.add_job(
    my_async_func,
    trigger=IntervalTrigger(minutes=60),
    id="my_job",
    args=[arg1, arg2],
)

# 添加定时任务（每天 09:00）
scheduler.add_job(
    my_async_func,
    trigger=CronTrigger(hour=9, minute=0),
    id="daily_job",
)

# 启动调度器
scheduler.start()

# 关闭调度器
scheduler.shutdown(wait=False)
```

**关键配置项：**
- `coalesce=True`: 如果错过多次执行，只执行一次
- `max_instances=1`: 同一任务同时只能有一个实例运行
- `replace_existing=True`: 注册时替换已存在的同 ID 任务

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：**
- Story 2.1（任务与日志数据模型）✅ 已完成
- Story 2.2（任务管理 API）✅ 已完成
- Story 2.3（OpenAI API 调用服务）✅ 已完成

**后续故事：**
- Story 2.5（任务管理 Web UI）将提供任务配置界面
- Story 2.6（执行日志查看）将展示执行历史

### Common LLM Pitfalls to Avoid

1. **不要使用 get_scheduler() 单例模式** - 使用现有的全局 `scheduler` 实例
2. **不要使用 async_session_maker** - 使用 `get_session_maker()` 函数
3. **不要忘记设置 executed_at 字段** - ExecutionLog 模型没有默认值，必须显式设置 `datetime.now(timezone.utc)`
4. **不要在禁用任务时创建 ExecutionLog** - 禁用任务应直接返回，不写入日志
5. **不要忘记检查 task.enabled 状态** - 执行前必须验证任务是否启用
6. **不要在同步函数中调用 await** - execute_task 必须是异步函数
7. **不要忘记处理任务不存在的情况** - 数据库查询可能返回 None
8. **不要直接使用加密的 api_key** - 必须先调用 decrypt_api_key()
9. **不要使用 scheduler.shutdown(wait=True)** - 异步环境下使用 wait=False
10. **不要忘记 replace_existing=True** - 避免重复注册任务时报错
11. **不要忘记修改 main.py 的导入和调用** - 从 `scheduler` 改为 `start_scheduler, shutdown_scheduler`

### ExecutionLog 模型说明

**ExecutionLog 字段（来自 Story 2.1）：**
- `id`: 主键
- `task_id`: 外键关联 Task
- `executed_at`: 执行时间（**必须显式设置，无默认值**）
- `status`: 状态（`success` / `failed`）
- `response_summary`: 响应摘要
- `error_message`: 错误信息（可空）

**response_time_ms 持久化方案：**

当前 ExecutionLog 没有 response_time_ms 字段。采用 Story 2.3 建议的方案 A：
将响应时间追加到 response_summary 字段：
```python
execution_log.response_summary = (
    f"{response.response_summary} (耗时: {response.response_time_ms}ms)"
)
```

### References

**源文档：**
- _bmad-output/architecture.md (Scheduler Pattern, Async Patterns)
- _bmad-output/prd.md (FR6, FR9: 任务执行和日志)
- _bmad-output/epics.md (Story 2.4: 定时调度引擎)
- _bmad-output/implementation-artifacts/2-3-openai-api-service.md (前置故事)

**外部文档：**
- APScheduler 文档: https://apscheduler.readthedocs.io/en/stable/
- SQLAlchemy 异步: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无调试问题

### Completion Notes List

- 实现了完整的 APScheduler 调度器配置，使用 AsyncIOScheduler 和内存存储
- 实现了 `start_scheduler()` 和 `shutdown_scheduler()` 异步函数
- 集成到 main.py 的 lifespan 生命周期管理
- 实现了 `register_task()` 支持间隔模式 (IntervalTrigger) 和固定时间模式 (CronTrigger)
- 实现了 `register_all_tasks()` 从数据库加载所有已启用任务
- 实现了 `execute_task()` 异步执行函数，包含：
  - 从数据库获取任务配置
  - 检查任务 enabled 状态
  - 调用 OpenAI 服务发送消息
  - 写入 ExecutionLog 记录执行结果
- 实现了动态任务管理：`add_job()`, `remove_job()`, `reschedule_job()`
- 编写了 20 个单元测试，覆盖所有功能场景
- 全部 112 个项目测试通过，无回归

### Senior Developer Review (AI)

**审查日期:** 2025-12-22
**审查结果:** ✅ 通过

**发现并修复的问题：**

1. **[MEDIUM] 缺少 APScheduler 关键配置** - 已添加 `coalesce=True` 和 `max_instances=1` 参数到 `scheduler.add_job()` (app/scheduler.py:107-108)

2. **[MEDIUM] File List 文档不完整** - 已将 `sprint-status.yaml` 添加到 File List

3. **[MEDIUM] 异常捕获过于宽泛** - 已将 `except Exception` 改为 `except JobLookupError` (app/scheduler.py:82, 210)

**保留的 LOW 级别问题（不影响功能）：**
- 硬编码中文字符串 `(耗时: ...)` - 符合项目语言配置，保持现状
- 部分函数文档字符串简略 - 不影响代码质量

**测试验证：** 112 个测试全部通过

### File List

**修改的文件:**
- app/scheduler.py - 实现调度器完整功能（222 行）
- app/main.py - 集成 start_scheduler/shutdown_scheduler
- _bmad-output/implementation-artifacts/sprint-status.yaml - 更新故事状态

**新建的文件:**
- tests/test_scheduler.py - 调度器单元测试（509 行，20 个测试用例）

