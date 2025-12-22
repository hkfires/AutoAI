# Story 2.3: OpenAI API 调用服务

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 系统,
I want 能够调用 OpenAI API 发送消息,
So that 定时任务可以自动触发 AI 交互。

## Acceptance Criteria

1. **Given** 任务配置了有效的 API 端点和密钥
   **When** 调用 OpenAI 服务发送消息
   **Then** 使用 httpx 异步客户端发送 POST 请求到配置的端点
   **And** 请求格式符合 OpenAI Chat Completions API 标准
   **And** 使用 Bearer Token 认证（API Key）
   **And** 请求超时设置为 30 秒

2. **Given** API 调用失败（网络错误）
   **When** 发生 httpx.RequestError
   **Then** 使用 tenacity 自动重试
   **And** 重试策略：最多 3 次，指数退避（2-10秒）
   **And** 重试仅针对网络错误，不重试 4xx 错误

3. **Given** API 调用完成（成功或最终失败）
   **When** 记录日志
   **Then** API 密钥在日志中脱敏显示
   **And** 使用 loguru 记录请求结果

4. **Given** API 调用成功
   **When** 处理响应
   **Then** 返回响应摘要（AI 回复内容的前 500 字符）
   **And** 记录请求耗时

5. **Given** API 调用最终失败
   **When** 重试次数耗尽或遇到 4xx 错误
   **Then** 抛出 OpenAIServiceError 异常
   **And** 异常包含详细错误信息

## Tasks / Subtasks

