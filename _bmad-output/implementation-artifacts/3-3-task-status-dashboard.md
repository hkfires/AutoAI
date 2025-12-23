# Story 3.3: 任务状态仪表板

Status: done

<!-- Validated: 2025-12-23 -->

## Story

As a 用户,
I want 在首页看到所有任务的运行状态概览,
so that 我可以快速了解系统整体运行情况。

## Acceptance Criteria

1. **AC1: 仪表板统计信息**
   - Given 用户已登录并访问首页
   - When 页面加载
   - Then 显示任务状态仪表板，包含：
     - 总任务数
     - 已启用任务数
     - 今日执行次数
     - 今日成功率（百分比）

2. **AC2: 任务列表增强显示**
   - Given 用户查看任务列表
   - When 页面加载
   - Then 任务列表显示每个任务的：
     - 任务名称
     - 调度规则描述（如"每2小时"或"每天09:00"）
     - 启用/禁用状态
     - 最后执行时间
     - 最后执行状态（成功/失败/从未执行）
     - 操作按钮（编辑、日志、删除）

3. **AC3: 失败任务高亮警告**
   - Given 任务最后执行失败
   - When 查看任务列表
   - Then 该任务行用警告色高亮显示

4. **AC4: 仪表板统计准确性**
   - Given 存在多个任务和执行记录
   - When 计算今日统计
   - Then 今日执行次数和成功率仅计算今日 00:00:00 UTC 之后的记录
   - And 成功率 = 今日成功次数 / 今日总执行次数 * 100（无执行时显示 --）

## Tasks / Subtasks

