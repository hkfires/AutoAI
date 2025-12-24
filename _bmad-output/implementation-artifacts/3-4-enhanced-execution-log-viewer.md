# Story 3.4: 增强的执行日志查看

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 用户,
I want 更详细地查看和筛选执行日志,
so that 我可以排查问题和监控系统运行。

## Acceptance Criteria

1. **AC1: 状态筛选功能**
   - Given 用户查看任务执行日志
   - When 进入日志页面
   - Then 支持按状态筛选（全部/成功/失败）
   - And 默认显示"全部"状态
   - And 筛选条件通过 URL 查询参数传递（如 `?status=success`）

2. **AC2: 日期范围筛选功能**
   - Given 用户查看任务执行日志
   - When 选择日期范围
   - Then 只显示指定日期范围内的记录
   - And 日期范围通过 URL 查询参数传递（如 `?start_date=2025-12-01&end_date=2025-12-23`）
   - And 日期为空时不限制日期范围

3. **AC3: 分页显示功能**
   - Given 执行日志超过 20 条
   - When 查看日志列表
   - Then 每页显示 20 条记录
   - And 显示分页导航（上一页/下一页/页码）
   - And 当前页码通过 URL 查询参数传递（如 `?page=2`）
   - And 分页时保留其他筛选条件

4. **AC4: 日志详情展开功能**
   - Given 用户点击某条日志行
   - When 展开日志详情
   - Then 显示完整信息：
     - 执行时间（精确到秒，本地时区）
     - 状态（成功/失败）
     - 响应摘要（成功时）
     - 完整错误信息（失败时）
   - Note: 请求耗时功能跳过（ExecutionLog 模型无 duration 字段，如需此功能需后续故事添加数据库迁移）

5. **AC5: 日志统计信息**
   - Given 用户进入日志页面
   - When 页面加载
   - Then 日志页面顶部显示统计信息：
     - 该任务总执行次数
     - 成功率（百分比）
     - 最近 7 天的执行趋势（简单文字描述，如"共执行 15 次，成功 14 次"）

## Tasks / Subtasks

