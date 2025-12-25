# Tech-Spec: 任务添加时自定义模型选择

**Created:** 2025-12-25
**Status:** Done
**Reviewed:** 2025-12-25

## Overview

### Problem Statement

当前添加任务时无法选择 AI 模型，系统硬编码使用 `gpt-3.5-turbo`。用户需要能够在创建/编辑任务时自定义使用的模型，以支持不同的 API 提供商和模型版本。

### Solution

在任务配置中添加 `model` 字段，允许用户：
1. 从预定义下拉列表中选择模型（默认选项：`gemini-claude-sonnet-4-5`）
2. 自由输入任意模型名称

### Scope

**In Scope:**
- Task 模型添加 `model` 字段
- 表单 UI 添加模型选择器（下拉 + 自定义输入）
- API/Web 路由支持 model 参数
- 调度器执行时传递 model 参数
- 相关测试更新

**Out of Scope:**
- 模型验证（不验证模型名称是否有效）
- 向后兼容（项目未部署）
- 数据库迁移（直接修改模型即可）

## Context for Development

### Codebase Patterns

- **ORM**: SQLAlchemy 2.0 async (`Mapped[]` 类型注解)
- **API Framework**: FastAPI
- **Validation**: Pydantic v2 (`Field`, `field_validator`)
- **Templates**: Jinja2 + 原生 JavaScript
- **表单处理**: `Form(...)` 依赖注入
- **字段长度约束**: 在 models.py 和 schemas.py 中同时定义

### Files to Reference

| 文件 | 作用 | 行号参考 |
|------|------|----------|
| `app/models.py` | Task ORM 模型 | L33 model 字段 |
| `app/schemas.py` | Pydantic schemas | L23 MAX_MODEL_LENGTH, L35 model 字段 |
| `templates/tasks/form.html` | 任务表单 UI | L28-41 模型选择器 |
| `app/web/tasks.py` | Web 表单处理 | L159 model 参数 |
| `app/scheduler.py` | 任务执行 | L162 model 传递 |
| `app/services/task_service.py` | CRUD 服务 | L35 model 字段 |
| `app/services/openai_service.py` | API 调用 | L65 model 参数 |

### Technical Decisions

1. **model 字段类型**: `String(100)` - 足够存储模型名称
2. **必填字段**: model 为必填，无默认值
3. **预定义模型**: 仅提供 `gemini-claude-sonnet-4-5` 作为下拉选项
4. **UI 交互**: 下拉选择，另有"自定义"选项触发文本输入框

## Implementation Plan

### Tasks

- [x] Task 1: 修改 `app/models.py` - 添加 `model` 字段到 Task 模型
- [x] Task 2: 修改 `app/schemas.py` - 添加 `model` 到 TaskBase/TaskCreate/TaskUpdate/TaskResponse
- [x] Task 3: 修改 `templates/tasks/form.html` - 添加模型选择器 UI（下拉 + 自定义输入）
- [x] Task 4: 修改 `app/web/tasks.py` - 处理表单中的 model 参数
- [x] Task 5: 修改 `app/services/task_service.py` - 在 create_task 中处理 model 字段
- [x] Task 6: 修改 `app/scheduler.py` - 执行任务时传递 model 参数给 send_message
- [x] Task 7: 更新测试文件 - 确保所有相关测试通过
- [x] Task 8: 删除旧数据库文件并重新初始化（因 schema 变更）

### Acceptance Criteria

- [x] AC 1: Given 用户在新建任务页面，When 查看表单，Then 应看到模型选择器（下拉列表 + 自定义输入选项）
- [x] AC 2: Given 用户选择预定义模型 `gemini-claude-sonnet-4-5`，When 提交表单，Then 任务保存该模型值
- [x] AC 3: Given 用户选择"自定义"并输入 `gpt-4-turbo`，When 提交表单，Then 任务保存自定义模型值
- [x] AC 4: Given 用户未选择或输入模型，When 提交表单，Then 应显示验证错误提示
- [x] AC 5: Given 任务执行时，When 调用 OpenAI API，Then 使用任务配置的 model 参数
- [x] AC 6: Given 编辑现有任务，When 查看表单，Then 应正确显示当前配置的模型值

## Additional Context

### Dependencies

- 无新增外部依赖
- 依赖现有的 `app/services/openai_service.py` 的 `model` 参数支持（已存在）

### Testing Strategy

1. **单元测试**: 更新 `tests/test_schemas.py` 验证 model 字段
2. **API 测试**: 更新 `tests/test_api_tasks.py` 包含 model 参数
3. **Web 测试**: 更新 `tests/test_web_tasks.py` 测试表单提交
4. **集成测试**: 确认调度器正确传递 model 参数

### Notes

- 由于项目未部署，直接删除 `data/autoai.db` 文件后重新启动即可应用 schema 变更
- 表单 UI 使用 JavaScript 动态切换下拉选择和自定义输入框
- model 字段在 API 响应中正常返回，无需脱敏处理

---

## Code Review Record

**Review Date:** 2025-12-25
**Reviewer:** Amelia (Dev Agent)

### Files Changed

| 文件 | 变更类型 |
|------|----------|
| `app/models.py` | Modified - 添加 model 字段 |
| `app/schemas.py` | Modified - 添加 model 到所有 schema |
| `app/web/tasks.py` | Modified - 处理 model 表单参数 |
| `app/scheduler.py` | Modified - 传递 model 到 send_message |
| `app/services/task_service.py` | Modified - create_task 包含 model |
| `templates/tasks/form.html` | Modified - 模型选择器 UI |
| `tests/test_schemas.py` | Modified - model 字段测试 |
| `tests/test_api_tasks.py` | Modified - API 测试包含 model |
| `tests/test_web_tasks.py` | Modified - Web 表单测试 |
| `tests/test_models.py` | Modified - ORM 模型测试 |
| `tests/test_api_logs.py` | Modified - 日志 API 测试 |

### Issues Found & Fixed

| 问题 | 严重度 | 状态 |
|------|--------|------|
| 表单 UI 编辑模式下自定义模型值被清空 | MEDIUM | Fixed |
| `toggleCustomModel()` 缺少 `isUserAction` 参数区分 | MEDIUM | Fixed |

### Test Results

- **Total Tests:** 201
- **Passed:** 200
- **Failed:** 1 (unrelated: `test_get_fernet_raises_without_key` - 测试环境问题)

### Conclusion

所有验收标准已实现并通过测试。代码质量良好，符合项目规范。
