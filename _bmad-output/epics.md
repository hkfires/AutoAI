---
stepsCompleted: [1, 2, 3, 4]
status: complete
completedAt: 'Thursday, December 19, 2025'
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/architecture.md'
---

# AutoAI - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for AutoAI, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**任务配置：**
- FR1: 用户可以配置 OpenAI API 端点地址
- FR2: 用户可以配置 API 认证密钥
- FR3: 用户可以设置定时规则（支持两种模式：间隔模式如"每2小时"，固定时间模式如"每天09:00"）
- FR4: 用户可以定义要发送的消息内容
- FR5: 用户可以启用或禁用任务

**任务执行：**
- FR6: 系统按照定时规则自动触发任务执行
- FR7: 系统向配置的 OpenAI API 发送消息
- FR8: 系统在发送失败时自动重试
- FR9: 系统记录每次执行的结果（成功/失败）

**用户认证（Phase 2）：**
- FR10: 用户可以通过登录认证访问管理后台
- FR11: 系统保护 API 密钥和任务配置的安全

**监控与日志（Phase 2）：**
- FR12: 用户可以查看任务执行日志
- FR13: 用户可以查看任务执行状态

**部署：**
- FR14: 系统支持 Docker 容器化部署
- FR15: 系统支持通过配置文件或环境变量进行初始配置

### NonFunctional Requirements

**安全：**
- NFR1: API 密钥必须加密存储，不得明文保存
- NFR2: 管理后台登录凭证必须加密存储
- NFR3: 敏感信息不得出现在日志中

**可靠性：**
- NFR4: 系统支持基本错误重试机制（网络失败时自动重试）
- NFR5: 系统能够在 VPS 重启后自动恢复运行（Docker 自动重启）

**集成：**
- NFR6: 系统支持 OpenAI 标准 API 格式（Chat Completions）
- NFR7: 系统使用 JSON 作为数据交换格式

### Additional Requirements

**来自架构文档的技术要求：**

- **Starter Template**: 不使用第三方 Starter 模板，从零构建简洁项目结构（Custom Minimal Setup）
- **技术栈**: Python 3.11+ / FastAPI / APScheduler / SQLite + SQLAlchemy 2.0 / httpx (async)
- **数据模型变更**: schedule_type（interval/fixed_time）、interval_minutes、fixed_time 替代 cron_expression
- **异步架构**: 全异步（async/await）设计，所有 I/O 操作必须使用异步
- **重试机制**: 使用 tenacity 库实现指数退避重试（3次尝试，2-10秒间隔）
- **日志系统**: 使用 loguru，敏感信息自动脱敏
- **配置管理**: 使用 pydantic-settings 进行类型安全的环境变量加载
- **Docker 部署**: python:3.11-slim 基础镜像，Volume 持久化 SQLite，restart: unless-stopped
- **命名规范**: snake_case（变量/函数/文件/数据库列/API字段），PascalCase（类名）
- **API 响应格式**: 直接返回数据，错误使用 FastAPI 标准格式 {"detail": "..."}
- **日期时间格式**: API 使用 ISO 8601 UTC

### FR Coverage Map

| FR | Epic | 描述 |
|----|------|------|
| FR1 | Epic 2 | 配置 OpenAI API 端点地址 |
| FR2 | Epic 2 | 配置 API 认证密钥 |
| FR3 | Epic 2 | 设置定时规则（间隔/固定时间） |
| FR4 | Epic 2 | 定义消息内容 |
| FR5 | Epic 2 | 启用/禁用任务 |
| FR6 | Epic 2 | 按定时规则自动触发 |
| FR7 | Epic 2 | 向 OpenAI API 发送消息 |
| FR8 | Epic 2 | 发送失败自动重试 |
| FR9 | Epic 2 | 记录执行结果 |
| FR10 | Epic 3 | 登录认证访问管理后台 |
| FR11 | Epic 3 | 保护 API 密钥和任务配置安全 |
| FR12 | Epic 3 | 查看任务执行日志 |
| FR13 | Epic 3 | 查看任务执行状态 |
| FR14 | Epic 1 | Docker 容器化部署 |
| FR15 | Epic 1 | 配置文件/环境变量配置 |

## Epic List

### Epic 1: 项目基础设施与配置
**用户成果:** 开发者可以克隆项目并通过环境变量配置系统，为后续开发奠定基础

**FRs 覆盖:** FR14, FR15
**NFRs 支持:** NFR5 (Docker 自动重启)

