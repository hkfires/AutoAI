# Story 1.1: 项目结构初始化

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 开发者,
I want 克隆一个结构清晰的项目骨架,
So that 我可以快速开始开发而不需要从零搭建项目结构。

## Acceptance Criteria

1. **Given** 开发者克隆了项目仓库
   **When** 查看项目目录结构
   **Then** 应看到以下结构：
   - `app/` 目录包含 `__init__.py`, `main.py`, `config.py`, `database.py`, `models.py`, `schemas.py`, `scheduler.py`
   - `app/api/` 目录包含 `__init__.py`, `tasks.py`
   - `app/services/` 目录包含 `__init__.py`, `openai_service.py`
   - `app/utils/` 目录包含 `__init__.py`, `security.py`
   - 根目录包含 `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`

2. **And** `requirements.txt` 包含所有必需依赖：
   - fastapi
   - uvicorn[standard]
   - sqlalchemy[asyncio]
   - aiosqlite
   - httpx
   - apscheduler
   - pydantic-settings
   - loguru
   - tenacity
   - python-multipart
   - cryptography (for Fernet)
   - jinja2

## Tasks / Subtasks

- [x] Task 1: 创建项目根目录结构 (AC: #1)
  - [x] 1.1 创建 `app/` 目录及 `__init__.py`
  - [x] 1.2 创建 `app/api/` 目录及 `__init__.py`
  - [x] 1.3 创建 `app/services/` 目录及 `__init__.py`
  - [x] 1.4 创建 `app/utils/` 目录及 `__init__.py`
  - [x] 1.5 创建 `data/` 目录及 `.gitkeep`（用于 SQLite 持久化）
  - [x] 1.6 创建 `logs/` 目录及 `.gitkeep`（用于日志文件）

- [x] Task 2: 创建核心应用文件骨架 (AC: #1)
  - [x] 2.1 创建 `app/main.py` - FastAPI 入口 + lifespan 管理
  - [x] 2.2 创建 `app/config.py` - Settings 类（pydantic-settings）
  - [x] 2.3 创建 `app/database.py` - SQLAlchemy async engine + session
  - [x] 2.4 创建 `app/models.py` - ORM 模型占位
  - [x] 2.5 创建 `app/schemas.py` - Pydantic schemas 占位
  - [x] 2.6 创建 `app/scheduler.py` - APScheduler 配置占位

- [x] Task 3: 创建 API 路由模块 (AC: #1)
  - [x] 3.1 创建 `app/api/tasks.py` - 任务 CRUD 路由占位

- [x] Task 4: 创建服务层模块 (AC: #1)
  - [x] 4.1 创建 `app/services/openai_service.py` - OpenAI 调用服务占位

- [x] Task 5: 创建工具模块 (AC: #1)
  - [x] 5.1 创建 `app/utils/security.py` - 安全工具函数占位

- [x] Task 6: 创建项目配置文件 (AC: #1, #2)
  - [x] 6.1 创建 `requirements.txt` - 所有必需依赖
  - [x] 6.2 创建 `.env.example` - 环境变量示例
  - [x] 6.3 创建 `.gitignore` - Git 忽略规则
  - [x] 6.4 创建 `README.md` - 项目说明文档

- [x] Task 7: 创建 Docker 配置 (AC: #1)
  - [x] 7.1 创建 `Dockerfile` - 使用 python:3.11-slim
  - [x] 7.2 创建 `docker-compose.yml` - 服务配置

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **技术栈要求**
   - Python 3.11+
   - FastAPI 作为 Web 框架
   - SQLAlchemy 2.0 + aiosqlite 异步 ORM
   - APScheduler 进程内调度
   - httpx 异步 HTTP 客户端
   - pydantic-settings 配置管理
   - loguru 日志系统
   - tenacity 重试机制

2. **Starter Approach: Custom Minimal Setup**
   - 不使用第三方 Starter 模板
   - 从零构建简洁项目结构
   - 保持代码简洁可控

3. **命名规范**
   - 文件名：snake_case.py（如 `openai_service.py`）
   - 类名：PascalCase（如 `Task`, `Settings`）
   - 函数/变量名：snake_case（如 `get_task_by_id`）
   - 常量：UPPER_SNAKE_CASE（如 `MAX_RETRIES`）

### Technical Requirements

**关键技术约束：**

1. **异步架构（Async-First）**
   - 所有 I/O 操作必须使用 async/await
   - SQLAlchemy 使用 async session
   - httpx 使用 AsyncClient

2. **配置管理（pydantic-settings）**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       database_url: str = "sqlite+aiosqlite:///./data/autoai.db"
       log_level: str = "INFO"
       admin_password: str  # 必需

       class Config:
           env_file = ".env"
   ```

3. **日志系统（loguru）**
   ```python
   from loguru import logger

   logger.add(
       "logs/autoai.log",
       rotation="10 MB",
       retention="7 days",
       format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
   )
   ```

4. **FastAPI Lifespan 管理**
   ```python
   from contextlib import asynccontextmanager
   from fastapi import FastAPI

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # 启动时：初始化数据库、启动调度器
       yield
       # 关闭时：停止调度器
   ```

### File Structure Requirements

**完整项目目录结构（来自架构文档）：**

```
autoai/                          # 项目根目录（当前为 AutoAI）
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
│   │   └── tasks.py             # /api/tasks CRUD 端点
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
│   └── .gitkeep                 # 保持目录存在
│
└── logs/                        # 日志目录
    └── .gitkeep                 # 保持目录存在
```

### Library/Framework Requirements

**requirements.txt 内容：**

```
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.19.0

# HTTP Client
httpx>=0.25.0

# Scheduler
apscheduler>=3.10.0

# Configuration
pydantic-settings>=2.1.0

# Logging
loguru>=0.7.0

# Retry
tenacity>=8.2.0

# Utilities
python-multipart>=0.0.6
cryptography>=41.0.0
jinja2>=3.1.0
```

### Docker Configuration Requirements

**Dockerfile（python:3.11-slim）：**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml：**

```yaml
version: '3.8'

services:
  autoai:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    env_file:
      - .env
```

### Environment Variables

**.env.example 内容：**

```
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/autoai.db

# Logging
LOG_LEVEL=INFO

# Admin
ADMIN_PASSWORD=your_secure_password_here
```

### .gitignore Requirements

```
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
*.so
.eggs/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
.venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Data & Logs
data/*.db
logs/*.log

# OS
.DS_Store
Thumbs.db

# BMAD (keep for development reference)
# _bmad/
# _bmad-output/
```

### Project Structure Notes

- 项目根目录当前为 `AutoAI/`，应用代码在 `app/` 子目录
- `data/` 和 `logs/` 目录通过 Docker Volume 持久化
- 所有 Python 包目录必须包含 `__init__.py`
- 骨架文件应包含基本导入和占位注释，便于后续 Story 填充

### References

本故事的所有技术要求均来自项目架构文档，开发时严格遵循上述规范即可。

## Dev Agent Record

### Implementation Plan
- 创建完整的项目目录结构，遵循架构文档规范
- 实现所有核心骨架文件，包含基本导入和占位符
- 配置 pydantic-settings、SQLAlchemy async、APScheduler
- 创建 Docker 配置文件

### Debug Log
- 2025-12-19: 所有目录和文件创建成功
- 2025-12-19: 依赖安装成功（pip install -r requirements.txt）
- 2025-12-19: Python 语法验证通过（py_compile）
- 2025-12-19: 模块导入测试成功

### Completion Notes
✅ 所有任务完成：
- 创建了完整的项目目录结构（app/, app/api/, app/services/, app/utils/, data/, logs/）
- 实现了核心应用文件骨架（main.py, config.py, database.py, models.py, schemas.py, scheduler.py）
- 创建了 API 路由模块（api/tasks.py）
- 创建了服务层模块（services/openai_service.py）
- 创建了工具模块（utils/security.py）
- 创建了项目配置文件（requirements.txt, .env.example, .gitignore, README.md）
- 创建了 Docker 配置（Dockerfile, docker-compose.yml）

## File List

### New Files
- app/__init__.py
- app/main.py
- app/config.py
- app/database.py
- app/models.py
- app/schemas.py
- app/scheduler.py
- app/api/__init__.py
- app/api/tasks.py
- app/services/__init__.py
- app/services/openai_service.py
- app/utils/__init__.py
- app/utils/security.py
- data/.gitkeep
- logs/.gitkeep
- requirements.txt
- .env.example
- README.md
- Dockerfile
- docker-compose.yml

### Modified Files
- .gitignore (添加了 Python、虚拟环境、IDE、环境变量等忽略规则)

## Change Log

- 2025-12-19: 初始化项目结构，创建所有骨架文件和配置
- 2025-12-19: [Code Review] 修复8个问题:
  - HIGH #1: main.py 添加 API 路由注册 (app.include_router)
  - HIGH #2: database.py 修复 get_session 类型注解 (AsyncGenerator)
  - HIGH #3: main.py 添加 loguru 文件日志配置
  - HIGH #4: config.py admin_password 改为必需字段
  - MEDIUM #5: config.py 使用 pydantic v2 model_config
  - MEDIUM #6: Dockerfile 添加数据目录创建
  - MEDIUM #7: docker-compose.yml 添加健康检查
  - MEDIUM #8: .gitignore 添加注释说明
