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

```bash
# 使用 docker-compose 启动
docker-compose up -d
```

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
