# Tech-Spec: 支持图像生成模型响应

**Created:** 2025-12-27
**Status:** Completed

## Overview

### Problem Statement

当 OpenAI 兼容 API 返回图像生成响应时（如 `gemini-3-pro-image`），响应的 `content` 字段为 `null`，而图像数据在 `images` 数组中。当前代码在 `openai_service.py:137` 对 `None` 值调用 `len()` 导致崩溃：

```
Unexpected error: object of type 'NoneType' has no len()
```

### Solution

修改 `send_message` 函数，检测图像响应并生成适当的文本摘要：
- 当 `content` 为 `null` 但存在 `images` 数组时，标记为图像生成成功
- 生成摘要格式：`[图像生成成功] 共 N 张图片`
- 保持现有数据库 schema 不变（只存储文本摘要）

### Scope (In/Out)

**In Scope:**
- 修改 `openai_service.py` 中的响应解析逻辑
- 添加图像响应的测试用例

**Out of Scope:**
- 数据库 schema 变更
- 图像 URL 存储
- 前端图像展示

## Context for Development

### Codebase Patterns

- **异步模式**: 使用 `async/await`
- **类型注解**: 完整的 type hints
- **日志**: 使用 `loguru.logger`
- **测试**: pytest + respx mock

### Files to Reference

| 文件 | 作用 |
|------|------|
| `app/services/openai_service.py` | 主要修改文件 |
| `tests/test_openai_service.py` | 添加测试用例 |
| `app/scheduler.py:195-199` | 异常捕获位置（无需修改） |

### Technical Decisions

1. **响应优先级**: `content` > `images` > 报错
2. **摘要格式**: 中文格式 `[图像生成成功] 共 N 张图片`
3. **reasoning_content**: 不使用，仅作为模型内部推理内容

## Implementation Plan

### Tasks

- [x] Task 1: 修改 `openai_service.py` 响应解析逻辑
  - 在第 117 行后添加图像响应检测
  - 修改第 137 行的空值处理

- [x] Task 2: 添加测试用例到 `test_openai_service.py`
  - 测试 `content=null` + `images` 存在的情况
  - 测试 `content=null` + `images` 为空/不存在的情况

### Acceptance Criteria

- [x] AC 1: Given 图像生成模型返回 `content=null` 和 `images` 数组，When 调用 `send_message`，Then 返回成功响应，摘要包含图片数量
- [x] AC 2: Given `content=null` 且无 `images`，When 调用 `send_message`，Then 抛出 `OpenAIServiceError`
- [x] AC 3: Given 正常文本响应，When 调用 `send_message`，Then 行为不变（向后兼容）
- [x] AC 4: 所有现有测试继续通过

## Additional Context

### Dependencies

无新增依赖

### Testing Strategy

```python
# 新增测试用例示例
MOCK_IMAGE_RESPONSE = {
    "id": "test",
    "object": "chat.completion",
    "created": 0,
    "model": "gemini-3-pro-image",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": None,
            "images": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}, "index": 0},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}, "index": 1}
            ]
        },
        "finish_reason": "stop"
    }]
}
```

### Notes

- 图像响应格式可能因不同 API 提供商而异，当前实现基于用户提供的 Gemini 格式
- 未来可能需要支持更多响应格式（如 `tool_calls`）

## Review Notes

- Adversarial review completed
- Findings: 10 total, 3 fixed, 7 skipped
- Resolution approach: auto-fix
- Fixed: F2 (冗余长度检查), F4/F8 (添加类型检查)
- Skipped: F1 (符合设计), F3/F5/F6/F7/F9/F10 (噪声/不确定/可接受)