**说明:** 这是 MVP 的起点，建立项目结构、配置管理和 Docker 部署基础。架构文档指定了 Custom Minimal Setup，这个 Epic 将创建整个项目框架。

---

### Epic 2: 核心定时执行引擎
**用户成果:** 用户可以配置定时任务，系统按时自动向 OpenAI API 发送消息，无需人工干预

**FRs 覆盖:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9
**NFRs 支持:** NFR1 (API密钥安全), NFR3 (日志脱敏), NFR4 (错误重试), NFR6 (OpenAI格式), NFR7 (JSON交换)

**说明:** 这是 MVP 的核心功能，包含任务配置和执行的完整流程。完成后用户可以通过配置文件/环境变量设置任务，系统自动执行。

---

### Epic 3: Web 管理后台与认证 [Phase 2]
**用户成果:** 用户可以通过 Web 界面安全登录，管理任务（增删改查），查看执行日志

**FRs 覆盖:** FR10, FR11, FR12, FR13
**NFRs 支持:** NFR2 (凭证加密)

**说明:** Phase 2 扩展功能，为用户提供图形化管理界面，替代配置文件方式。

---

## Epic 1: 项目基础设施与配置

**目标:** 开发者可以克隆项目并通过环境变量配置系统，为后续开发奠定基础

### Story 1.1: 项目结构初始化

**As a** 开发者,
**I want** 克隆一个结构清晰的项目骨架,
**So that** 我可以快速开始开发而不需要从零搭建项目结构。

**Acceptance Criteria:**

**Given** 开发者克隆了项目仓库
**When** 查看项目目录结构
**Then** 应看到以下结构：
- `app/` 目录包含 `__init__.py`, `main.py`, `config.py`, `database.py`, `models.py`, `schemas.py`, `scheduler.py`
- `app/api/` 目录包含 `__init__.py`, `tasks.py`
- `app/services/` 目录包含 `__init__.py`, `openai_service.py`
- `app/utils/` 目录包含 `__init__.py`, `security.py`
- 根目录包含 `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`
**And** `requirements.txt` 包含所有必需依赖（fastapi, uvicorn, sqlalchemy, httpx, apscheduler, pydantic-settings, loguru, tenacity）

---

### Story 1.2: 环境配置管理

**As a** 开发者,
**I want** 通过环境变量配置系统级参数,
**So that** 我可以在不修改代码的情况下调整基础配置。

**Acceptance Criteria:**

**Given** 项目已初始化
**When** 创建 `.env` 文件或设置环境变量
**Then** 应用可以读取以下配置：
- `DATABASE_URL`: SQLite 数据库路径（默认 `sqlite+aiosqlite:///./data/autoai.db`）
- `LOG_LEVEL`: 日志级别（默认 `INFO`）
- `ADMIN_PASSWORD`: 管理后台密码（必需）
**And** 配置类使用 pydantic-settings 实现类型安全加载
**And** `.env.example` 包含所有配置项的示例
**And** OpenAI API 相关配置（端点、密钥）不在环境变量中，而是通过任务配置存储在数据库中

---

### Story 1.3: Docker 容器化部署

**As a** 用户,
**I want** 使用 Docker 一键部署应用,
**So that** 我可以在 VPS 上快速启动服务并确保系统重启后自动恢复。

**Acceptance Criteria:**

**Given** 项目已完成配置管理
**When** 运行 `docker-compose up -d`
**Then** 容器应成功启动
**And** 容器使用 `python:3.11-slim` 基础镜像
**And** SQLite 数据库文件通过 Volume 挂载到 `./data` 目录持久化
**And** 日志文件通过 Volume 挂载到 `./logs` 目录
**And** 容器配置 `restart: unless-stopped` 实现自动重启
**And** 应用监听 8000 端口

---

## Epic 2: 核心定时执行引擎

**目标:** 用户可以配置定时任务，系统按时自动向 OpenAI API 发送消息，无需人工干预

### Story 2.1: 任务与日志数据模型

**As a** 开发者,
**I want** 建立任务和执行日志的数据模型,
**So that** 系统可以持久化存储任务配置和执行记录。

**Acceptance Criteria:**

**Given** 数据库连接已配置
**When** 应用启动时
**Then** 自动创建以下数据表：

**Task 表：**
- `id`: 主键
- `name`: 任务名称
- `api_endpoint`: OpenAI API 端点地址
- `api_key`: API 密钥（加密存储）
- `schedule_type`: 调度类型（`interval` 或 `fixed_time`）
- `interval_minutes`: 间隔分钟数（间隔模式使用）
- `fixed_time`: 固定时间 HH:MM 格式（固定时间模式使用）
- `message_content`: 要发送的消息内容
- `enabled`: 是否启用
- `created_at`, `updated_at`: 时间戳

