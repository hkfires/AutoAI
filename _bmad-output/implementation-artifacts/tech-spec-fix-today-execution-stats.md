# Tech-Spec: 修复"今日执行"统计和时间显示的时区问题

**Created:** 2025-12-26
**Status:** Completed

## Overview

### Problem Statement

任务列表页面的统计数据和时间显示存在时区问题：

1. **"今日执行"统计为 0**：系统使用 UTC 时区计算"今日"，但用户在中国（UTC+8）。例如：
   - 北京时间 2025-12-26 08:00 执行的任务
   - 对应 UTC 2025-12-25 24:00
   - 代码用 UTC 的 12-26 00:00 作为"今日"起点，导致统计错误

2. **"最后执行"时间显示不正确**：显示的是 UTC 时间而非北京时间，导致用户看到的时间比实际早 8 小时

### Solution

统一配置为 **UTC+8（北京时间）**：
- 后端统计使用 UTC+8 计算"今日"起止时间
- 时间显示转换为 UTC+8 显示

### Scope

**In Scope:**
- 添加 UTC+8 时区常量配置
- 修复 `get_dashboard_stats()` 函数中的"今日"日期计算逻辑
- 修复任务列表中 `last_executed_at` 的时区转换显示

**Out of Scope:**
- 修改执行日志存储格式（继续使用 UTC 存储）
- 历史数据迁移

## Context for Development

### Codebase Patterns

- **时间存储**：所有时间使用 UTC 存储（`datetime.now(timezone.utc)`）
- **时间显示**：日志页面使用 JavaScript 的 `local-time` 类进行客户端时区转换

### Files to Reference

| File | Purpose |
|------|---------|
| `app/web/tasks.py:30-65` | `get_dashboard_stats()` 函数 - 今日统计计算 |
| `app/web/tasks.py:116-128` | 任务列表构建 - last_executed_at 格式化 |
| `templates/tasks/list.html:63` | 列表页时间显示 |

### Technical Decisions

1. **时区配置**：使用固定的 UTC+8 时区（`timezone(timedelta(hours=8))`）
2. **存储保持 UTC**：继续使用 UTC 存储，只在统计和显示时转换为 UTC+8
3. **后端统一处理**：时区转换在后端完成，前端直接显示

## Implementation Plan

### Tasks

- [x] Task 1: 在 `app/web/tasks.py` 顶部添加 UTC+8 时区常量
- [x] Task 2: 修改 `get_dashboard_stats()` 使用 UTC+8 计算今日起点
- [x] Task 3: 修改任务列表中 `last_executed_at` 转换为 UTC+8 显示
- [x] Task 4: 验证修复效果

### Detailed Implementation

#### Task 1: 添加时区常量

**文件**: `app/web/tasks.py`

在 imports 后添加：
```python
# 北京时间 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))
```

#### Task 2: 修改统计函数

**文件**: `app/web/tasks.py`

```python
# 修改前 (line 32):
today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

# 修改后:
# 获取北京时间的今日起点，转换为 UTC 用于数据库查询
china_now = datetime.now(CHINA_TZ)
china_today_start = china_now.replace(hour=0, minute=0, second=0, microsecond=0)
today_start = china_today_start.astimezone(timezone.utc)
```

#### Task 3: 修改时间格式化

**文件**: `app/web/tasks.py`

```python
# 修改前 (line 124-125):
"last_executed_at": last_executed_at.strftime("%Y-%m-%d %H:%M")
                   if last_executed_at else None,

# 修改后: UTC 转换为北京时间后格式化
"last_executed_at": last_executed_at.replace(tzinfo=timezone.utc)
                   .astimezone(CHINA_TZ)
                   .strftime("%Y-%m-%d %H:%M")
                   if last_executed_at else None,
```

### Acceptance Criteria

- [x] AC 1: Given 任务在北京时间今日执行过, When 访问任务列表页, Then "今日执行"统计 > 0
- [x] AC 2: Given 任务在 UTC 时间 14:48 (北京时间 22:48) 执行, When 查看任务列表, Then "最后执行"显示 "22:48"
- [x] AC 3: Given 跨日边界执行（如北京时间凌晨 1:00 = UTC 17:00 前一天）, When 计算今日统计, Then 正确计入当日

## Additional Context

### Dependencies

- 无新增依赖（使用标准库 `datetime`）

### Testing Strategy

1. 手动测试：验证统计和显示是否正确
2. 可选：添加单元测试模拟不同时区场景

### Notes

- 保持 UTC 存储是最佳实践，只在统计和展示层做时区转换
- 如果未来需要支持多时区，可以将 `CHINA_TZ` 改为配置项

## Review Notes

- Adversarial review completed
- Findings: 10 total, 4 fixed, 6 skipped (undecided/by-design)
- Resolution approach: auto-fix
- Fixed: F2 (类型注解), F3 (代码可读性), F4 (注释语言统一为英文), F5 (跨日边界测试)
