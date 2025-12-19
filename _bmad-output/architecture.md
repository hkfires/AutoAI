---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '_bmad-output/prd.md'
documentCounts:
  prd: 1
  epics: 0
  ux: 0
  research: 0
  projectDocs: 0
  projectContext: 0
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: 'Thursday, December 18, 2025'
project_name: 'AutoAI'
user_name: 'Hkfires'
date: 'Thursday, December 18, 2025'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- 15 项功能需求，覆盖任务配置（5项）、任务执行（4项）、用户认证（2项）、监控日志（2项）、部署（2项）
- MVP 阶段聚焦：定时触发 + OpenAI API 调用 + 基本配置 + Docker 部署
- Phase 2 扩展：Web 管理后台 + 认证 + 日志查看

**Non-Functional Requirements:**
- 安全性：API 密钥和凭证必须加密存储，日志脱敏
- 可靠性：网络失败自动重试，Docker 自动重启恢复
- 集成：遵循 OpenAI API 标准格式

**Scale & Complexity:**
- Primary domain: api_backend + web_app
- Complexity level: Low
- Estimated architectural components: 5-7

### Technical Constraints & Dependencies

- 部署目标：VPS + Docker 容器化
- 外部 API：OpenAI Chat Completions API
- 认证机制：API Key
- 数据交换：JSON 格式

### Cross-Cutting Concerns Identified

1. **Security**: API 密钥加密存储影响配置和执行模块
2. **Error Handling**: 重试机制影响调度器和 HTTP 客户端
3. **Logging**: 执行日志贯穿任务执行全流程
4. **Configuration**: 环境变量/配置文件管理影响所有组件

## Starter Template Evaluation

### Primary Technology Domain

api_backend + web_app (Python)

### Technology Stack Selected

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | 用户偏好，生态成熟 |
| Backend Framework | FastAPI | 现代异步架构，自动 API 文档，轻量高效 |
| Scheduler | APScheduler | 原生 Python 调度器，支持间隔和固定时间触发 |
| Database | SQLite + SQLAlchemy 2.0 | 轻量级，无需独立数据库服务，适合个人工具 |
| HTTP Client | httpx (async) | 异步 HTTP 客户端，适配 FastAPI |
| Web Templates | Jinja2 | FastAPI 原生支持，简单管理界面 |
| Containerization | Docker | 用户需求，VPS 部署 |

### Starter Approach

**Custom Minimal Setup**（自定义最小化设置）

不使用第三方 Starter 模板，从零构建简洁项目结构。原因：
- 项目复杂度低，无需复杂脚手架
- 个人工具，保持代码简洁可控
- 避免引入不需要的依赖和抽象

### Project Structure

```
autoai/
├── app/
│   ├── main.py          # FastAPI 入口 + 调度器启动
│   ├── config.py        # 配置管理（环境变量）
│   ├── database.py      # SQLite + SQLAlchemy 配置
│   ├── models.py        # 数据模型（Task, Log）
│   ├── scheduler.py     # APScheduler 定时任务
│   ├── api/             # API 路由
│   └── services/        # 业务逻辑（OpenAI 调用）
├── templates/           # 管理界面模板
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Architectural Decisions from Stack

1. **Async-First**: FastAPI + httpx 全异步架构
2. **Simple Persistence**: SQLite 文件数据库，无需独立服务
3. **In-Process Scheduling**: APScheduler 进程内调度，无需 Redis/消息队列
4. **Template-Based UI**: Jinja2 服务端渲染，无需前后端分离

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- 技术栈选择：Python + FastAPI + SQLite（已确定）
- 调度机制：APScheduler 进程内调度（已确定）
- 部署方式：Docker 容器化（已确定）

**Important Decisions (Shape Architecture):**
- 认证机制：简单密码 + Session（Phase 2）
- API 密钥存储：MVP 环境变量，Phase 2 Fernet 加密
- 重试策略：tenacity 库
- 日志系统：loguru

**Deferred Decisions (Post-MVP):**
- 数据库迁移工具（Alembic）
- 多 AI 目标支持
- 消息模板管理

### Data Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | SQLite | 单用户个人工具，无需独立数据库服务 |
| ORM | SQLAlchemy 2.0 | Python 标准 ORM，异步支持 |
| Migration | 无（MVP） | 简化 MVP，Phase 2 引入 Alembic |

**Data Models:**

```python
# Task 模型
class Task:
    id: int (PK)
    name: str
    api_endpoint: str
    api_key: str              # MVP: 从环境变量读取
    schedule_type: str        # "interval" 或 "fixed_time"
    interval_minutes: int?    # 间隔模式：间隔分钟数（如 120 表示每2小时）
    fixed_time: str?          # 固定时间模式：HH:MM 格式（如 "09:00"）
    message_content: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