**ExecutionLog 表：**
- `id`: 主键
- `task_id`: 外键关联 Task
- `executed_at`: 执行时间
- `status`: 状态（`success` / `failed`）
- `response_summary`: 响应摘要
- `error_message`: 错误信息（可空）

**And** 使用 SQLAlchemy 2.0 异步 ORM
**And** API 密钥在数据库中加密存储（使用 Fernet）

---

### Story 2.2: 任务管理 API

**As a** 前端开发者,
**I want** 通过 REST API 管理任务,
**So that** Web UI 可以进行任务的增删改查操作。

**Acceptance Criteria:**

**Given** 数据模型已创建
**When** 调用任务管理 API
**Then** 支持以下端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/tasks` | GET | 获取所有任务列表 |
| `/api/tasks` | POST | 创建新任务 |
| `/api/tasks/{id}` | GET | 获取单个任务详情 |
| `/api/tasks/{id}` | PUT | 更新任务配置 |
| `/api/tasks/{id}` | DELETE | 删除任务 |

**And** API 响应使用 JSON 格式，字段使用 snake_case
**And** 创建成功返回 201，删除成功返回 204
**And** 任务不存在时返回 404
**And** API 密钥在响应中脱敏显示（如 `sk-...***`）
**And** 使用 Pydantic schemas 验证请求和响应

---

### Story 2.3: OpenAI API 调用服务

**As a** 系统,
**I want** 能够调用 OpenAI API 发送消息,
**So that** 定时任务可以自动触发 AI 交互。

**Acceptance Criteria:**

**Given** 任务配置了有效的 API 端点和密钥
**When** 调用 OpenAI 服务发送消息
**Then** 使用 httpx 异步客户端发送 POST 请求到配置的端点
**And** 请求格式符合 OpenAI Chat Completions API 标准
**And** 使用 Bearer Token 认证（API Key）
**And** 请求超时设置为 30 秒

**Given** API 调用失败（网络错误）
**When** 发生 httpx.RequestError
**Then** 使用 tenacity 自动重试
**And** 重试策略：最多 3 次，指数退避（2-10秒）
**And** 重试仅针对网络错误，不重试 4xx 错误

**Given** API 调用完成（成功或最终失败）
**When** 记录日志
**Then** API 密钥在日志中脱敏显示
**And** 使用 loguru 记录请求结果

---

### Story 2.4: 定时调度引擎

**As a** 用户,
**I want** 系统按照我设定的时间自动执行任务,
**So that** 我无需手动触发，系统自动运行。

**Acceptance Criteria:**

**Given** 存在已启用的任务
**When** 应用启动时
**Then** APScheduler 加载所有已启用任务的调度规则
**And** 间隔模式任务按 `interval_minutes` 周期执行
**And** 固定时间模式任务在每天的 `fixed_time` 执行

**Given** 任务触发执行
**When** 调度器调用任务
**Then** 调用 OpenAI 服务发送消息
**And** 将执行结果写入 ExecutionLog 表
**And** 记录状态（success/failed）和响应摘要

**Given** 任务被禁用
**When** 调度器检查任务状态
**Then** 跳过该任务的执行

**Given** 应用重启
**When** 调度器初始化
**Then** 自动恢复所有已启用任务的调度

---

### Story 2.5: 任务管理 Web 界面

**As a** 用户,
**I want** 通过 Web 界面管理定时任务,
**So that** 我可以方便地配置 API 信息、定时规则和消息内容。

**Acceptance Criteria:**

**Given** 用户访问管理界面
**When** 打开首页
**Then** 显示所有任务列表，包含：名称、调度规则、启用状态、最后执行时间

**Given** 用户点击"新建任务"
**When** 填写任务表单
**Then** 可以配置：
- 任务名称
- OpenAI API 端点地址
- API 密钥（输入框类型为 password）
- 调度类型（间隔/固定时间）
- 间隔分钟数 或 固定时间
- 消息内容
- 启用/禁用开关

**Given** 用户提交任务表单
**When** 表单验证通过
**Then** 任务保存到数据库
**And** 调度器立即加载新任务
**And** 页面跳转到任务列表并显示成功消息

**Given** 用户编辑现有任务
**When** 修改配置并保存
**Then** 更新数据库中的任务配置
**And** 调度器重新加载该任务的调度规则

**Given** 用户删除任务
**When** 确认删除
**Then** 从数据库删除任务及其执行日志
**And** 调度器移除该任务的调度

**And** 界面使用 Jinja2 模板服务端渲染
**And** 界面简洁实用，无需复杂样式

---

### Story 2.6: 执行日志查看

**As a** 用户,
**I want** 查看任务的执行历史,
**So that** 我可以确认任务是否正常运行。

**Acceptance Criteria:**

**Given** 用户在任务列表点击"查看日志"
**When** 进入日志页面
**Then** 显示该任务的执行历史列表，包含：
- 执行时间
- 状态（成功/失败，用颜色区分）
- 响应摘要（成功时）
- 错误信息（失败时）

**And** 日志按执行时间倒序排列（最新在前）
**And** 默认显示最近 50 条记录
**And** API 端点 `/api/tasks/{id}/logs` 返回日志数据

---

## Epic 3: Web 管理后台与认证 [Phase 2]

**目标:** 用户可以通过 Web 界面安全登录，管理任务（增删改查），查看执行日志

### Story 3.1: 用户登录认证

**As a** 用户,
**I want** 通过密码登录管理后台,
**So that** 只有我可以访问和管理任务配置。

**Acceptance Criteria:**

**Given** 用户访问管理界面
**When** 未登录状态
**Then** 自动跳转到登录页面

**Given** 用户在登录页面
**When** 输入正确的管理员密码
**Then** 登录成功，跳转到任务列表页面
**And** 创建用户 Session

**Given** 用户在登录页面
**When** 输入错误的密码
**Then** 显示"密码错误"提示
**And** 保持在登录页面

**Given** 用户已登录
**When** 点击"退出登录"
**Then** Session 失效
**And** 跳转到登录页面

**And** 管理员密码从环境变量 `ADMIN_PASSWORD` 读取
**And** 密码在存储和比对时使用安全哈希
**And** Session 使用 FastAPI 的 `SessionMiddleware`

---

### Story 3.2: 路由与 API 保护

**As a** 系统管理员,
**I want** 所有管理功能都需要登录才能访问,
**So that** API 密钥和任务配置得到安全保护。

**Acceptance Criteria:**

**Given** 用户未登录
**When** 访问以下 Web 页面
**Then** 返回 302 重定向到登录页面：
- 任务列表页 (`/`)
- 新建任务页 (`/tasks/new`)
- 编辑任务页 (`/tasks/{id}/edit`)
- 任务日志页 (`/tasks/{id}/logs`)

**Given** 用户未登录
**When** 调用以下 API 端点
**Then** 返回 401 Unauthorized：
- `GET /api/tasks`
- `POST /api/tasks`
- `GET /api/tasks/{id}`
- `PUT /api/tasks/{id}`
- `DELETE /api/tasks/{id}`
- `GET /api/tasks/{id}/logs`

**Given** 用户已登录
**When** 访问受保护的页面或 API
**Then** 正常返回内容

**And** 登录页面 (`/login`) 不需要认证即可访问

---

### Story 3.3: 任务状态仪表板

**As a** 用户,
**I want** 在首页看到所有任务的运行状态概览,
**So that** 我可以快速了解系统整体运行情况。

**Acceptance Criteria:**

**Given** 用户已登录并访问首页
**When** 页面加载
**Then** 显示任务状态仪表板，包含：
- 总任务数
- 已启用任务数
- 今日执行次数
- 今日成功率

**And** 任务列表显示每个任务的：
- 任务名称
- 调度规则描述（如"每2小时"或"每天09:00"）
- 启用/禁用状态
- 最后执行时间
- 最后执行状态（成功/失败/从未执行）
- 操作按钮（编辑、日志、删除）

**Given** 任务最后执行失败
**When** 查看任务列表
**Then** 该任务行用警告色高亮显示

---

### Story 3.4: 增强的执行日志查看

**As a** 用户,
**I want** 更详细地查看和筛选执行日志,
**So that** 我可以排查问题和监控系统运行。

**Acceptance Criteria:**

**Given** 用户查看任务执行日志
**When** 进入日志页面
**Then** 支持以下功能：
- 按状态筛选（全部/成功/失败）
- 按日期范围筛选
- 分页显示（每页 20 条）

**Given** 用户点击某条日志
**When** 展开日志详情
**Then** 显示完整信息：
- 执行时间（精确到秒）
- 状态
- 请求耗时
- 响应摘要（成功时）
- 完整错误信息（失败时）

**And** 日志页面顶部显示统计信息：
- 该任务总执行次数
- 成功率
- 最近 7 天的执行趋势（简单文字描述）
