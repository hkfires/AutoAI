# Story 1.3: Docker 容器化部署

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 用户,
I want 使用 Docker 一键部署应用,
So that 我可以在 VPS 上快速启动服务并确保系统重启后自动恢复。

## Acceptance Criteria

1. **Given** 项目已完成配置管理
   **When** 运行 `docker-compose up -d`
   **Then** 容器应成功启动
   **And** 应用在容器内正常运行

2. **And** 容器使用 `python:3.11-slim` 基础镜像
   - Dockerfile 的 FROM 指令使用 python:3.11-slim
   - 镜像保持轻量化

3. **And** SQLite 数据库文件通过 Volume 挂载到 `./data` 目录持久化
   - docker-compose.yml 配置 `./data:/app/data` Volume 映射
   - 数据库文件在容器重启后保留

4. **And** 日志文件通过 Volume 挂载到 `./logs` 目录
   - docker-compose.yml 配置 `./logs:/app/logs` Volume 映射
   - 日志文件在容器重启后保留

5. **And** 容器配置 `restart: unless-stopped` 实现自动重启
   - 系统重启后容器自动恢复运行
   - 手动停止的容器不会自动重启

6. **And** 应用监听 8000 端口
   - Dockerfile EXPOSE 8000
   - docker-compose.yml 映射 8000:8000

7. **And** 容器健康检查正常工作
   - healthcheck 调用 /health 端点
   - 容器状态显示为 healthy

8. **And** 构建和部署过程已验证和文档化
   - README.md 包含 Docker 部署指南
   - 包含构建、运行、停止、日志查看等常用命令

## Tasks / Subtasks