- [x] Task 1: 扩展后端日志查询支持筛选和分页 (AC: #1, #2, #3)
  - [x] 1.1 修改 `app/web/tasks.py` 的 `view_task_logs` 函数，添加查询参数支持
  - [x] 1.2 添加 `status` 参数（可选，值为 success/failed/空）
  - [x] 1.3 添加 `start_date` 和 `end_date` 参数（可选，格式 YYYY-MM-DD）
  - [x] 1.4 添加 `page` 参数（默认为 1，每页 20 条）
  - [x] 1.5 计算总页数并传递给模板

- [x] Task 2: 实现日志统计查询 (AC: #5)
  - [x] 2.1 查询该任务的总执行次数
  - [x] 2.2 查询成功次数并计算成功率
  - [x] 2.3 查询最近 7 天的执行统计（执行次数、成功次数）
  - [x] 2.4 将 `log_stats` 字典传递给模板

- [x] Task 3: 更新日志页面模板支持筛选 (AC: #1, #2)
  - [x] 3.1 添加筛选表单区域（状态下拉框、日期输入框、筛选按钮）
  - [x] 3.2 表单提交使用 GET 方法，保持 URL 参数
  - [x] 3.3 回显当前筛选条件值
  - [x] 3.4 添加"清除筛选"按钮重置条件

- [x] Task 4: 实现分页导航 (AC: #3)
  - [x] 4.1 在日志列表底部添加分页控件
  - [x] 4.2 显示当前页/总页数
  - [x] 4.3 分页链接保留当前筛选条件
  - [x] 4.4 处理边界情况（首页禁用上一页，末页禁用下一页）

- [x] Task 5: 实现日志详情展开 (AC: #4)
  - [x] 5.1 使用 JavaScript 实现点击行展开/收起
  - [x] 5.2 展开区域显示完整日志信息
  - [x] 5.3 添加展开行的样式（不同背景色标识）

- [x] Task 6: 添加统计信息展示 (AC: #5)
  - [x] 6.1 在筛选表单上方添加统计卡片区域
  - [x] 6.2 显示总执行次数、成功率
  - [x] 6.3 显示最近 7 天趋势描述

- [x] Task 7: 添加必要的 CSS 样式
  - [x] 7.1 筛选表单样式（水平排列）
  - [x] 7.2 分页控件样式
  - [x] 7.3 展开详情行样式
  - [x] 7.4 统计卡片样式（复用仪表板样式）

- [x] Task 8: 编写测试 (AC: #1-#5)
  - [x] 8.1 测试状态筛选返回正确记录
  - [x] 8.2 测试日期范围筛选返回正确记录
  - [x] 8.3 测试分页返回正确记录数
  - [x] 8.4 测试统计数据计算正确性
  - [x] 8.5 测试空日志时的边界情况
  - [x] 8.6 测试筛选条件组合（状态+日期+分页）
  - [x] 8.7 测试 7 天趋势统计计算
  - [x] 8.8 测试无效 page 参数处理（page=0, page=-1 应默认为 1）
  - [x] 8.9 测试无效 status 参数处理（status=invalid 应忽略筛选）

## Dev Notes

### 现有代码扩展点

- `app/web/tasks.py:348-377` - 现有 `view_task_logs` 函数，需要大幅增强
- `templates/tasks/logs.html` - 现有模板，需要添加筛选、分页、统计
- `templates/base.html` - 已有仪表板 CSS 样式，可复用

### 后端实现模式

#### 必需导入语句 (Task 1, 2)

在 `app/web/tasks.py` 文件顶部确保以下导入存在：

```python
# 标准库
from datetime import datetime, timedelta, timezone
from typing import Optional

# SQLAlchemy（部分已存在，确认完整性）
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

# 项目内部
from app.models import Task, ExecutionLog
from app.database import get_session
```

#### get_log_stats 辅助函数 (Task 2)

**添加位置:** `app/web/tasks.py`，在 `view_task_logs` 函数之前（约第 340 行位置）

```python
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
```

#### view_task_logs 函数增强 (Task 1)

**修改位置:** `app/web/tasks.py:348-377`，替换现有 `view_task_logs` 函数

```python
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
```

#### 日志统计查询

```python
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
```

### 前端实现模式

#### 筛选表单 HTML

```html
<!-- 筛选表单 -->
<form method="GET" class="filter-form">
    <div class="filter-group">
        <label for="status">状态</label>
        <select name="status" id="status">
            <option value="">全部</option>
            <option value="success" {% if filters.status == 'success' %}selected{% endif %}>成功</option>
            <option value="failed" {% if filters.status == 'failed' %}selected{% endif %}>失败</option>
        </select>
    </div>
    <div class="filter-group">
        <label for="start_date">开始日期</label>
        <input type="date" name="start_date" id="start_date" value="{{ filters.start_date or '' }}">
    </div>
    <div class="filter-group">
        <label for="end_date">结束日期</label>
        <input type="date" name="end_date" id="end_date" value="{{ filters.end_date or '' }}">
    </div>
    <button type="submit" class="btn btn-primary">筛选</button>
    <a href="/tasks/{{ task.id }}/logs" class="btn btn-secondary">清除</a>
</form>
```

#### 分页导航 HTML (Task 4)

**Note:** 使用 `or ''` 避免 None 值渲染为字符串 "None"

```html
<!-- 分页导航 -->
{% if total_pages > 1 %}
<div class="pagination">
    {% if page > 1 %}
    <a href="?page={{ page - 1 }}&status={{ filters.status or '' }}&start_date={{ filters.start_date or '' }}&end_date={{ filters.end_date or '' }}" class="page-link">上一页</a>
    {% else %}
    <span class="page-link disabled">上一页</span>
    {% endif %}

    <span class="page-info">第 {{ page }} / {{ total_pages }} 页</span>

    {% if page < total_pages %}
    <a href="?page={{ page + 1 }}&status={{ filters.status or '' }}&start_date={{ filters.start_date or '' }}&end_date={{ filters.end_date or '' }}" class="page-link">下一页</a>
    {% else %}
    <span class="page-link disabled">下一页</span>
    {% endif %}
</div>
{% endif %}
```

#### 日志行与展开详情 HTML 结构 (Task 5)

**关键:** 每条日志需要两行 - 主行 `.log-row` 和详情行 `.detail-row`

```html
<tbody>
    {% for log in logs %}
    <!-- 主行：可点击展开 -->
    <tr class="log-row {% if log.status == 'failed' %}row-warning{% endif %}">
        <td><span class="local-time" data-utc="{{ log.executed_at.isoformat() }}Z">{{ log.executed_at.strftime('%Y-%m-%d %H:%M:%S') }}</span></td>
        <td>
            {% if log.status == 'success' %}
                <span class="status-success">✓ 成功</span>
            {% else %}
                <span class="status-failed">✗ 失败</span>
            {% endif %}
        </td>
        <td>{{ (log.response_summary or log.error_message or '-')[:50] }}...</td>
    </tr>
    <!-- 详情行：默认隐藏 -->
    <tr class="detail-row hidden">
        <td colspan="3">
            <div class="detail-content">
                <div class="detail-item">
                    <span class="detail-label">执行时间：</span>
                    <span class="local-time" data-utc="{{ log.executed_at.isoformat() }}Z">{{ log.executed_at.strftime('%Y-%m-%d %H:%M:%S') }}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">状态：</span>
                    {% if log.status == 'success' %}成功{% else %}失败{% endif %}
                </div>
                {% if log.status == 'success' %}
                <div class="detail-item">
                    <span class="detail-label">响应摘要：</span>
                    <pre style="white-space: pre-wrap;">{{ log.response_summary or '无' }}</pre>
                </div>
                {% else %}
                <div class="detail-item">
                    <span class="detail-label">错误信息：</span>
                    <pre style="white-space: pre-wrap; color: #dc3545;">{{ log.error_message or '未知错误' }}</pre>
                </div>
                {% endif %}
            </div>
        </td>
    </tr>
    {% else %}
    <tr>
        <td colspan="3" style="text-align: center; color: #666;">暂无执行记录</td>
    </tr>
    {% endfor %}
</tbody>
```

#### 展开详情 JavaScript (Task 5)

```javascript
document.querySelectorAll('.log-row').forEach(function(row) {
    row.addEventListener('click', function() {
        var detailRow = this.nextElementSibling;
        if (detailRow && detailRow.classList.contains('detail-row')) {
            detailRow.classList.toggle('hidden');
            this.classList.toggle('expanded');
        }
    });
});
```

### CSS 样式 (Task 7)

**添加位置:** `templates/base.html` 的 `<style>` 块中（约第 30 行位置，与 Story 3.3 样式相邻）

**复用 Story 3.3 样式:** 统计卡片直接使用已有的 `.dashboard`, `.dashboard-card`, `.card-value`, `.card-label` 类

```css
/* 筛选表单样式 */
.filter-form {
    display: flex;
    gap: 15px;
    align-items: flex-end;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.filter-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}
.filter-group label {
    font-size: 0.9em;
    color: #6c757d;
}
.filter-group input, .filter-group select {
    padding: 8px 12px;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    font-size: 1em;
}

/* 分页样式 */
.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    margin-top: 20px;
}
.page-link {
    padding: 8px 16px;
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    text-decoration: none;
    color: #212529;
}
.page-link:hover:not(.disabled) {
    background: #e9ecef;
}
.page-link.disabled {
    color: #6c757d;
    cursor: not-allowed;
}
.page-info {
    color: #6c757d;
}

/* 展开详情样式 */
.log-row {
    cursor: pointer;
}
.log-row:hover {
    background: #f8f9fa;
}
.log-row.expanded {
    background: #e3f2fd;
}
.detail-row {
    background: #f8f9fa;
}
.detail-row.hidden {
    display: none;
}
.detail-content {
    padding: 15px 20px;
    border-left: 3px solid #007bff;
}
.detail-item {
    margin-bottom: 10px;
}
.detail-label {
    font-weight: bold;
    color: #495057;
}
```

### 数据库注意事项

- **请求耗时跳过**: ExecutionLog 表当前没有 `duration` 字段，本故事不实现请求耗时显示功能
- 如需记录耗时，需在后续故事中添加数据库迁移

### 无效参数处理策略

- **page 参数**: `page = max(1, min(page, total_pages))` 确保无效值（0, -1, 超出范围）自动修正为有效值
- **status 参数**: 只接受 "success" 或 "failed"，其他值（如 "invalid"）自动忽略，不应用筛选
- **日期参数**: 无效格式的日期字符串会被 try/except 捕获并忽略

### 时区策略

- 所有日期筛选使用 UTC 时区
- `start_date` 解析为当天 00:00:00 UTC
- `end_date` 解析为次日 00:00:00 UTC（实现 end_date 当天包含）
- 前端使用 JavaScript 将 UTC 时间转换为本地时区显示

### 依赖关系

- **前置条件**: Story 3.1, 3.2, 3.3 已完成（认证和仪表板基础设施就绪）
- **复用 Story 3.3 组件**:
  - `templates/base.html:209-222` - 仪表板 CSS 样式（`.dashboard`, `.dashboard-card`, `.card-value`, `.card-label`）
  - `templates/base.html:215-221` - 状态标签样式（`.status-success`, `.status-failed`）
  - `templates/base.html:220` - 警告行高亮样式（`.row-warning`）

### 架构约束（来源：architecture.md）

1. **全异步架构** - 所有数据库操作使用 async/await
2. **Pydantic 验证** - 查询参数使用 FastAPI 自动验证
3. **SQLAlchemy 2.0** - 使用 `select()` 语法构建查询
4. **loguru 日志** - 错误情况使用 `logger.error()` 记录
5. **UTC 时区** - 所有时间计算使用 UTC

### 测试策略

- 使用 pytest-asyncio 进行异步测试
- 使用 httpx.AsyncClient 测试 Web 路由
- 模拟 ExecutionLog 数据覆盖各种筛选场景
- 测试边界情况：空日志、单页、多页、无效参数

### References

- [Source: _bmad-output/epics.md#Story 3.4]
- [Source: _bmad-output/architecture.md#API Naming Conventions]
- [Source: _bmad-output/architecture.md#Async Patterns]
- [Source: app/web/tasks.py:348-377] - 现有日志查看函数
- [Source: templates/tasks/logs.html] - 现有日志模板
- [Source: 3-3-task-status-dashboard.md] - 仪表板样式参考

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

### Completion Notes List

- ✅ Task 1-2: 实现了 `get_log_stats` 辅助函数和增强的 `view_task_logs` 函数，支持状态筛选、日期范围筛选和分页
- ✅ Task 3-4: 更新了 `templates/tasks/logs.html` 模板，添加了筛选表单和分页导航
- ✅ Task 5: 实现了日志详情展开功能，使用 JavaScript 点击切换显示
- ✅ Task 6: 添加了统计信息卡片，显示总执行次数、成功率和 7 天趋势
- ✅ Task 7: 在 `templates/base.html` 中添加了筛选表单、分页和展开详情的 CSS 样式
- ✅ Task 8: 添加了 13 个新测试用例，覆盖所有筛选、分页和统计功能
- ✅ 所有 202 个测试通过，无回归

### File List

- app/web/tasks.py (modified) - 添加 `get_log_stats` 函数，增强 `view_task_logs` 函数
- templates/tasks/logs.html (modified) - 完全重写，添加统计卡片、筛选表单、分页、详情展开
- templates/base.html (modified) - 添加筛选表单、分页、展开详情的 CSS 样式
- tests/test_web_tasks.py (modified) - 添加 TestLogsFilteringAndPagination 和 TestLogsStatistics 测试类
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified) - 更新 Story 3.4 状态

## Change Log

- 2025-12-23: Story 3.4 实现完成 - 增强的执行日志查看功能，包括状态筛选、日期范围筛选、分页、详情展开和统计信息
