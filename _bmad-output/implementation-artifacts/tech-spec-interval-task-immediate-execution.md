# Tech-Spec: 间隔任务立即执行功能

**Created:** 2025-12-26
**Status:** Completed

## Review Notes

- 对抗性代码审查已完成
- 发现：10 个问题，5 个 CRITICAL/HIGH 已修复
- 修复方法：
  - F1 [CRITICAL]: 添加任务引用跟踪和异常处理 ✅
  - F2 [CRITICAL]: 添加 API 端点集成测试 ✅
  - F3 [HIGH]: 修复事件循环上下文违规 ✅
  - F4 [HIGH]: 竞态条件作为未来优化延期
  - F5 [HIGH]: asyncio 导入移到模块级别 ✅
  - F6-F10 [MEDIUM/LOW]: 作为技术债务记录

## 实现亮点

- 使用 `loop.create_task()` 而非 `asyncio.create_task()` 避免事件循环问题
- 添加 `execute_with_cleanup()` 内部函数处理异常和清理
- 使用全局 `_pending_immediate_tasks` 集合跟踪待处理任务
- 所有日志消息添加 `[IMMEDIATE]` 前缀便于监控
- 新增 3 个 API 端点测试确保 AC #5 满足

## Overview

### Problem Statement

当前系统创建间隔任务时，第一次执行会等待完整的间隔周期后才触发。例如，创建一个30分钟间隔的任务，需要等待30分钟后才会第一次执行。这导致用户无法立即验证任务配置是否正确，也无法立即获取数据。

### Solution

修改间隔任务（`schedule_type="interval"`）的行为，使其在任务创建或更新时立即执行第一次请求，然后按照设定的间隔继续执行。

### Scope (In/Out)

**In Scope:**
- ✅ 创建间隔任务时立即执行（仅当 `enabled=True`）
- ✅ 更新间隔任务时立即执行（仅当更新后 `enabled=True` 且 `schedule_type="interval"`）
- ✅ 保持定时任务（`schedule_type="fixed_time"`）的原有行为不变

**Out of Scope:**
- ❌ 不修改定时任务的执行逻辑
- ❌ 不影响任务禁用（`enabled=False`）时的行为
- ❌ 不修改调度器的核心调度逻辑

## Context for Development

### Codebase Patterns

**1. 异步架构：**
- 项目使用 FastAPI + SQLAlchemy（异步模式）
- 调度器使用 APScheduler 的 AsyncIOScheduler
- 所有数据库操作和任务执行都是异步的

**2. 任务调度流程：**
```
创建任务流程：
Web表单/API请求 → task_service.create_task() → add_job(task) → register_task(task) → APScheduler

更新任务流程：
Web表单/API请求 → task_service.update_task() → reschedule_job(task) → register_task(task) → APScheduler
```

**3. 执行逻辑：**
- 核心执行函数：`execute_task(task_id: int)` (scheduler.py:114)
- 执行流程：加载任务 → 检查enabled → 调用OpenAI API → 记录ExecutionLog
- 支持成功/失败状态记录

**4. 错误处理模式：**
- 调度器注册失败不影响任务保存（使用 try-except 包裹）
- 应用启动时重新注册所有启用的任务

### Files to Reference

**核心文件：**
- `app/scheduler.py:68-111` - `register_task()` 函数（调度器注册逻辑）
- `app/scheduler.py:114-189` - `execute_task()` 函数（任务执行逻辑）
- `app/scheduler.py:192-198` - `add_job()` 函数（动态添加任务）
- `app/scheduler.py:215-225` - `reschedule_job()` 函数（重新调度任务）

**调用点：**
- `app/web/tasks.py:207` - Web 创建任务后调用 `add_job()`
- `app/web/tasks.py:314` - Web 更新任务后调用 `reschedule_job()`
- `app/api/tasks.py:26` - API 创建任务（目前未调用调度器，需要补充）

**测试文件：**
- `tests/test_scheduler.py` - 调度器单元测试
- `tests/test_web_tasks.py` - Web 任务创建/更新集成测试

**模型和Schema：**
- `app/models.py:16-47` - Task 模型定义
- `app/schemas.py` - TaskCreate, TaskUpdate schema 定义

### Technical Decisions

**决策1：使用直接调用 `execute_task()` 而非修改 APScheduler 参数**

**理由：**
- ✅ 简单直接，代码变更最小
- ✅ 不影响 APScheduler 的内部调度逻辑
- ✅ 更容易理解和维护
- ✅ 可以在调用处清晰控制"何时立即执行"

**替代方案（被拒绝）：**
- ❌ 使用 `next_run_time=datetime.now()` 参数：会使 APScheduler 立即触发，但后续间隔计算可能不准确
- ❌ 使用 `run_date` trigger：需要组合触发器逻辑，过于复杂

**决策2：异步执行而非同步等待**

**理由：**
- ✅ 不阻塞 Web 请求响应
- ✅ 与现有异步架构保持一致
- ✅ 任务执行失败不影响任务创建成功

**实现方式：**
```python
import asyncio
asyncio.create_task(execute_task(task.id))
```

**决策3：API 路由也需要添加立即执行逻辑**

**发现：** `app/api/tasks.py:26` 创建任务后没有调用调度器
**修复：** 添加 `add_job(task)` 调用，与 Web 路由保持一致

## Implementation Plan

### Tasks

- [x] **Task 1**: 修改 `add_job()` 函数，添加立即执行逻辑
  - 文件：`app/scheduler.py:192-198`
  - 检查条件：`task.enabled=True` AND `task.schedule_type="interval"`
  - 调用：`asyncio.create_task(execute_task(task.id))`