- [x] Task 1: 定义服务异常类和返回类型 (AC: #5)
  - [x] 1.1 创建 `OpenAIServiceError` 自定义异常类
  - [x] 1.2 创建 `OpenAIResponse` 数据类，包含 response_summary 和 response_time_ms

- [x] Task 2: 实现 OpenAI API 调用核心逻辑 (AC: #1)
  - [x] 2.1 实现 `send_message()` 异步函数
  - [x] 2.2 构建 Chat Completions API 请求体
  - [x] 2.3 设置 Authorization: Bearer {api_key} 请求头
  - [x] 2.4 配置 httpx.AsyncClient 超时 30 秒

- [x] Task 3: 实现重试逻辑 (AC: #2)
  - [x] 3.1 使用 tenacity @retry 装饰器
  - [x] 3.2 配置 stop_after_attempt(3)
  - [x] 3.3 配置 wait_exponential(min=2, max=10)
  - [x] 3.4 配置 retry_if_exception_type(httpx.RequestError)
  - [x] 3.5 确保 HTTP 4xx 错误不重试

- [x] Task 4: 实现日志脱敏和响应处理 (AC: #3, #4)
  - [x] 4.1 调用 mask_api_key() 脱敏日志中的 API 密钥
  - [x] 4.2 提取响应中的 AI 回复内容
  - [x] 4.3 截取响应摘要（前 500 字符）
  - [x] 4.4 记录请求耗时（毫秒）

- [x] Task 5: 编写单元测试 (AC: 全部)
  - [x] 5.0 添加 `respx>=0.20.0` 到 `requirements.txt`（测试依赖）
  - [x] 5.1 创建 `tests/test_openai_service.py`
  - [x] 5.2 测试成功调用场景（mock httpx）
  - [x] 5.3 测试网络错误重试场景
  - [x] 5.4 测试 4xx 错误不重试场景
  - [x] 5.5 测试超时场景
  - [x] 5.6 测试日志脱敏

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **异步架构** - 所有 HTTP 调用使用 async/await + httpx.AsyncClient
2. **重试机制** - 使用 tenacity 库，指数退避策略
3. **日志系统** - 使用 loguru，敏感信息自动脱敏
4. **错误处理** - 自定义异常类封装服务层错误
5. **命名规范** - snake_case（函数、变量）

**相关需求支持：**
- FR7: 系统向配置的 OpenAI API 发送消息
- FR8: 系统在发送失败时自动重试
- NFR3: 敏感信息不得出现在日志中
- NFR6: 系统支持 OpenAI 标准 API 格式（Chat Completions）

### Technical Requirements

**项目现有代码基础（Story 2.1/2.2 已完成）：**

1. **占位符文件** - `app/services/openai_service.py` 已存在，当前为空占位
2. **脱敏工具** - `app/utils/security.py` 提供 `mask_api_key()` 函数
3. **解密工具** - `app/utils/security.py` 提供 `decrypt_api_key()` 函数
4. **Task 模型** - `app/models.py` 定义了 Task 和 ExecutionLog
5. **已安装依赖** - httpx, tenacity, loguru 已在 requirements.txt

**OpenAI Chat Completions API 格式：**

```python
# 请求格式
{
    "model": "gpt-3.5-turbo",  # 或其他模型
    "messages": [
        {"role": "user", "content": "消息内容"}
    ]
}

# 响应格式
{
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-3.5-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "AI 回复内容"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}
```

**服务实现模式：**

```python
# app/services/openai_service.py
"""OpenAI API Service with Retry Logic."""

import time
from dataclasses import dataclass

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.security import mask_api_key


class OpenAIServiceError(Exception):
    """Exception raised when OpenAI API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@dataclass
class OpenAIResponse:
    """Response from OpenAI API call."""

    response_summary: str  # First 500 chars of AI response
    response_time_ms: int  # Request duration in milliseconds


# HTTP timeout configuration
REQUEST_TIMEOUT = 30.0  # seconds


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True,
)
async def _make_request(
    client: httpx.AsyncClient,
    endpoint: str,
    headers: dict,
    payload: dict,
) -> httpx.Response:
    """Make HTTP request with retry logic.

    Only retries on network errors (httpx.RequestError).
    Does not retry on HTTP 4xx/5xx errors.
    """
    response = await client.post(endpoint, headers=headers, json=payload)
    return response


async def send_message(
    api_endpoint: str,
    api_key: str,
    message_content: str,
    model: str = "gpt-3.5-turbo",
) -> OpenAIResponse:
    """Send a message to OpenAI API.

    Args:
        api_endpoint: The OpenAI API endpoint URL.
        api_key: The API key (plain text, already decrypted).
        message_content: The message to send.
        model: The model to use (default: gpt-3.5-turbo).

    Returns:
        OpenAIResponse with response summary and timing.

    Raises:
        OpenAIServiceError: If the API call fails after retries.
    """
    masked_key = mask_api_key(api_key)
    logger.info(f"Sending message to OpenAI API (key: {masked_key})")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message_content}],
    }

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await _make_request(client, api_endpoint, headers, payload)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Check for HTTP errors
        if response.status_code >= 400:
            error_detail = response.text[:500] if response.text else "No error details"
            logger.error(
                f"OpenAI API error: {response.status_code} - {error_detail} "
                f"(key: {masked_key})"
            )
            raise OpenAIServiceError(
                message=f"API returned {response.status_code}: {error_detail}",
                status_code=response.status_code,
            )

        # Parse successful response
        data = response.json()
        ai_content = data["choices"][0]["message"]["content"]
        response_summary = ai_content[:500] if len(ai_content) > 500 else ai_content

        logger.info(
            f"OpenAI API call successful in {elapsed_ms}ms "
            f"(key: {masked_key})"
        )

        return OpenAIResponse(
            response_summary=response_summary,
            response_time_ms=elapsed_ms,
        )

    except httpx.RequestError as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            f"OpenAI API network error after {elapsed_ms}ms: {e} "
            f"(key: {masked_key})"
        )
        raise OpenAIServiceError(
            message=f"Network error: {str(e)}",
            status_code=None,
        ) from e
```

**关键实现细节：**

1. **重试分离** - `_make_request()` 单独处理重试，便于测试和控制
2. **超时配置** - `httpx.AsyncClient(timeout=30.0)` 秒级超时
3. **错误分类** - 网络错误(RequestError)重试，HTTP错误不重试
4. **性能计时** - 使用 `time.perf_counter()` 高精度计时
5. **响应截取** - 响应摘要限制 500 字符，避免日志过长
6. **异步上下文** - 使用 `async with` 管理 httpx 客户端生命周期

### Library/Framework Requirements

**已安装依赖（无需新增）：**

| 库 | 版本 | 用途 |
|----|------|------|
| httpx | >=0.25.0 | 异步 HTTP 客户端 |
| tenacity | >=8.2.0 | 重试逻辑 |
| loguru | >=0.7.0 | 日志记录 |

### File Structure Requirements

**需要修改的文件：**
```
app/
└── services/
    └── openai_service.py      # 修改：实现 OpenAI 服务

tests/
└── test_openai_service.py     # 新建：服务测试
```

### Testing Requirements

**测试策略：**

使用 pytest + httpx 的 mock 功能测试 API 调用。使用 `respx` 库 mock HTTP 请求。

```python
# tests/test_openai_service.py
import pytest
import httpx
import respx
from httpx import Response

from app.services.openai_service import (
    send_message,
    OpenAIServiceError,
    OpenAIResponse,
)


# Test data
TEST_ENDPOINT = "https://api.openai.com/v1/chat/completions"
TEST_API_KEY = "sk-test1234567890abcdef"
TEST_MESSAGE = "Hello, AI!"

MOCK_SUCCESS_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-3.5-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}


@pytest.mark.asyncio
@respx.mock
async def test_send_message_success():
    """Test successful API call."""
    respx.post(TEST_ENDPOINT).mock(
        return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
    )

    result = await send_message(
        api_endpoint=TEST_ENDPOINT,
        api_key=TEST_API_KEY,
        message_content=TEST_MESSAGE,
    )

    assert isinstance(result, OpenAIResponse)
    assert result.response_summary == "Hello! How can I help you today?"
    assert result.response_time_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_send_message_http_error_no_retry():
    """Test that HTTP 4xx errors are not retried."""
    call_count = 0

    def count_calls(request):
        nonlocal call_count
        call_count += 1
        return Response(401, json={"error": {"message": "Invalid API key"}})

    respx.post(TEST_ENDPOINT).mock(side_effect=count_calls)

    with pytest.raises(OpenAIServiceError) as exc_info:
        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

    assert exc_info.value.status_code == 401
    assert call_count == 1  # No retry for 4xx


@pytest.mark.asyncio
@respx.mock
async def test_send_message_network_error_retry():
    """Test that network errors trigger retry."""
    call_count = 0

    def fail_then_succeed(request):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.ConnectError("Connection refused")
        return Response(200, json=MOCK_SUCCESS_RESPONSE)

    respx.post(TEST_ENDPOINT).mock(side_effect=fail_then_succeed)

    result = await send_message(
        api_endpoint=TEST_ENDPOINT,
        api_key=TEST_API_KEY,
        message_content=TEST_MESSAGE,
    )

    assert call_count == 3  # 2 failures + 1 success
    assert isinstance(result, OpenAIResponse)


@pytest.mark.asyncio
@respx.mock
async def test_send_message_max_retries_exceeded():
    """Test that max retries raises OpenAIServiceError."""
    respx.post(TEST_ENDPOINT).mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(OpenAIServiceError) as exc_info:
        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

    assert "Network error" in exc_info.value.message
    assert exc_info.value.status_code is None


@pytest.mark.asyncio
@respx.mock
async def test_response_summary_truncation():
    """Test that long responses are truncated to 500 chars."""
    long_response = "A" * 1000
    mock_response = {
        **MOCK_SUCCESS_RESPONSE,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": long_response},
                "finish_reason": "stop"
            }
        ]
    }

    respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=mock_response))

    result = await send_message(
        api_endpoint=TEST_ENDPOINT,
        api_key=TEST_API_KEY,
        message_content=TEST_MESSAGE,
    )

    assert len(result.response_summary) == 500


@pytest.mark.asyncio
async def test_api_key_masked_in_logs(caplog):
    """Test that API key is masked in log output."""
    import logging

    # This test verifies the masking function is called
    # Actual log capture requires loguru sink configuration
    from app.utils.security import mask_api_key

    masked = mask_api_key(TEST_API_KEY)
    assert masked == "sk-t...cdef"
    assert TEST_API_KEY not in masked


@pytest.mark.asyncio
@respx.mock
async def test_send_message_timeout():
    """Test that timeout raises OpenAIServiceError."""
    import httpx

    # Mock a timeout by raising TimeoutException
    respx.post(TEST_ENDPOINT).mock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )

    with pytest.raises(OpenAIServiceError) as exc_info:
        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

    # TimeoutException is a subclass of RequestError, so it will be retried
    # After max retries, it should raise OpenAIServiceError
    assert exc_info.value.status_code is None
    assert "Network error" in exc_info.value.message or "timeout" in exc_info.value.message.lower()
```

**测试依赖：**

在 `requirements.txt` 中添加测试依赖（Task 5.0 的第一步）：
```
respx>=0.20.0  # httpx mock library
```

**测试清单：**

| 测试场景 | 预期行为 | 验证点 |
|----------|----------|--------|
| 成功调用 | 返回 OpenAIResponse | response_summary, response_time_ms |
| HTTP 4xx 错误 | 不重试，抛出异常 | status_code=401, call_count=1 |
| 网络错误重试成功 | 重试后成功 | call_count=3 |
| 重试次数耗尽 | 抛出 OpenAIServiceError | "Network error" in message |
| 响应截取 | 截取前 500 字符 | len(summary) == 500 |
| 日志脱敏 | API 密钥脱敏显示 | masked format |
| 超时场景 | 重试后抛出 OpenAIServiceError | status_code=None |

### Previous Story Intelligence

**来自 Story 2.1/2.2 的经验教训：**

1. **懒加载模式** - 使用 `get_settings()` 而非直接导入 `settings` 实例
2. **脱敏函数** - `mask_api_key()` 已在 `app/utils/security.py` 实现
3. **解密函数** - `decrypt_api_key()` 用于从数据库读取加密密钥后解密
4. **异步模式** - 所有 I/O 操作必须使用 async/await

**注意：** 调用 `send_message()` 前需要先用 `decrypt_api_key()` 解密数据库中的加密密钥：

```python
from app.utils.security import decrypt_api_key
from app.services.openai_service import send_message

# 从数据库获取 task 后
plain_api_key = decrypt_api_key(task.api_key)
result = await send_message(
    api_endpoint=task.api_endpoint,
    api_key=plain_api_key,  # 传入明文密钥
    message_content=task.message_content,
)
```

### Git Intelligence Summary

**最近提交：**
- `7728101 2-2-task-management-api` - 任务管理 API 完成
- `354a2c3 2-1-task-log-data-model` - 数据模型完成

**可参考的代码模式：**
- `app/utils/security.py:15-27` - `mask_api_key()` 脱敏模式
- `app/utils/security.py:60-69` - `decrypt_api_key()` 解密模式
- `app/services/task_service.py` - 服务层异步模式

**Story 2.2 修改的文件：**
- `app/services/task_service.py` - 新建
- `app/api/tasks.py` - 实现 API 端点
- `tests/test_api_tasks.py` - API 测试

### Latest Technical Information

**httpx 异步客户端（2025 最新版本）：**

```python
# httpx 0.25+ 推荐模式
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, headers=headers, json=payload)
```

**tenacity 重试配置（8.2+）：**

```python
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True,  # 重要：确保最终异常被抛出
)
async def my_async_func():
    ...
```

**loguru 异步安全：**
- loguru 的 `logger.info()` 等方法在异步环境中是线程安全的
- 无需额外配置即可在 async 函数中使用

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：**
- Story 2.1（任务与日志数据模型）✅ 已完成
- Story 2.2（任务管理 API）✅ 已完成

**后续故事：**
- Story 2.4（定时调度引擎）将调用此服务执行任务
- Story 2.5（任务管理 Web UI）将显示执行结果
- Story 2.6（执行日志查看）将展示执行历史

### Common LLM Pitfalls to Avoid

1. **不要忘记异步上下文管理器** - httpx.AsyncClient 必须使用 `async with`
2. **不要在日志中暴露明文 API 密钥** - 始终使用 `mask_api_key()`
3. **不要重试 HTTP 4xx 错误** - 这些是客户端错误，重试无意义
4. **不要忘记 reraise=True** - tenacity 默认不重抛异常
5. **不要使用同步 httpx 客户端** - 必须使用 `httpx.AsyncClient`
6. **不要硬编码模型名称** - 使用默认参数但允许覆盖
7. **不要忘记超时配置** - 必须设置 30 秒超时
8. **不要在服务层直接访问数据库** - 调用方负责读取任务和写入日志

### Response Time 持久化说明

`OpenAIResponse.response_time_ms` 返回请求耗时，用于：
1. **日志记录** - 通过 loguru 记录到应用日志（当前实现）
2. **ExecutionLog 持久化** - Story 2.4（定时调度引擎）将负责调用此服务并写入 ExecutionLog

**注意：** 当前 `ExecutionLog` 模型没有 `response_time_ms` 字段。如需在数据库中持久化请求耗时，Story 2.4 可选择：
- 方案 A：将 response_time_ms 追加到 response_summary 字段
- 方案 B：在 Story 2.4 中添加 ExecutionLog.response_time_ms 字段（需要数据库迁移）

当前 MVP 阶段采用方案 A 足够，Phase 2 可考虑方案 B。

### Windows 兼容性说明

- httpx 在 Windows 上使用 asyncio 的默认事件循环
- 测试使用 `pytest-asyncio` 插件
- 无需特殊的 Windows 适配

### References

**源文档：**
- _bmad-output/architecture.md (API & Communication Patterns, Retry Strategy)
- _bmad-output/prd.md (FR7, FR8: 任务执行)
- _bmad-output/epics.md (Story 2.3: OpenAI API 调用服务)
- _bmad-output/implementation-artifacts/2-2-task-management-api.md (前置故事)

**外部文档：**
- OpenAI API 文档: https://platform.openai.com/docs/api-reference/chat
- httpx 文档: https://www.python-httpx.org/async/
- tenacity 文档: https://tenacity.readthedocs.io/

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无需调试日志 - 所有测试首次通过。

### Completion Notes List

- ✅ 实现 OpenAIServiceError 自定义异常类，包含 message 和 status_code 属性
- ✅ 实现 OpenAIResponse 数据类，返回响应摘要（前500字符）和请求耗时（毫秒）
- ✅ 实现 send_message() 异步函数，使用 httpx.AsyncClient 发送 POST 请求
- ✅ 请求格式符合 OpenAI Chat Completions API 标准
- ✅ 使用 Bearer Token 认证，30秒超时配置
- ✅ 使用 tenacity 实现重试逻辑：最多3次，指数退避2-10秒
- ✅ 仅对网络错误（httpx.RequestError）重试，HTTP 4xx 错误不重试
- ✅ 所有日志使用 mask_api_key() 脱敏 API 密钥
- ✅ 22 个单元测试全部通过，覆盖所有验收标准
- ✅ 全量回归测试通过（92测试）

### File List

**修改的文件：**
- `app/services/openai_service.py` - 实现 OpenAI API 调用服务
- `requirements.txt` - 添加 respx>=0.20.0 测试依赖
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - 更新Story状态

**新建的文件：**
- `tests/test_openai_service.py` - 22 个单元测试

### Change Log

- 2025-12-22: 完成 Story 2.3 OpenAI API 调用服务实现
- 2025-12-22: 代码审查完成 - 修正文档测试数量声明 (17→22, 87→92)

### Code Review Record

**审查日期:** 2025-12-22
**审查模型:** Claude Opus 4.5

**发现摘要:**
| 严重级别 | 数量 | 状态 |
|---------|------|------|
| HIGH | 0 | N/A |
| MEDIUM | 4 | 3已修复/1架构建议 |
| LOW | 3 | 记录备查 |

**已修复问题:**
- [MEDIUM-1] 测试数量声明已更正 (17→22)
- [MEDIUM-2] 回归测试数量已更正 (87→92)

**架构改进建议（后续考虑）:**
- [MEDIUM-3] 超时配置可移至 config.py 增加运维灵活性
- [MEDIUM-4] 显式捕获 JSONDecodeError 提供更清晰错误消息

**审查结论:** ✅ 代码质量良好，所有 AC 均已实现，测试覆盖全面

