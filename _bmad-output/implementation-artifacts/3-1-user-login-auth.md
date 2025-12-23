# Story 3.1: 用户登录认证

Status: done

<!-- Validated: 2025-12-23 -->

## Story

As a 用户,
I want 通过密码登录管理后台,
so that 只有我可以访问和管理任务配置。

## Acceptance Criteria

1. **AC1: 未登录重定向** *(基础设施就绪，路由保护在 Story 3.2 实现)*
   - Given 用户访问管理界面
   - When 未登录状态
   - Then 自动跳转到登录页面 (`/login`)
   - *注: 本 Story 提供 `get_current_user` 依赖函数，Story 3.2 将应用到受保护路由*

2. **AC2: 登录成功**
   - Given 用户在登录页面
   - When 输入正确的管理员密码
   - Then 登录成功，跳转到任务列表页面 (`/`)
   - And 创建用户 Session

3. **AC3: 登录失败**
   - Given 用户在登录页面
   - When 输入错误的密码
   - Then 显示"密码错误"提示
   - And 保持在登录页面

4. **AC4: 退出登录**
   - Given 用户已登录
   - When 点击"退出登录"
   - Then Session 失效
   - And 跳转到登录页面

5. **AC5: 密码安全比对**
   - Given 管理员密码从环境变量 `ADMIN_PASSWORD` 读取（明文）
   - When 用户提交密码进行验证
   - Then 使用 `secrets.compare_digest` 进行时序安全比对（防止时序攻击）

6. **AC6: Session 管理**
   - Given 用户登录成功
   - When 创建 Session
   - Then 使用 `itsdangerous` 签名 cookie（复用现有 `encryption_key`）
   - And Session 有效期为 7 天
   - And Session 过期后自动重定向到登录页面

## Tasks / Subtasks