- [x] Task 1: 增强后端路由获取仪表板统计数据 (AC: #1, #4)
  - [x] 1.1 修改 `app/web/tasks.py` 的 `list_tasks` 函数添加统计查询
  - [x] 1.2 查询总任务数和已启用任务数
  - [x] 1.3 查询今日执行次数（今日 00:00 UTC 之后的 ExecutionLog 记录）
  - [x] 1.4 查询今日成功次数并计算成功率（后端返回格式化字符串如"85%"或"--"）
  - [x] 1.5 将 `stats` 字典传递给模板（与现有 `tasks` 变量并列）

- [x] Task 2: 增强任务列表查询获取最后执行状态 (AC: #2, #3)
  - [x] 2.1 扩展现有子查询，使用单个子查询同时获取 `last_executed_at` 和 `last_status`
  - [x] 2.2 在 task_dict 中添加 `last_execution_status` 字段（success/failed/null）
  - [x] 2.3 添加调度规则格式化逻辑（interval_minutes >= 60 时显示小时）

- [x] Task 3: 更新首页模板显示仪表板 (AC: #1, #2)
  - [x] 3.1 修改 `templates/tasks/list.html` 添加仪表板卡片区域（使用 `stats` 变量）
  - [x] 3.2 显示四个统计卡片：总任务数、已启用、今日执行、今日成功率
  - [x] 3.3 更新调度规则列显示格式化后的描述

- [x] Task 4: 增强任务列表显示最后执行状态 (AC: #2, #3)
  - [x] 4.1 在任务列表表格中添加"最后状态"列
  - [x] 4.2 根据 `last_execution_status` 显示：成功（绿色）、失败（红色）、从未执行（灰色）
  - [x] 4.3 失败任务行添加警告背景色

- [x] Task 5: 更新 base.html 添加仪表板样式 (AC: #3)
  - [x] 5.1 在 `templates/base.html` 的 `<style>` 块中添加仪表板 CSS
  - [x] 5.2 添加警告行高亮样式 `.row-warning`
  - [x] 5.3 添加状态标签样式（`.status-success`, `.status-failed`, `.status-never`）

- [x] Task 6: 编写测试 (AC: #1, #2, #4)
  - [x] 6.1 测试首页返回仪表板统计数据
  - [x] 6.2 测试今日执行次数计算正确性（包含 00:00:00 UTC 边界测试）
  - [x] 6.3 测试今日成功率计算正确性（0%、100%、中间值）
  - [x] 6.4 测试任务列表包含最后执行状态
  - [x] 6.5 测试无执行记录时成功率显示"--"
  - [x] 6.6 测试无任何任务时仪表板显示（全部为 0）
  - [x] 6.7 测试调度规则格式化（分钟和小时显示）

## Dev Notes

### 时区策略

所有时间计算和存储使用 **UTC 时区**。"今日"定义为 UTC 时区的 00:00:00 至 23:59:59。

```python
from datetime import datetime, timezone

today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
# 查询条件使用 >= today_start 包含边界时刻
```

### 统计查询实现

使用 `asyncio.gather` 并行执行两个独立查询提升性能：

```python
import asyncio
from sqlalchemy import select, func, case

async def get_dashboard_stats(session: AsyncSession):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # 并行执行两个查询
    task_query = select(
        func.count(Task.id).label("total"),
        func.sum(case((Task.enabled == True, 1), else_=0)).label("enabled"),
    )
    exec_query = select(
        func.count(ExecutionLog.id).label("count"),
        func.sum(case((ExecutionLog.status == "success", 1), else_=0)).label("success"),
    ).where(ExecutionLog.executed_at >= today_start)

    task_result, exec_result = await asyncio.gather(
        session.execute(task_query),
        session.execute(exec_query),
    )

    task_stats = task_result.one()
    exec_stats = exec_result.one()

    # 计算成功率（后端格式化，避免前端除零）
    today_count = exec_stats.count or 0
    today_success = exec_stats.success or 0
    success_rate = f"{int(today_success / today_count * 100)}%" if today_count > 0 else "--"

    return {
        "total_tasks": task_stats.total or 0,
        "enabled_tasks": task_stats.enabled or 0,
        "today_executions": today_count,
        "today_success_rate": success_rate,
    }
```

### 最后执行状态查询

扩展现有子查询，使用单个子查询同时获取时间和状态，避免重复行问题：

```python
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

# 使用窗口函数获取每个任务的最后执行记录
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

# 只取 rn=1 的记录（最新一条）
latest_exec = (
    select(
        last_exec_subquery.c.task_id,
        last_exec_subquery.c.last_executed_at,
        last_exec_subquery.c.last_status,
    )
    .where(last_exec_subquery.c.rn == 1)
    .subquery()
)

# 最终查询
result = await session.execute(
    select(Task, latest_exec.c.last_executed_at, latest_exec.c.last_status)
    .outerjoin(latest_exec, Task.id == latest_exec.c.task_id)
    .order_by(Task.id)
)
```

### 调度规则格式化

```python
def format_schedule(task: dict) -> str:
    if task["schedule_type"] == "interval":
        minutes = task["interval_minutes"]
        if minutes >= 60 and minutes % 60 == 0:
            return f"每 {minutes // 60} 小时"
        return f"每 {minutes} 分钟"
    return f"每天 {task['fixed_time']}"
```

### 模板变量传递

`render_template` 调用需同时传递 `tasks` 和 `stats`：

```python
return render_template(
    request,
    "tasks/list.html",
    {"tasks": task_list, "stats": stats, "message": message, "message_type": message_type},
)
```

### CSS 样式（添加到 base.html 的 style 块）

```css
/* 仪表板样式 */
.dashboard { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
.dashboard-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px;
                  padding: 20px; min-width: 140px; flex: 1; text-align: center; }
.dashboard-card .card-value { font-size: 2em; font-weight: bold; color: #212529; }
.dashboard-card .card-label { color: #6c757d; margin-top: 5px; }

/* 状态标签 */
.status-success { color: #198754; font-weight: bold; }
.status-failed { color: #dc3545; font-weight: bold; }
.status-never { color: #6c757d; }

/* 警告行高亮 */
.row-warning { background-color: #fff3cd !important; }
```

### 现有代码扩展点

- `app/web/tasks.py:29-75` - 现有 `list_tasks` 函数，已有子查询模式
- `templates/tasks/list.html` - 现有模板结构
- `templates/base.html:7-33` - 现有 CSS 样式块

### 重要约束

1. **UTC 时区** - 所有时间计算使用 UTC，"今日"边界包含 00:00:00
2. **单次查询** - 使用窗口函数 `row_number()` 确保唯一性，避免重复行
3. **后端格式化** - 成功率在后端计算并格式化为字符串，避免前端除零
4. **扩展现有代码** - 在现有 `list_tasks` 函数中添加逻辑，保持代码组织一致

### 依赖关系

- **前置条件**: Story 3.1, 3.2 已完成（认证基础设施就绪）
- **后续依赖**: Story 3.4 将进一步增强日志查看功能

## Dev Agent Record

### Agent Model Used

gemini-claude-opus-4-5-thinking

### Debug Log References

(无调试问题)

### Completion Notes List

- 实现了 `get_dashboard_stats()` 函数，使用 `asyncio.gather` 并行执行任务统计和执行统计查询
- 使用窗口函数 `row_number()` 获取每个任务的最新执行状态，避免重复行问题
- 添加了仪表板卡片显示：总任务数、已启用任务数、今日执行次数、今日成功率
- 在任务列表中添加了"最后状态"列，显示成功/失败/从未执行状态
- 失败任务行自动添加警告背景色高亮
- 调度规则格式化：interval_minutes >= 60 且可被 60 整除时显示小时
- 所有 188 个测试通过，无回归问题

### Senior Developer Review (AI)

**审查日期:** 2025-12-23
**审查模型:** gemini-claude-opus-4-5-thinking

**发现并修复的问题:**

1. **[H1][已修复]** 测试断言不充分 - 多个仪表板测试只验证 HTTP 200，未验证实际统计数值
   - `tests/test_web_tasks.py:603,647,702` - 增强断言验证实际值

2. **[M1][已修复]** CSS 绿色状态颜色不一致 (#28a745 vs #198754)
   - `templates/base.html:30` - 统一为 #198754

3. **[M2/M3][已修复]** 调度规则格式化测试覆盖不完整
   - 添加 `test_schedule_format_non_hour_interval` 测试非整小时情况 (90 分钟)
   - 修正 `test_schedule_format_minutes` 断言逻辑

4. **[M4][已修复]** 窗口函数查询添加索引注释
   - `app/web/tasks.py:82` - 添加性能说明

**测试验证:** 41/41 passed

### File List

- app/web/tasks.py (修改)
- templates/tasks/list.html (修改)
- templates/base.html (修改)
- tests/test_web_tasks.py (修改)

### Change Log

- 2025-12-23: 实现任务状态仪表板功能 (Story 3.3)
- 2025-12-23: 代码审查修复 - 增强测试断言、统一 CSS 颜色、添加非整小时测试