# ExecutionLog 模型
class ExecutionLog:
    id: int (PK)
    task_id: int (FK)
    executed_at: datetime
    status: str           # success / failed
    response_summary: str
    error_message: str?
```

### Authentication & Security

| Decision | Choice | Phase | Rationale |
|----------|--------|-------|-----------|
| 管理后台认证 | 简单密码 + Session | Phase 2 | 单用户，最简方案 |
| API 密钥存储 | 环境变量 | MVP | 简化配置 |
| API 密钥存储 | Fernet 加密 | Phase 2 | 多任务支持 |
| 敏感信息日志 | 自动脱敏 | MVP | 安全要求 |

**Security Patterns:**
- 管理后台密码从环境变量 `ADMIN_PASSWORD` 读取
- Session 使用 FastAPI 的 `SessionMiddleware`
- API 密钥在日志中显示为 `sk-...***`

### API & Communication Patterns

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTTP 客户端 | httpx (async) | 原生异步，适配 FastAPI |
| 重试机制 | tenacity | 成熟库，指数退避，配置灵活 |
| 日志系统 | loguru | 语法简洁，开箱即用 |
| API 文档 | Swagger UI (内置) | FastAPI 自动生成 |

**Retry Strategy:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError)
)
async def call_openai_api(...):
    ...
```

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|-----------|
| 基础镜像 | python:3.11-slim | 轻量，安全 |
| 数据持久化 | Docker Volume | SQLite 文件挂载 |
| 自动重启 | restart: unless-stopped | 系统重启后自动恢复 |
| 配置管理 | pydantic-settings | 类型安全的环境变量加载 |

**Docker Compose Structure:**
```yaml
services:
  autoai:
    build: .
    restart: unless-stopped
    volumes:
      - ./data:/app/data    # SQLite 持久化
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    ports:
      - "8000:8000"
```

### Decision Impact Analysis

**Implementation Sequence:**
1. 项目结构 + 配置管理（config.py）
2. 数据库模型（models.py, database.py）
3. OpenAI API 调用服务（services/openai.py）
4. APScheduler 调度器（scheduler.py）
5. FastAPI 入口 + 生命周期（main.py）
6. Docker 配置（Dockerfile, docker-compose.yml）
7. [Phase 2] Web 管理后台
8. [Phase 2] 认证系统

**Cross-Component Dependencies:**
- `scheduler.py` 依赖 `services/openai.py` 和 `models.py`
- `main.py` 依赖所有模块，负责生命周期管理
- `config.py` 被所有模块依赖

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 5 大类潜在冲突区域需要统一规范

### Naming Patterns

**Database Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| 表名 | snake_case 复数 | `tasks`, `execution_logs` |
| 列名 | snake_case | `task_id`, `created_at`, `api_endpoint` |
| 外键 | {referenced_table_singular}_id | `task_id` |
| 索引 | ix_{table}_{column} | `ix_tasks_enabled` |

**API Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| 端点路径 | snake_case 复数 | `/api/tasks`, `/api/execution_logs` |
| 路径参数 | snake_case | `/api/tasks/{task_id}` |
| 查询参数 | snake_case | `?page_size=10&is_enabled=true` |
| JSON 字段 | snake_case | `{"task_id": 1, "created_at": "..."}` |