- [x] Task 1: 验证并优化 Dockerfile (AC: #2, #6)
  - [x] 1.1 验证 python:3.11-slim 基础镜像
  - [x] 1.2 优化 Dockerfile 层缓存（先 COPY requirements.txt）
  - [x] 1.3 确保 /app/data 和 /app/logs 目录创建
  - [x] 1.4 验证 uvicorn 启动命令正确

- [x] Task 2: 验证并优化 docker-compose.yml (AC: #3, #4, #5, #6, #7)
  - [x] 2.1 验证 Volume 映射（./data:/app/data, ./logs:/app/logs）
  - [x] 2.2 验证 restart: unless-stopped 配置
  - [x] 2.3 验证端口映射 8000:8000
  - [x] 2.4 验证 healthcheck 配置
  - [x] 2.5 验证环境变量传递（.env 文件和 ADMIN_PASSWORD）

- [x] Task 3: 创建 .dockerignore 文件 (AC: 优化镜像构建) ⚠️ 新建文件
  - [x] 3.1 **新建** `.dockerignore` 文件（当前项目中不存在）
  - [x] 3.2 排除 .venv、__pycache__、.git 等不必要文件
  - [x] 3.3 排除 .env（敏感信息不打包进镜像）
  - [x] 3.4 排除 tests、_bmad、_bmad-output 等开发相关文件

- [x] Task 4: 端到端部署验证 (AC: #1, #7)
  - [x] 4.1 创建 .env 文件（从 .env.example 复制并配置）
  - [x] 4.2 运行 docker-compose build 构建镜像 (用户跳过 Docker 测试)
  - [x] 4.3 运行 docker-compose up -d 启动容器 (用户跳过 Docker 测试)
  - [x] 4.4 验证容器状态为 healthy (用户跳过 Docker 测试)
  - [x] 4.5 验证 /health 端点响应正常 ✅ 通过代码测试验证
  - [x] 4.6 验证数据持久化（创建数据后重启容器）(用户跳过 Docker 测试)
  - [x] 4.7 验证日志文件写入 (用户跳过 Docker 测试)

- [x] Task 5: 更新 README.md 部署文档 (AC: #8) ⚠️ 当前文档过于简略
  - [x] 5.1 添加 Docker 部署前置条件说明（Docker >= 20.10, Docker Compose >= 2.0）
  - [x] 5.2 添加完整快速启动步骤（复制 .env、配置密码、构建启动）
  - [x] 5.3 添加常用 Docker 命令表格（build/up/down/logs/restart/exec）
  - [x] 5.4 添加环境变量配置说明表格
  - [x] 5.5 添加数据持久化说明（./data 和 ./logs 目录）
  - [x] 5.6 添加健康检查验证说明
  - [x] 5.7 添加故障排查提示（容器日志查看、进入容器调试）

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **基础镜像** - `python:3.11-slim`（轻量、安全）
2. **数据持久化** - Docker Volume 挂载 SQLite 文件
3. **自动重启** - `restart: unless-stopped`（系统重启后自动恢复）
4. **配置管理** - 通过 .env 文件和环境变量（pydantic-settings）

**相关 NFR 支持：**
- NFR5: 系统能够在 VPS 重启后自动恢复运行（Docker 自动重启）

### Technical Requirements

**Dockerfile 验证清单（文件已存在）：**

| 检查项 | 要求 | 状态 |
|--------|------|------|
| 基础镜像 | `FROM python:3.11-slim` | ✅ 已验证 |
| 工作目录 | `WORKDIR /app` | ✅ 已验证 |
| 持久化目录 | `RUN mkdir -p /app/data /app/logs` | ✅ 已验证 |
| 层缓存优化 | 先 `COPY requirements.txt`，再 `pip install` | ✅ 已验证 |
| 端口暴露 | `EXPOSE 8000` | ✅ 已验证 |
| 启动命令 | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` | ✅ 已验证 |

**docker-compose.yml 验证清单（文件已存在）：**

| 检查项 | 要求 | 状态 |
|--------|------|------|
| 版本 | `version: '3.8'` | ✅ 已验证 |
| 重启策略 | `restart: unless-stopped` | ✅ 已验证 |
| 端口映射 | `8000:8000` | ✅ 已验证 |
| 数据卷 | `./data:/app/data` | ✅ 已验证 |
| 日志卷 | `./logs:/app/logs` | ✅ 已验证 |
| 环境变量 | `env_file: .env` + `ADMIN_PASSWORD` | ✅ 已验证 |
| 健康检查 | `healthcheck` 调用 `/health` 端点 | ✅ 已验证 |

**需要新建的 .dockerignore 文件内容：**

```
# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv
ENV

# Git
.git
.gitignore

# IDE
.vscode
.idea
*.swp
*.swo

# Testing
.pytest_cache
.coverage
htmlcov

# Environment
.env
*.env.local

# Development files
_bmad
_bmad-output
tests
*.md
!README.md

# Misc
.DS_Store
Thumbs.db
```

### Library/Framework Requirements

**Docker 相关技术栈：**
- 基础镜像: `python:3.11-slim`
- 容器编排: `docker-compose version '3.8'`
- Python 依赖: 所有依赖通过 requirements.txt 安装

**已安装依赖（无需额外安装）：**
- uvicorn[standard]>=0.24.0 - ASGI 服务器

### File Structure Requirements

**需要修改/验证的文件：**
```
./
├── Dockerfile              # 验证配置
├── docker-compose.yml      # 验证配置
├── .dockerignore           # 新建：优化构建
├── README.md               # 添加 Docker 部署文档
└── .env.example            # 已存在，确认配置完整
```

**持久化目录结构（运行时）：**
```
./
├── data/                   # Volume: SQLite 数据库
│   └── autoai.db
└── logs/                   # Volume: 应用日志
    └── autoai.log
```

### Testing Requirements

**验证测试（手动执行）：**

| 测试场景 | 命令/操作 | 预期结果 |
|----------|-----------|----------|
| 构建镜像 | `docker-compose build` | 镜像构建成功，无错误 |
| 启动容器 | `docker-compose up -d` | 容器启动，状态为 running |
| 健康检查 | `docker-compose ps` | 容器状态显示 (healthy) |
| API 访问 | `docker-compose exec autoai python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"` | 返回 `{"status": "healthy"}` |
| 数据持久化 | `docker-compose restart` 后检查 data/ 目录 | autoai.db 文件保留 |
| 日志持久化 | 检查 logs/ 目录 | autoai.log 文件存在 |
| 自动重启 | `docker-compose restart` | 容器自动恢复到 healthy 状态 |
| 停止容器 | `docker-compose down` | 容器停止，data/ logs/ 保留 |

**容器内验证命令：**

```bash
# 进入容器（使用 docker-compose exec 避免硬编码容器名）
docker-compose exec autoai bash

# 检查目录结构
ls -la /app/
ls -la /app/data/
ls -la /app/logs/

# 检查进程
ps aux | grep uvicorn

# 容器内健康检查（python:3.11-slim 不含 curl）
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

**从主机验证（需安装 curl）：**

```bash
# 健康检查
curl http://localhost:8000/health

# 如果没有 curl，使用 PowerShell (Windows)
Invoke-WebRequest -Uri http://localhost:8000/health

# 或使用 Python
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

### Previous Story Intelligence

**来自 Story 1.1 和 1.2 的经验教训：**

1. **现有代码基础**
   - Dockerfile 和 docker-compose.yml 已在 Story 1.1 创建
   - /health 端点已在 main.py 中实现
   - 环境变量配置已在 Story 1.2 完善

2. **配置管理集成**
   - 使用 pydantic-settings 加载环境变量
   - ADMIN_PASSWORD 是必需字段
   - DATABASE_URL 默认为 `sqlite+aiosqlite:///./data/autoai.db`

3. **日志配置**
   - loguru 已配置写入 `logs/autoai.log`
   - 日志级别从 LOG_LEVEL 环境变量读取

### Git Intelligence Summary

**最近提交分析：**
- `bd92736 1-2-environment-config-management` - 完善环境配置管理
- `cc6ab50 1-1-project-structure-init` - 创建项目结构

**相关文件：**
- Dockerfile - 已存在，需验证
- docker-compose.yml - 已存在，需验证
- app/main.py - 包含 /health 端点

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - 项目基础设施与配置
**前置依赖：**
- Story 1.1（项目结构初始化）- 已完成
- Story 1.2（环境配置管理）- 已完成
**后续依赖：** Epic 2（核心定时执行引擎）依赖 Epic 1 完成

### Common LLM Pitfalls to Avoid

1. **不要修改已正确配置的文件** - 当前 Dockerfile 和 docker-compose.yml 已符合要求，仅需验证
2. **必须新建 .dockerignore** - 该文件当前不存在，防止敏感文件（.env）和不必要文件打包进镜像
3. **不要跳过验证步骤** - 必须实际构建和运行容器验证配置
4. **不要忽略健康检查** - 确保容器状态为 healthy 而非仅仅 running
5. **必须更新 README.md** - 当前 Docker 部署部分过于简略，必须按模板补充完整
6. **使用 docker-compose exec** - 避免硬编码容器名（如 `autoai-autoai-1`），使用 `docker-compose exec autoai` 更可靠
7. **容器内无 curl** - python:3.11-slim 不包含 curl，使用 Python urllib 进行容器内健康检查

### Windows 兼容性说明

本项目支持在 Windows（Docker Desktop）环境下开发和部署：

- **Volume 路径**: `./data:/app/data` 格式在 Windows Docker Desktop 中自动转换，无需手动修改
- **行尾符**: Git 配置应使用 `core.autocrlf=input` 避免 Dockerfile 行尾符问题
- **PowerShell 验证**: 如果没有 curl，使用 `Invoke-WebRequest` 或 Python 进行健康检查

### README.md Docker 部署文档模板

**重要**: 当前 README.md 中 Docker 部署部分仅有一行命令，必须替换为以下完整内容：

```markdown
## Docker 部署

### 前置条件

- Docker >= 20.10
- Docker Compose >= 2.0

### 快速启动

1. 复制环境变量配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 .env 文件，设置必需的 ADMIN_PASSWORD：
   ```bash
   # Linux/Mac
   nano .env

   # Windows
   notepad .env
   ```
   修改 `ADMIN_PASSWORD=your_secure_password`

3. 构建并启动容器：
   ```bash
   docker-compose up -d --build
   ```

4. 等待健康检查通过（约 30 秒）：
   ```bash
   docker-compose ps
   # 状态应显示 (healthy)
   ```

5. 验证服务运行：
   ```bash
   # Linux/Mac (需要 curl)
   curl http://localhost:8000/health

   # Windows PowerShell
   Invoke-WebRequest -Uri http://localhost:8000/health

   # 跨平台 (Python)
   python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
   ```

### 常用命令

| 操作 | 命令 |
|------|------|
| 启动服务 | `docker-compose up -d` |
| 停止服务 | `docker-compose down` |
| 重启服务 | `docker-compose restart` |
| 查看日志 | `docker-compose logs -f` |
| 查看状态 | `docker-compose ps` |
| 重新构建 | `docker-compose up -d --build` |
| 进入容器 | `docker-compose exec autoai bash` |

### 数据持久化

以下目录通过 Docker Volume 挂载，数据在容器重启后保留：

| 目录 | 说明 |
|------|------|
| `./data/` | SQLite 数据库文件 (autoai.db) |
| `./logs/` | 应用日志文件 (autoai.log) |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接字符串 | `sqlite+aiosqlite:///./data/autoai.db` |
| LOG_LEVEL | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) | `INFO` |
| ADMIN_PASSWORD | 管理密码 | **必需，无默认值** |

### 故障排查

**容器无法启动：**
```bash
# 查看容器日志
docker-compose logs autoai

# 检查 .env 文件是否存在且 ADMIN_PASSWORD 已设置
cat .env
```

**健康检查失败：**
```bash
# 进入容器检查
docker-compose exec autoai bash

# 容器内测试
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```
```

### References

**源文档：**
- _bmad-output/architecture.md (Infrastructure & Deployment)
- _bmad-output/prd.md (FR14, FR15, NFR5)
- _bmad-output/epics.md (Story 1.3: Docker 容器化部署)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

- 发现并修复 `app/main.py` 和 `app/database.py` 中的导入错误：`from app.config import settings` → `from app.config import get_settings`
- 原因：`config.py` 使用懒加载模式，只导出 `Settings` 类和 `get_settings()` 函数，不导出 `settings` 实例

### Completion Notes List

1. **Task 1-2 (验证 Dockerfile 和 docker-compose.yml)**: 所有配置项均符合要求，无需修改
2. **Task 3 (创建 .dockerignore)**: 新建文件，排除敏感信息和不必要的开发文件
3. **Task 4 (端到端验证)**:
   - 用户跳过 Docker 命令测试
   - 通过代码测试验证应用可正常运行
   - 修复了 `settings` 导入错误（main.py:8, database.py:8）
   - 健康检查端点 `/health` 返回 `{"status": "healthy"}`
   - 所有 12 个测试通过
4. **Task 5 (更新 README.md)**: 添加完整 Docker 部署文档（前置条件、快速启动、常用命令、数据持久化、环境变量、故障排查）

### File List

**新建文件：**
- `.dockerignore` - Docker 构建忽略文件
- `.env` - 环境变量配置文件（从 .env.example 复制）
- `tests/test_health.py` - 健康检查端点测试（代码审查新增）

**修改文件：**
- `app/main.py` - 修复 settings 导入为 get_settings()
- `app/database.py` - 修复 settings 导入为 get_settings()
- `README.md` - 添加完整 Docker 部署文档
- `tests/conftest.py` - 添加 pytest-asyncio 配置（代码审查新增）
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Sprint 状态更新

**验证文件（无修改）：**
- `Dockerfile` - 配置正确
- `docker-compose.yml` - 配置正确

### Change Log

- 2025-12-20: Story 1.3 实现完成 - Docker 容器化部署配置验证、.dockerignore 创建、README 文档更新、导入错误修复
- 2025-12-20: 代码审查修复 - 添加健康检查端点测试 (test_health.py)、更新 File List、更新验证清单状态

