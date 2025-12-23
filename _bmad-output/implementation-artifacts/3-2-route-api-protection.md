# Story 3.2: 路由与 API 保护

Status: done

<!-- Validated: 2025-12-23 -->

## Story

As a 系统管理员,
I want 所有管理功能都需要登录才能访问,
so that API 密钥和任务配置得到安全保护。

## Acceptance Criteria

1. **AC1: Web 页面未登录重定向**
   - Given 用户未登录
   - When 访问以下 Web 页面
   - Then 返回 302 重定向到登录页面：
     - 任务列表页 (`/`)
     - 新建任务页 (`/tasks/new`)
     - 编辑任务页 (`/tasks/{id}/edit`)
     - 任务日志页 (`/tasks/{id}/logs`)

2. **AC2: API 端点未登录返回 401**
   - Given 用户未登录
   - When 调用以下 API 端点
   - Then 返回 401 Unauthorized：
     - `GET /api/tasks`
     - `POST /api/tasks`
     - `GET /api/tasks/{id}`
     - `PUT /api/tasks/{id}`
     - `DELETE /api/tasks/{id}`
     - `GET /api/tasks/{id}/logs`

3. **AC3: 已登录用户正常访问**
   - Given 用户已登录（有效 session cookie）
   - When 访问受保护的页面或 API
   - Then 正常返回内容

4. **AC4: 登录页面无需认证**
   - Given 任何用户
   - When 访问登录页面 (`/login`)
   - Then 不需要认证即可访问

5. **AC5: API 错误响应格式**
   - Given 用户未登录调用 API
   - When 返回 401 错误
   - Then 响应体格式为 `{"detail": "Not authenticated"}`

## Tasks / Subtasks