**Code Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| 文件名 | snake_case.py | `openai_service.py`, `task_router.py` |
| 类名 | PascalCase | `Task`, `ExecutionLog`, `OpenAIService` |
| 函数名 | snake_case | `get_task_by_id()`, `send_message()` |
| 变量名 | snake_case | `task_id`, `api_key`, `cron_expression` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有成员 | _leading_underscore | `_db_session`, `_scheduler` |

### Structure Patterns

**Project Organization:**

```
app/
├── __init__.py
├── main.py              # FastAPI 应用入口 + lifespan
├── config.py            # Settings 类，pydantic-settings
├── database.py          # 数据库引擎 + session 管理
├── models.py            # SQLAlchemy ORM 模型
├── schemas.py           # Pydantic 请求/响应 schemas
├── scheduler.py         # APScheduler 配置和任务注册
├── api/
│   ├── __init__.py
│   ├── tasks.py         # /api/tasks 路由
│   └── logs.py          # /api/logs 路由（Phase 2）
├── services/
│   ├── __init__.py
│   └── openai_service.py  # OpenAI API 调用逻辑
└── utils/
    ├── __init__.py
    └── security.py      # 脱敏、加密工具函数
```

**Test Organization:**

```
tests/
├── __init__.py
├── conftest.py          # pytest fixtures
├── test_scheduler.py
├── test_openai_service.py
└── test_api_tasks.py
```

- 测试框架：pytest
- 测试文件命名：`test_{module}.py`
- 测试函数命名：`test_{function}_{scenario}()`

### Format Patterns

**API Response Formats:**

成功响应（直接返回数据）：
```python
# 单个对象
{"id": 1, "name": "Daily Task", "enabled": true, "created_at": "2025-12-18T09:00:00Z"}

# 列表
[{"id": 1, ...}, {"id": 2, ...}]

# 创建成功 (201)
{"id": 3, "name": "New Task", ...}
```

错误响应：
```python
# FastAPI 标准格式
{"detail": "Task not found"}

# 带错误码（可选）
{"detail": "Invalid cron expression", "error_code": "INVALID_CRON"}
```

**HTTP Status Code Usage:**

| Scenario | Status Code |
|----------|-------------|
| 成功获取 | 200 OK |
| 创建成功 | 201 Created |
| 更新成功 | 200 OK |
| 删除成功 | 204 No Content |
| 参数错误 | 400 Bad Request |
| 未认证 | 401 Unauthorized |
| 资源不存在 | 404 Not Found |
| 服务器错误 | 500 Internal Server Error |

**Date/Time Formats:**

| Context | Format | Example |
|---------|--------|---------|
| JSON API | ISO 8601 UTC | `2025-12-18T09:00:00Z` |
| 数据库存储 | datetime 类型 | SQLite 自动处理 |
| 日志输出 | 本地时间 | `2025-12-18 17:00:00` |
| 固定时间格式 | HH:MM (24小时制) | `09:00`, `14:30` |
| 间隔格式 | 分钟数 | `60` (每小时), `120` (每2小时) |

### Communication Patterns

**Logging Patterns:**

```python
from loguru import logger

# 配置
logger.add(
    "logs/autoai.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# 使用
logger.info(f"Task {task.name} executed successfully")
logger.error(f"API call failed: {error}")
logger.debug(f"Request payload: {payload}")
```

**Sensitive Data Masking:**

```python
def mask_api_key(key: str) -> str:
    """将 API 密钥脱敏显示"""
    if len(key) > 8:
        return f"{key[:4]}...{key[-4:]}"
    return "***"

# 日志中使用
logger.info(f"Using API key: {mask_api_key(api_key)}")
```

### Process Patterns

**Error Handling Patterns:**

```python
from fastapi import HTTPException

# API 层错误
raise HTTPException(status_code=404, detail="Task not found")

# 服务层错误
class OpenAIServiceError(Exception):
    """OpenAI API 调用失败"""
    pass

# 捕获并记录
try:
    result = await openai_service.send_message(...)
except OpenAIServiceError as e:
    logger.error(f"OpenAI call failed: {e}")
    await save_execution_log(task_id, status="failed", error=str(e))
```

**Async Patterns:**