- [x] Task 1: 添加认证相关依赖 (AC: #5, #6)
  - [x] 1.1 在 requirements.txt 添加 `itsdangerous>=2.1.2`（注：passlib 不需要，使用 secrets.compare_digest）
  - [x] 1.2 运行 pip install 安装依赖

- [x] Task 2: 创建认证工具模块 (AC: #5)
  - [x] 2.1 在 `app/utils/security.py` 添加密码验证函数
  - [x] 2.2 实现 `verify_password(plain, stored)` 使用 `secrets.compare_digest`

- [x] Task 3: 创建认证路由模块 (AC: #2, #3, #4, #6, AC1 基础设施)
  - [x] 3.1 创建 `app/web/auth.py` 模块
  - [x] 3.2 实现 `GET /login` 登录页面路由
  - [x] 3.3 实现 `POST /login` 登录处理路由（验证密码、创建 session cookie）
  - [x] 3.4 实现 `POST /logout` 退出登录路由（清除 session cookie）
  - [x] 3.5 实现 `get_current_user` 依赖函数（从 cookie 读取并验证 session）
  - [x] 3.6 验证 `/login` 路由不与现有路由冲突
  - [x] 3.7 实现 `render_template` 辅助函数（自动注入 is_authenticated）

- [x] Task 4: 创建登录页面模板 (AC: #2, #3)
  - [x] 4.1 创建 `templates/auth/login.html` 登录页面模板
  - [x] 4.2 包含密码输入框和登录按钮
  - [x] 4.3 显示错误消息（密码错误时）

- [x] Task 5: 注册认证路由 (AC: #1, #2, #3, #4)
  - [x] 5.1 在 `app/main.py` 导入并注册 auth router
  - [x] 5.2 确保 `/login` 路由可访问

- [x] Task 6: 更新导航栏 (AC: #4)
  - [x] 6.1 在 `templates/base.html` 添加"退出登录"链接（仅已登录时显示）

- [x] Task 7: 编写测试 (AC: #1, #2, #3, #4, #5)
  - [x] 7.1 创建 `tests/test_auth.py`
  - [x] 7.2 测试登录成功场景
  - [x] 7.3 测试登录失败场景
  - [x] 7.4 测试退出登录场景
  - [x] 7.5 测试 Session 过期场景

## Dev Notes

### 技术实现要点

**密码验证：**
- `ADMIN_PASSWORD` 从环境变量读取，存储为明文（`app/config.py:21`）
- 使用 `secrets.compare_digest` 进行时序安全比对，防止时序攻击
- 单用户系统，无需数据库存储用户信息

**Session 方案：**
- 使用 `itsdangerous.URLSafeTimedSerializer` 签名 cookie
- 复用现有 `encryption_key`（由 `ensure_encryption_key()` 在 `main.py` lifespan 中自动初始化）
- Session 有效期 7 天，过期后重定向到登录页

**安全说明：**
- CSRF 保护：单用户 MVP 场景延后实现，Story 3.x 可扩展
- 登录频率限制：单用户场景延后实现

### 项目结构变更

```
app/
├── web/
│   ├── __init__.py
│   ├── tasks.py          # 现有（本 Story 不修改）
│   └── auth.py           # 新增：认证路由
├── utils/
│   └── security.py       # 修改：添加 verify_password 函数
└── main.py               # 修改：注册 auth router

templates/
├── base.html             # 修改：添加退出登录链接
└── auth/
    └── login.html        # 新增：登录页面模板

requirements.txt          # 修改：添加依赖（含版本号）
```

### 代码模式参考

**密码验证（app/utils/security.py 添加）：**
```python
import secrets

def verify_password(plain_password: str, stored_password: str) -> bool:
    """验证密码是否匹配（时序安全比对）。

    Args:
        plain_password: 用户输入的密码
        stored_password: 从环境变量读取的密码

    Returns:
        True 如果密码匹配，否则 False
    """
    return secrets.compare_digest(plain_password, stored_password)
```

**Session Token（app/web/auth.py）：**
```python
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from fastapi import Request, Response
from app.config import get_settings

SESSION_MAX_AGE = 86400 * 7  # 7 天

def get_serializer() -> URLSafeTimedSerializer:
    """获取签名序列化器（复用 encryption_key）。"""
    return URLSafeTimedSerializer(get_settings().encryption_key)

def create_session_token() -> str:
    """创建已认证的 session token。"""
    return get_serializer().dumps({"authenticated": True})

def verify_session_token(token: str) -> bool:
    """验证 session token 是否有效。"""
    try:
        data = get_serializer().loads(token, max_age=SESSION_MAX_AGE)
        return data.get("authenticated", False)
    except (SignatureExpired, BadSignature):
        return False
```

**登录路由（app/web/auth.py）：**
```python
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.utils.security import verify_password

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login_page(request: Request):
    """显示登录页面。"""
    return templates.TemplateResponse(request, "auth/login.html", {})

@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    """处理登录请求。"""
    settings = get_settings()
    if not verify_password(password, settings.admin_password):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"message": "密码错误", "message_type": "error"},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session",
        value=create_session_token(),
        httponly=True,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )
    return response

@router.post("/logout")
async def logout():
    """处理退出登录。"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session")
    return response
```

**main.py 修改：**
```python
# 在现有 import 后添加
from app.web.auth import router as auth_router

# 在 app.include_router(web_tasks_router) 后添加
app.include_router(auth_router)
```

**登录页面模板（templates/auth/login.html）：**
```html
{% extends "base.html" %}

{% block title %}登录 - AutoAI{% endblock %}

{% block content %}
<div style="max-width: 400px; margin: 100px auto;">
    <h1 style="text-align: center;">AutoAI 登录</h1>

    <form method="POST" action="/login" style="margin-top: 30px;">
        <div class="form-group">
            <label for="password">管理员密码</label>
            <input type="password" id="password" name="password"
                   required autofocus placeholder="请输入密码">
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">
            登录
        </button>
    </form>
</div>
{% endblock %}
```

### 测试策略

- 使用 `pytest` + `pytest-asyncio` + `httpx.AsyncClient`
- 测试依赖：确保 `pytest>=7.0.0` 和 `pytest-asyncio>=0.21.0` 已安装（开发依赖）
- 测试环境变量：`ADMIN_PASSWORD=test123`
- 验证点：
  - 正确密码返回 303 重定向 + session cookie
  - 错误密码返回 401 + 错误消息
  - 退出登录清除 cookie
  - 过期 token 验证失败

### References

- [Source: architecture.md#Authentication & Security] - Session 使用签名 cookie
- [Source: epics.md#Story 3.1] - 验收标准
- [Source: app/config.py:21] - admin_password 配置项
- [Source: app/utils/security.py] - 现有加密工具
- [Source: app/main.py:30] - ensure_encryption_key() 已在 lifespan 中调用
- [Source: templates/base.html] - 基础模板

### 重要约束

1. **不修改现有路由保护** - 路由保护在 Story 3.2 实现
2. **遵循异步模式** - 所有路由函数使用 async
3. **中文界面** - 错误消息和页面文本使用中文
4. **日志规范** - 使用 loguru，敏感信息脱敏
5. **命名规范** - snake_case 函数/变量，PascalCase 类名

### 依赖关系

- **前置条件**: Epic 2 已完成（Web 界面基础设施就绪）
- **后续依赖**: Story 3.2 将使用本 Story 的认证机制保护路由

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无

### Completion Notes List

- 2025-12-23: Story 3.1 用户登录认证实现完成
- 添加了 `itsdangerous>=2.1.2` 依赖用于签名 session cookie
- 在 `app/utils/security.py` 添加了 `verify_password()` 函数，使用 `secrets.compare_digest` 进行时序安全比对
- 创建了 `app/web/auth.py` 认证路由模块，包含登录页面、登录处理、退出登录路由
- 实现了 `get_current_user()` 依赖函数用于验证 session
- 创建了 `templates/auth/login.html` 登录页面模板
- 在 `app/main.py` 注册了 auth router
- 更新了 `templates/base.html` 添加退出登录按钮（仅已登录时显示）
- 创建了 `tests/test_auth.py` 包含 15 个测试用例，全部通过
- 全部 167 个测试通过，无回归

### Code Review Notes (AI)

**审查日期:** 2025-12-23
**审查员:** Claude Opus 4.5

**发现并修复的问题:**

1. **[HIGH] is_authenticated 未传递到模板** - 已修复
   - 问题：`base.html` 检查 `is_authenticated` 但路由未传递此变量
   - 修复：创建 `render_template()` 辅助函数自动注入 `is_authenticated`
   - 修改文件：`app/web/auth.py`, `app/web/tasks.py`

2. **[HIGH] AC1 实现范围不明确** - 已澄清
   - 问题：Story AC1 与 Dev Notes 关于路由保护的说明存在冲突
   - 修复：更新 AC1 说明，明确基础设施在本 Story 完成，路由保护在 Story 3.2 实现

3. **[MEDIUM] File List 缺少 test_security.py** - 已修复
   - 问题：`tests/test_security.py` 新增测试但未记录
   - 修复：更新 File List 添加该文件

4. **[MEDIUM] httpx cookie 废弃警告** - 已修复
   - 问题：测试使用 per-request cookies 导致 DeprecationWarning
   - 修复：改用 client-level cookies 设置方式

**测试结果:** 167 passed, 0 warnings

### File List

- requirements.txt (修改: 添加 itsdangerous>=2.1.2)
- app/utils/security.py (修改: 添加 verify_password 函数)
- app/web/auth.py (新增: 认证路由模块，含 render_template 辅助函数)
- app/web/tasks.py (修改: 使用 render_template 注入 is_authenticated)
- app/main.py (修改: 注册 auth router)
- templates/base.html (修改: 添加退出登录按钮)
- templates/auth/login.html (新增: 登录页面模板)
- tests/test_auth.py (新增: 认证测试 15 个用例)
- tests/test_security.py (修改: 添加 verify_password 测试 3 个用例)
