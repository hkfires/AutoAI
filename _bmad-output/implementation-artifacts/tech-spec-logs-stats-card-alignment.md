# Tech-Spec: 日志统计卡片样式对齐修复

**Created:** 2025-12-26
**Status:** Implementation Complete

## Overview

### Problem Statement

执行日志页面的统计卡片存在样式不一致问题：
- 左边两个卡片显示数字（如 `3`、`100%`）+ 标签，格式统一
- 右边卡片显示完整句子（`"共执行 3 次，成功 3 次"`），与其他卡片格式不一致
- 右边卡片使用了 `font-size: 1em` 缩小字体，导致视觉上不对齐

### Solution

将右侧卡片改为与左侧一致的格式：
- 主数字显示为 `3 / 3` 格式（执行次数 / 成功次数）
- 标签改为 `最近7天 执行/成功`
- 移除特殊字体大小样式，使用统一的 `card-value` 样式

**修改前：**
```
| 3            | 100%      | 共执行 3 次，成功 3 次 |
| 总执行次数   | 成功率    | 最近 7 天              |
```

**修改后：**
```
| 3            | 100%      | 3 / 3                  |
| 总执行次数   | 成功率    | 最近7天 执行/成功      |
```

### Scope (In/Out)

**In Scope:**
- 修改后端返回的统计数据格式
- 修改前端模板显示格式

**Out Scope:**
- 卡片的 CSS 样式（已有统一样式）
- 其他页面的统计显示

## Context for Development

### Codebase Patterns

- 后端使用 FastAPI + SQLAlchemy async
- 前端使用 Jinja2 模板 + 简单 CSS
- 统计数据通过 `get_task_stats()` 函数获取

### Files to Reference

1. `app/web/tasks.py` - 后端统计逻辑（第 370-401 行）
2. `templates/tasks/logs.html` - 前端模板（第 22-25 行）

### Technical Decisions

- 后端返回两个独立字段 `recent_count` 和 `recent_success`，而不是格式化字符串
- 前端模板中组合显示为 `{{ stats.recent_count }} / {{ stats.recent_success }}`
- 当无数据时显示 `-- / --`

## Implementation Plan

### Tasks

- [x] Task 1: 修改 `app/web/tasks.py` 中的 `get_task_stats()` 函数
  - 将 `recent_trend` 字段替换为 `recent_count` 和 `recent_success` 两个字段
  - 修改返回字典结构

- [x] Task 2: 修改 `templates/tasks/logs.html` 模板
  - 更新第三个卡片的显示格式
  - 移除 `font-size: 1em` 内联样式
  - 更新标签文字

### Acceptance Criteria

- [x] AC 1: 三个统计卡片的数字字体大小一致
- [x] AC 2: 右侧卡片显示格式为 `X / Y`（执行次数 / 成功次数）
- [x] AC 3: 标签显示为 `最近7天 执行/成功`
- [x] AC 4: 无数据时显示 `-- / --`
- [x] AC 5: 现有测试通过

## Additional Context

### Dependencies

无新依赖

### Testing Strategy

- 运行现有测试确保不破坏功能
- 手动验证页面显示效果

### Notes

这是一个纯 UI 改进，不涉及业务逻辑变更。