```python
# 所有 I/O 操作必须使用 async/await
async def get_task(task_id: int) -> Task | None:
    async with get_session() as session:
        result = await session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

# HTTP 调用
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload)
```

**Retry Patterns:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError)
)
async def call_openai_api(endpoint: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
```

### Enforcement Guidelines

**All Code MUST:**

1. 遵循 Python snake_case 命名（变量/函数/文件），PascalCase（类）
2. 所有 I/O 操作使用 async/await
3. 使用 loguru 记录日志，敏感信息自动脱敏
4. API 返回 snake_case JSON 字段
5. 使用 Pydantic schemas 验证请求/响应
6. 错误使用 FastAPI HTTPException，状态码语义正确
7. 数据库操作通过 SQLAlchemy async session

**Anti-Patterns to Avoid:**

```python
# BAD: 同步 I/O
def get_task(task_id):  # 缺少 async
    ...

# BAD: 混合命名风格
taskId = 1  # 应该是 task_id
class task_model:  # 应该是 TaskModel

# BAD: 直接暴露敏感信息
logger.info(f"API key: {api_key}")  # 应该脱敏

# BAD: 硬编码配置
OPENAI_URL = "https://api.openai.com"  # 应该从 config 读取
```

## Project Structure & Boundaries

### Requirements to Structure Mapping

| 需求类别 | 对应模块/目录 |
|----------|--------------|
| 任务配置 (FR1-5) | `app/models.py`, `app/schemas.py`, `app/api/tasks.py` |
| 任务执行 (FR6-9) | `app/scheduler.py`, `app/services/openai_service.py` |
| 用户认证 (FR10-11) | `app/api/auth.py` (Phase 2) |
| 监控日志 (FR12-13) | `app/api/logs.py`, `app/models.py` (Phase 2) |
| 部署 (FR14-15) | `Dockerfile`, `docker-compose.yml`, `app/config.py` |

### Complete Project Directory Structure

```
autoai/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略规则
├── Dockerfile                   # Docker 镜像定义
├── docker-compose.yml           # Docker Compose 配置
│
├── app/                         # 应用主目录
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口 + lifespan 管理
│   ├── config.py                # Settings 类 (pydantic-settings)
│   ├── database.py              # SQLAlchemy 引擎 + async session
│   ├── models.py                # ORM 模型 (Task, ExecutionLog)
│   ├── schemas.py               # Pydantic 请求/响应 schemas
│   ├── scheduler.py             # APScheduler 配置 + 任务注册
│   │
│   ├── api/                     # API 路由模块
│   │   ├── __init__.py
│   │   ├── tasks.py             # /api/tasks CRUD 端点
│   │   └── logs.py              # /api/logs 查询端点 (Phase 2)
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   └── openai_service.py    # OpenAI API 调用 + 重试逻辑
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       └── security.py          # API 密钥脱敏等
│
├── data/                        # 数据持久化目录 (Docker Volume)
│   └── autoai.db                # SQLite 数据库文件
│
├── logs/                        # 日志目录
│   └── autoai.log               # 应用日志文件
│
└── tests/                       # 测试目录
    ├── __init__.py
    ├── conftest.py              # pytest fixtures
    ├── test_config.py           # 配置测试
    ├── test_models.py           # 模型测试
    ├── test_scheduler.py        # 调度器测试
    ├── test_openai_service.py   # OpenAI 服务测试
    └── test_api_tasks.py        # API 端点测试
```

### Architectural Boundaries

**API Boundaries:**

```
外部客户端
    │
    ▼
┌─────────────────────────────────┐
│  FastAPI (main.py)              │  ← HTTP 入口
│  ├── /api/tasks/*               │  ← 任务管理 API
│  ├── /api/logs/*                │  ← 日志查询 API (Phase 2)
│  └── /docs                      │  ← Swagger UI
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Services Layer                  │
│  └── openai_service.py          │  ← 业务逻辑封装
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Data Layer                      │
│  ├── models.py (SQLAlchemy)     │  ← ORM 定义
│  └── database.py                │  ← 连接管理
└─────────────────────────────────┘
    │
    ▼
  SQLite (data/autoai.db)
```

**Component Communication Boundaries:**

| 调用方 | 被调用方 | 通信方式 |
|--------|---------|---------|
| `main.py` | `scheduler.py` | lifespan 启动/关闭 |
| `scheduler.py` | `openai_service.py` | 直接函数调用 (async) |
| `scheduler.py` | `models.py` | SQLAlchemy session |
| `api/tasks.py` | `models.py` | SQLAlchemy session |
| `openai_service.py` | OpenAI API | httpx HTTP 请求 |

**Data Boundaries:**

| 数据类型 | 存储位置 | 访问方式 |
|----------|---------|---------|
| 任务配置 | SQLite `tasks` 表 | SQLAlchemy ORM |
| 执行日志 | SQLite `execution_logs` 表 | SQLAlchemy ORM |
| 应用日志 | `logs/autoai.log` | loguru 写入 |
| 环境配置 | `.env` / 环境变量 | pydantic-settings |

### Key File Responsibilities

| 文件 | 职责 | 依赖 |
|------|------|------|
| `main.py` | FastAPI 应用入口，lifespan 管理调度器启停 | 所有模块 |
| `config.py` | 环境变量加载，Settings 类定义 | 无 |
| `database.py` | SQLAlchemy async engine 和 session 工厂 | config.py |
| `models.py` | Task, ExecutionLog ORM 模型 | database.py |
| `schemas.py` | TaskCreate, TaskResponse 等 Pydantic 模型 | 无 |
| `scheduler.py` | APScheduler 配置，任务注册和执行 | models, services |
| `openai_service.py` | OpenAI API 调用，重试逻辑 | config, httpx |
| `api/tasks.py` | 任务 CRUD API 端点 | models, schemas |

### Integration Points

**Internal Integration:**
- `scheduler.py` 在每个定时触发点调用 `openai_service.send_message()`
- 执行结果写入 `execution_logs` 表

**External Integration:**
- OpenAI Chat Completions API (`https://api.openai.com/v1/chat/completions`)
- 认证方式：Bearer Token (API Key)

**Data Flow:**
```
定时触发 → scheduler.py
         → openai_service.send_message()
         → httpx POST to OpenAI
         → 响应处理
         → save_execution_log()
         → SQLite
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- 所有技术选择（FastAPI + SQLAlchemy 2.0 + APScheduler + httpx）均为 Python 原生异步生态，相互兼容
- Python 3.11+ 支持所有选定库的最新版本
- 无冲突决策

**Pattern Consistency:**
- 全异步架构（async/await）贯穿所有组件
- snake_case 命名规范统一应用于数据库、API、代码
- loguru 日志 + tenacity 重试 + httpx 异步通信模式一致

**Structure Alignment:**
- 项目结构完整支持所有架构组件
- API / Service / Data 三层边界清晰
- 内外部集成点明确标识

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**

| 需求 | 状态 | 架构支持 |
|------|------|---------|
| FR1-5 任务配置 | ✅ MVP | models.py, schemas.py, api/tasks.py |
| FR6-9 任务执行 | ✅ MVP | scheduler.py, openai_service.py |
| FR10-11 用户认证 | ⏳ Phase 2 | 已预留 api/auth.py |
| FR12-13 监控日志 | ⏳ Phase 2 | 已预留 api/logs.py |
| FR14-15 部署 | ✅ MVP | Dockerfile, docker-compose.yml |

**Non-Functional Requirements Coverage:**

| NFR | 状态 | 实现方式 |
|-----|------|---------|
| NFR1-3 安全 | ✅ | 环境变量存储敏感信息，日志脱敏 |
| NFR4-5 可靠性 | ✅ | tenacity 重试，Docker 自动重启 |
| NFR6-7 集成 | ✅ | httpx + JSON 标准格式 |

### Implementation Readiness Validation ✅

**Decision Completeness:**
- 关键决策有版本号：Python 3.11+, SQLAlchemy 2.0, FastAPI 等
- 实现模式完整：5 大类模式全覆盖
- 一致性规则明确：强制规则 + 反模式示例
- 主要模式有代码示例

**Structure Completeness:**
- 完整目录树已定义
- 所有文件和目录已指定
- 集成点明确标识
- 组件边界清晰

**Pattern Completeness:**
- 命名、结构、格式、通信、进程模式全覆盖
- 每个模式都有代码示例
- 反模式已标识

### Gap Analysis Results

**Critical Gaps:** 无

**Important Gaps:** 无

**Nice-to-Have (Future):**
- 健康检查端点 `/health`
- Prometheus 指标端点
- GitHub Actions CI/CD

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] 项目上下文分析完成
- [x] 规模和复杂度评估
- [x] 技术约束识别
- [x] 横切关注点映射

**✅ Architectural Decisions**
- [x] 关键决策有版本记录
- [x] 技术栈完整指定
- [x] 集成模式定义
- [x] 安全/可靠性考虑

**✅ Implementation Patterns**
- [x] 命名约定确立
- [x] 结构模式定义
- [x] 通信模式指定
- [x] 进程模式记录

**✅ Project Structure**
- [x] 完整目录结构定义
- [x] 组件边界建立
- [x] 集成点映射
- [x] 需求到结构映射

### Architecture Readiness Assessment

**Overall Status:** 🟢 READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- 技术栈简洁统一（全 Python 异步生态）
- 架构复杂度与需求匹配（低复杂度个人工具）
- 模式规则清晰，易于遵循
- Docker 部署简化运维

**Areas for Future Enhancement:**
- Phase 2：Web 管理后台 + 认证
- Phase 3：多 AI 目标 + 消息模板

### Implementation Handoff

**AI Agent Guidelines:**
- 严格遵循本文档所有架构决策
- 在所有组件中一致使用实现模式
- 尊重项目结构和边界
- 架构问题参考本文档

**First Implementation Priority:**
1. 创建项目结构和 requirements.txt
2. 实现 config.py（配置管理）
3. 实现 database.py + models.py（数据层）
4. 实现 openai_service.py（服务层）
5. 实现 scheduler.py（调度器）
6. 实现 main.py（应用入口）
7. 配置 Docker 部署

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** Thursday, December 18, 2025
**Document Location:** _bmad-output/architecture.md

### Final Architecture Deliverables

**Complete Architecture Document**
- 所有架构决策已记录，包含具体版本号
- 实现模式确保 AI Agent 一致性
- 完整项目结构，包含所有文件和目录
- 需求到架构映射
- 验证确认一致性和完整性

**Implementation Ready Foundation**
- 20+ 架构决策已制定
- 5 大类实现模式已定义
- 6 个主要架构组件已指定
- 15 项功能需求 + 7 项非功能需求已支持

**AI Agent Implementation Guide**
- 技术栈及验证版本
- 防止实现冲突的一致性规则
- 项目结构及清晰边界
- 集成模式和通信标准

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] 所有决策协调一致，无冲突
- [x] 技术选择相互兼容
- [x] 模式支持架构决策
- [x] 结构与所有选择对齐

**✅ Requirements Coverage**
- [x] 所有功能需求已支持
- [x] 所有非功能需求已处理
- [x] 横切关注点已处理
- [x] 集成点已定义

**✅ Implementation Readiness**
- [x] 决策具体可执行
- [x] 模式防止 Agent 冲突
- [x] 结构完整无歧义
- [x] 提供示例以便清晰理解

### Project Success Factors

**Clear Decision Framework**
每个技术选择都是协作制定的，有明确理由，确保所有利益相关者理解架构方向。

**Consistency Guarantee**
实现模式和规则确保多个 AI Agent 产生兼容、一致的代码，无缝协作。

**Complete Coverage**
所有项目需求都有架构支持，从业务需求到技术实现有清晰映射。

**Solid Foundation**
选择的技术栈和架构模式提供生产就绪的基础，遵循当前最佳实践。

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** 使用本文档记录的架构决策和模式开始实现。

**Document Maintenance:** 实现过程中做出重大技术决策时，请更新本架构文档。