- [x] Task 1: 创建认证依赖函数和异常处理器 (AC: #1, #2, #3)
  - [x] 1.1 在 `app/web/auth.py` 创建 `AuthRedirectException` 异常类
  - [x] 1.2 在 `app/web/auth.py` 创建 `require_auth_web()` 依赖函数（抛出 AuthRedirectException）
  - [x] 1.3 在 `app/web/auth.py` 创建 `require_auth_api()` 依赖函数（抛出 HTTPException 401）
  - [x] 1.4 在 `app/main.py` 注册 `AuthRedirectException` 异常处理器（重定向到 /login）

- [x] Task 2: 保护 Web 路由 (AC: #1, #3)
  - [x] 2.1 修改 `app/web/tasks.py` 的 `list_tasks` 路由添加认证依赖
  - [x] 2.2 修改 `app/web/tasks.py` 的 `new_task_form` 路由添加认证依赖
  - [x] 2.3 修改 `app/web/tasks.py` 的 `create_task` 路由添加认证依赖
  - [x] 2.4 修改 `app/web/tasks.py` 的 `edit_task_form` 路由添加认证依赖
  - [x] 2.5 修改 `app/web/tasks.py` 的 `update_task` 路由添加认证依赖
  - [x] 2.6 修改 `app/web/tasks.py` 的 `delete_task` 路由添加认证依赖
  - [x] 2.7 修改 `app/web/tasks.py` 的 `view_task_logs` 路由添加认证依赖

- [x] Task 3: 保护 API 路由 (AC: #2, #3, #5)
  - [x] 3.1 修改 `app/api/tasks.py` 的 `create_task` 路由添加认证依赖
  - [x] 3.2 修改 `app/api/tasks.py` 的 `get_tasks` 路由添加认证依赖
  - [x] 3.3 修改 `app/api/tasks.py` 的 `get_task` 路由添加认证依赖
  - [x] 3.4 修改 `app/api/tasks.py` 的 `update_task` 路由添加认证依赖
  - [x] 3.5 修改 `app/api/tasks.py` 的 `delete_task` 路由添加认证依赖
  - [x] 3.6 修改 `app/api/tasks.py` 的 `get_task_logs` 路由添加认证依赖

- [x] Task 4: 验证公开路由无需认证 (AC: #4)
  - [x] 4.1 确认 `/login` 路由不添加认证依赖（已在 Story 3.1 实现）
  - [x] 4.2 确认 `/logout` 路由不添加认证依赖（清除 cookie 操作，任何状态都应可调用）

- [x] Task 5: 编写测试 (AC: #1, #2, #3, #4, #5)
  - [x] 5.1 更新 `tests/test_auth.py` 添加 Web 路由保护测试
  - [x] 5.2 创建 `tests/test_api_protection.py` 添加 API 保护测试
  - [x] 5.3 测试未登录访问 Web 页面返回 302 + Location: /login
  - [x] 5.4 测试未登录访问 API 返回 401 + 正确响应体
  - [x] 5.5 测试已登录访问受保护资源成功
  - [x] 5.6 测试登录页面无需认证

## Dev Notes

### 技术实现要点

**认证依赖函数设计：**

Story 3.1 已实现 `verify_session_token()` 函数。本 Story 创建两个依赖函数：

1. **`require_auth_web()`** - Web 页面路由专用
   - 检查 session cookie 有效性
   - 无效时抛出 `AuthRedirectException`（由异常处理器转换为 302 重定向）
   - 有效时返回 `True`

2. **`require_auth_api()`** - API 路由专用
   - 检查 session cookie 有效性
   - 无效时抛出 `HTTPException(status_code=401, detail="Not authenticated")`
   - 有效时返回 `True`

**关键：FastAPI 依赖函数不能直接返回 Response 对象**，必须使用异常 + 异常处理器模式实现重定向。

### 项目结构变更

```
app/
├── main.py               # 修改：注册 AuthRedirectException 异常处理器
├── web/
│   ├── auth.py           # 修改：添加 AuthRedirectException, require_auth_web, require_auth_api
│   └── tasks.py          # 修改：所有路由添加认证依赖
├── api/
│   └── tasks.py          # 修改：所有路由添加认证依赖

tests/
├── test_auth.py          # 修改：添加 Web 路由保护测试
└── test_api_protection.py # 新增：API 保护测试
```

### 代码模式参考

**认证异常和依赖函数（app/web/auth.py 添加）：**

```python
from fastapi import Cookie, HTTPException

class AuthRedirectException(Exception):
    """未认证用户访问受保护 Web 页面时抛出，触发重定向到登录页。"""
    pass


def require_auth_web(session: str | None = Cookie(default=None)) -> bool:
    """Web 页面认证依赖 - 未登录抛出 AuthRedirectException。

    Args:
        session: Session cookie value.

    Returns:
        True if authenticated.

    Raises:
        AuthRedirectException: If not authenticated (handled by exception handler).
    """
    if not (verify_session_token(session) if session else False):
        raise AuthRedirectException()
    return True


def require_auth_api(session: str | None = Cookie(default=None)) -> bool:
    """API 认证依赖 - 未登录返回 401。

    Args:
        session: Session cookie value.

    Returns:
        True if authenticated.

    Raises:
        HTTPException: 401 Unauthorized if not authenticated.
    """
    if not (verify_session_token(session) if session else False):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True
```

**注册异常处理器（app/main.py 添加）：**

```python
from fastapi import Request
from fastapi.responses import RedirectResponse
from app.web.auth import AuthRedirectException

@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request: Request, exc: AuthRedirectException):
    """Handle auth redirect exception by redirecting to login page."""
    return RedirectResponse(url="/login", status_code=302)
```

**Web 路由添加依赖（app/web/tasks.py）：**

```python
from app.web.auth import render_template, require_auth_web

@router.get("/")
async def list_tasks(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_web),  # 添加认证依赖
    message: Optional[str] = None,
    message_type: str = "success",
):
    # ... 现有代码不变
```

**API 路由添加依赖（app/api/tasks.py）：**

```python
from app.web.auth import require_auth_api

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_auth_api),  # 添加认证依赖
):
    # ... 现有代码不变
```

**测试模式（tests/test_api_protection.py）：**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def unauthenticated_client():
    """Create test client without authentication."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.mark.asyncio
async def test_api_tasks_requires_auth(unauthenticated_client):
    """Test that /api/tasks requires authentication."""
    async with unauthenticated_client as client:
        response = await client.get("/api/tasks")
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_web_page_redirects_to_login(unauthenticated_client):
    """Test that web pages redirect to /login when not authenticated."""
    async with unauthenticated_client as client:
        response = await client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"
```

### 前一个 Story 的关键实现

Story 3.1 已完成（`app/web/auth.py`）：
- `verify_session_token(token: str) -> bool` - 验证 session token
- `get_current_user(session: str | None) -> bool` - 获取认证状态
- `SESSION_COOKIE_NAME = "session"` - Cookie 名称常量

### 测试策略

- 使用 `pytest` + `pytest-asyncio` + `httpx.AsyncClient`
- 测试环境变量：`ADMIN_PASSWORD=test123`
- 验证点：
  - 未登录 Web 页面返回 302 + `Location: /login` header
  - 未登录 API 返回 401 + `{"detail": "Not authenticated"}`
  - 已登录访问所有路由返回正常内容
  - `/login` 和 `/logout` 无需认证

### References

- [Source: architecture.md#Authentication & Security] - 认证机制设计
- [Source: architecture.md#API Naming Conventions] - API 响应格式
- [Source: epics.md#Story 3.2] - 验收标准
- [Source: app/web/auth.py] - 现有认证工具函数
- [Source: app/web/tasks.py] - 需要保护的 Web 路由
- [Source: app/api/tasks.py] - 需要保护的 API 路由
- [Source: 3-1-user-login-auth.md] - 前置 Story 实现细节

### 重要约束

1. **使用现有认证基础设施** - 复用 Story 3.1 的 `verify_session_token()` 函数
2. **遵循异步模式** - 所有路由函数保持 async
3. **中文界面** - Web 页面使用中文，API 使用英文
4. **日志规范** - 使用 loguru，敏感信息脱敏
5. **命名规范** - snake_case 函数/变量
6. **API 响应格式** - 401 错误使用 `{"detail": "Not authenticated"}`
7. **最小化修改** - 只添加认证依赖，不改变现有业务逻辑

### 依赖关系

- **前置条件**: Story 3.1 已完成（认证基础设施就绪）
- **后续依赖**: Story 3.3, 3.4 将依赖本 Story 的路由保护机制

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

N/A - 实现顺利，无需调试。

### Completion Notes List

- 实现了 `AuthRedirectException` 异常类和 `require_auth_web()`, `require_auth_api()` 两个认证依赖函数
- 在 `app/main.py` 注册了 `AuthRedirectException` 异常处理器，实现未登录时 302 重定向到 /login
- 为所有 Web 路由添加了 `require_auth_web` 依赖（共 7 个路由）
- 为所有 API 路由添加了 `require_auth_api` 依赖（共 6 个端点）
- 验证了 `/login` 和 `/logout` 路由无需认证
- 创建了 `tests/test_api_protection.py` 包含 10 个 API 保护测试
- 更新了 `tests/test_auth.py` 添加 8 个 Web 路由保护测试
- 更新了现有测试文件的 client fixture 以包含认证 cookie
- 全部 190 个测试通过，无回归

### File List

**Modified:**
- app/web/auth.py - 添加 AuthRedirectException, require_auth_web, require_auth_api
- app/main.py - 添加 AuthRedirectException 异常处理器
- app/web/tasks.py - 所有路由添加 require_auth_web 依赖
- app/api/tasks.py - 所有路由添加 require_auth_api 依赖
- tests/test_auth.py - 添加 Web 路由保护测试
- tests/test_web_tasks.py - client fixture 添加认证 cookie
- tests/test_api_tasks.py - client fixture 添加认证 cookie
- tests/test_api_logs.py - client fixture 添加认证 cookie

**New:**
- tests/test_api_protection.py - API 保护测试

### Change Log

- 2025-12-23: Story 3.2 实现完成 - 添加路由与 API 保护，所有管理功能需登录访问
- 2025-12-23: [Code Review] 修复代码审查发现的问题:
  - 修复 app/web/auth.py 导入顺序问题（AuthRedirectException 移至导入后）
  - 简化 require_auth_web/require_auth_api 中的冗余条件逻辑
  - 改进 tests/test_api_protection.py 测试质量（使用具体异常类型替代通用 except）
  - 改进 tests/test_auth.py 测试质量（使用 SQLAlchemy OperationalError 替代通用 except）
  - 新增 3 个 POST 路由未认证重定向测试（create_task, update_task, delete_task）

