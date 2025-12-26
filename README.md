# AutoAI

自动化 AI 任务执行系统 - 基于 FastAPI 的定时任务调度平台。

## 功能特性

- 定时执行 AI 任务（调用 OpenAI API）
- Web 管理界面
- 执行日志查看
- 支持多种调度策略

## 技术栈

- **Web 框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy (异步)
- **调度器**: APScheduler
- **HTTP 客户端**: httpx
- **配置管理**: pydantic-settings
- **日志**: loguru

## 快速开始

### 环境要求

- Python 3.11+
- Docker (可选)

### 本地开发

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 4. 启动应用
uvicorn app.main:app --reload
```

### Docker 部署

#### 前置条件

- Docker >= 20.10
- Docker Compose >= 2.0

#### 快速启动

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
   docker compose up -d --build
   ```

4. 等待健康检查通过（约 30 秒）：
   ```bash
   docker compose ps
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

#### 常用命令

| 操作 | 命令 |
|------|------|
| 启动服务 | `docker compose up -d` |
| 停止服务 | `docker compose down` |
| 重启服务 | `docker compose restart` |
| 查看日志 | `docker compose logs -f` |
| 查看状态 | `docker compose ps` |
| 重新构建 | `docker compose up -d --build` |
| 进入容器 | `docker compose exec autoai bash` |

#### 数据持久化

以下目录通过 Docker Volume 挂载，数据在容器重启后保留：

| 目录 | 说明 |
|------|------|
| `./data/` | SQLite 数据库文件 (autoai.db) |
| `./logs/` | 应用日志文件 (autoai.log) |

#### 故障排查

**容器无法启动：**
```bash
# 查看容器日志
docker compose logs autoai

# 检查 .env 文件是否存在且 ADMIN_PASSWORD 已设置
cat .env
```

**健康检查失败：**
```bash
# 进入容器检查
docker compose exec autoai bash

# 或直接在容器内测试
docker compose exec autoai python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | 数据库连接字符串 | `sqlite+aiosqlite:///./data/autoai.db` |
| LOG_LEVEL | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) | `INFO` |
| ADMIN_PASSWORD | 管理密码 | **必需，无默认值** |
| ENCRYPTION_KEY | API Key 加密密钥 | 本地开发自动生成，Docker 需手动设置 |

### 生成 ENCRYPTION_KEY

`ENCRYPTION_KEY` 用于加密存储 API Key。本地开发时会自动生成并保存到 `.env` 文件，Docker 部署时需手动设置。

生成方法：

```bash
# 方式1：使用 Docker 容器生成（需要先安装 cryptography）
docker run --rm python:3.11-slim sh -c "pip install -q cryptography && python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""

# 方式2：使用 docker compose exec（容器已启动时）
docker compose exec autoai python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 方式3：本地 Python 环境
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将生成的密钥添加到 `.env` 文件：
```bash
ENCRYPTION_KEY=your_generated_key_here
```

> ⚠️ **重要**：如果更换 `ENCRYPTION_KEY`，之前加密的 API Key 将无法解密，需要重新配置。

## 项目结构

```
autoai/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI 入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── models.py          # ORM 模型
│   ├── schemas.py         # Pydantic schemas
│   ├── scheduler.py       # 调度器配置
│   ├── api/               # API 路由
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── data/                   # 数据持久化
├── logs/                   # 日志文件
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 镜像
└── docker-compose.yml     # Docker Compose 配置
```

## API 文档

启动应用后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