- [x] **Task 2**: 修改 `reschedule_job()` 函数，添加立即执行逻辑
  - 文件：`app/scheduler.py:215-225`
  - 相同条件检查
  - 相同异步调用方式

- [x] **Task 3**: 修复 API 路由缺少调度器注册的问题
  - 文件：`app/api/tasks.py:19-27`
  - 在创建任务后调用 `add_job(task)`
  - 添加 try-except 错误处理（参考 web/tasks.py:206-210）

- [x] **Task 4**: 添加日志记录
  - 在立即执行时记录 INFO 日志
  - 格式：`"Immediately executing interval task {task_id} ({task.name})"`

- [x] **Task 5**: 编写/更新单元测试
  - 文件：`tests/test_scheduler.py`
  - 新测试：`test_add_job_executes_interval_task_immediately`
  - 新测试：`test_reschedule_job_executes_interval_task_immediately`
  - 新测试：`test_add_job_does_not_execute_fixed_time_task_immediately`
  - 新测试：`test_add_job_does_not_execute_disabled_task_immediately`

- [x] **Task 6**: 更新集成测试
  - 文件：`tests/test_web_tasks.py`
  - 验证创建/更新间隔任务后 ExecutionLog 被创建
  - 验证定时任务不受影响

### Acceptance Criteria

- [x] **AC 1**: 创建间隔任务（enabled=True）时，立即执行第一次请求
  - Given: 用户创建一个 `schedule_type="interval"`, `enabled=True` 的任务
  - When: 任务保存成功并注册到调度器
  - Then: 系统立即调用 `execute_task()`，无需等待间隔时间

- [x] **AC 2**: 创建间隔任务（enabled=False）时，不执行
  - Given: 用户创建一个 `schedule_type="interval"`, `enabled=False` 的任务
  - When: 任务保存成功
  - Then: 系统不执行 `execute_task()`

- [x] **AC 3**: 更新间隔任务时，立即执行
  - Given: 用户编辑一个现有任务，更新后 `schedule_type="interval"`, `enabled=True`
  - When: 任务更新成功并重新调度
  - Then: 系统立即执行 `execute_task()`

- [x] **AC 4**: 定时任务（fixed_time）不受影响
  - Given: 用户创建或更新一个 `schedule_type="fixed_time"` 的任务
  - When: 任务保存成功
  - Then: 系统不立即执行，等待到达指定时间

- [x] **AC 5**: API 路由与 Web 路由行为一致
  - Given: 使用 REST API 创建间隔任务
  - When: POST `/api/tasks` 成功
  - Then: 任务被注册到调度器并立即执行

- [x] **AC 6**: 执行记录正确保存
  - Given: 间隔任务被创建或更新
  - When: 立即执行完成
  - Then: `execution_logs` 表中存在对应的执行记录（status=success 或 failed）

- [x] **AC 7**: 所有单元测试通过
  - When: 运行 `pytest tests/test_scheduler.py -v`
  - Then: 所有测试用例通过，包括新增的6个测试

- [x] **AC 8**: 所有集成测试通过
  - When: 运行 `pytest tests/test_web_tasks.py tests/test_api_tasks.py -v`
  - Then: 所有测试用例通过

## Additional Context

### Dependencies

- **APScheduler** >= 3.10.0 - 任务调度框架
- **asyncio** - Python 标准库，用于异步任务创建

### Testing Strategy

**1. 单元测试策略：**
```python
# Mock database session 和 OpenAI service
# 验证 execute_task 被调用
with patch("app.scheduler.execute_task") as mock_execute:
    add_job(mock_interval_task)
    # 验证被调用
    mock_execute.assert_called_once_with(mock_interval_task.id)
```

**2. 集成测试策略：**
```python
# 使用真实数据库（测试数据库）
# 创建任务后，等待短时间，验证 ExecutionLog 被创建
response = await client.post("/tasks/new", data=task_data)
await asyncio.sleep(0.5)  # 等待异步执行完成
logs = await session.execute(select(ExecutionLog).where(ExecutionLog.task_id == task.id))
assert len(logs.scalars().all()) >= 1
```

**3. 边界测试：**
- 调度器未启动时创建任务（应该不抛出异常）
- 任务执行失败时（验证错误记录）
- 并发创建多个任务（验证互不影响）

### Notes

**1. 异步执行注意事项：**
- 使用 `asyncio.create_task()` 而非 `await execute_task()`
- 原因：不阻塞 HTTP 响应，任务在后台执行
- 副作用：立即执行的结果不会影响 HTTP 响应（这是预期行为）

**2. 日志记录：**
- 立即执行应该有明确的日志标识，便于调试
- 建议格式：`"[IMMEDIATE] Executing interval task {task_id}"`

**3. 向后兼容性：**
- 不需要数据迁移
- 现有任务不受影响
- 仅影响新创建/更新的间隔任务

**4. 性能考虑：**
- 立即执行不会显著增加系统负载
- 异步执行不阻塞主线程
- 如果 OpenAI API 响应慢，不会影响用户体验

**5. 潜在风险：**
- ⚠️ 如果用户批量创建大量任务，可能导致短时间内大量 API 调用
- 缓解措施：现有的速率限制和错误处理已足够
- ⚠️ 测试环境中需要 mock OpenAI API，避免真实调用

**6. 未来优化建议：**
- 考虑添加"首次执行延迟"配置选项（可选功能）
- 考虑在 UI 中显示"立即执行中"的状态提示
