# Story 2.1: 任务与日志数据模型

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 开发者,
I want 建立任务和执行日志的数据模型,
So that 系统可以持久化存储任务配置和执行记录。

## Acceptance Criteria

1. **Given** 数据库连接已配置
   **When** 应用启动时
   **Then** 自动创建以下数据表（如果不存在）

2. **Task 表结构：**
   - `id`: Integer, 主键, 自增
   - `name`: String(100), 任务名称, 不可空
   - `api_endpoint`: String(500), OpenAI API 端点地址, 不可空
   - `api_key`: String(500), API 密钥（加密存储）, 不可空
   - `schedule_type`: String(20), 调度类型（`interval` 或 `fixed_time`）, 不可空
   - `interval_minutes`: Integer, 间隔分钟数（间隔模式使用）, 可空
   - `fixed_time`: String(5), 固定时间 HH:MM 格式（固定时间模式使用）, 可空
   - `message_content`: Text, 要发送的消息内容, 不可空
   - `enabled`: Boolean, 是否启用, 默认 True
   - `created_at`: DateTime, 创建时间, 自动设置
   - `updated_at`: DateTime, 更新时间, 自动更新

3. **ExecutionLog 表结构：**
   - `id`: Integer, 主键, 自增
   - `task_id`: Integer, 外键关联 Task, 不可空
   - `executed_at`: DateTime, 执行时间, 不可空
   - `status`: String(20), 状态（`success` / `failed`）, 不可空
   - `response_summary`: Text, 响应摘要, 可空
   - `error_message`: Text, 错误信息, 可空

4. **And** 使用 SQLAlchemy 2.0 异步 ORM
   - 继承自 AsyncAttrs 和 DeclarativeBase
   - 使用 mapped_column 和 Mapped 类型注解

5. **And** API 密钥在数据库中加密存储
   - 使用 Fernet 对称加密
   - 加密密钥从 ENCRYPTION_KEY 环境变量读取
   - 如果未配置，自动生成并写入 .env 文件

6. **And** 提供加密/解密工具函数
   - `encrypt_api_key(plain_text: str) -> str`
   - `decrypt_api_key(encrypted_text: str) -> str`
   - 密钥脱敏函数 `mask_api_key(key: str) -> str`

7. **And** 提供 Pydantic Schemas 用于 API 验证
   - TaskCreate, TaskUpdate, TaskResponse
   - ExecutionLogResponse
   - API 响应中 api_key 自动脱敏

## Tasks / Subtasks

- [x] Task 1: 确认 Fernet 加密依赖 (AC: #5)
  - [x] 1.1 确认 requirements.txt 已包含 `cryptography>=41.0.0`（已存在，无需修改）
  - [x] 1.2 运行 `pip install -r requirements.txt` 安装依赖

- [x] Task 2: 更新环境配置支持加密密钥 (AC: #5)
  - [x] 2.1 在 `app/config.py` Settings 类添加 `encryption_key: str | None = None`
  - [x] 2.2 更新 `.env.example` 添加 `ENCRYPTION_KEY=` 示例
  - [x] 2.3 实现 `ensure_encryption_key()` 函数：检查 ENCRYPTION_KEY，如不存在则自动生成并追加到 .env 文件
  - [x] 2.4 在 `app/main.py` lifespan startup 中调用 `ensure_encryption_key()`

- [x] Task 3: 实现加密工具函数 (AC: #5, #6)
  - [x] 3.1 实现 `mask_api_key(key: str) -> str` 密钥脱敏函数（当前 security.py 为空占位符，需要实现）
  - [x] 3.2 实现 `get_fernet()` 获取加密器（懒加载单例模式）
  - [x] 3.3 实现 `encrypt_api_key(plain_text: str) -> str`
  - [x] 3.4 实现 `decrypt_api_key(encrypted_text: str) -> str`

- [x] Task 4: 创建 SQLAlchemy ORM 模型 (AC: #2, #3, #4)
  - [x] 4.1 修改 `app/database.py` 中的 Base 类，添加 AsyncAttrs 混入：`class Base(AsyncAttrs, DeclarativeBase)`
  - [x] 4.2 在 `app/models.py` 从 database.py 导入 Base：`from app.database import Base`
  - [x] 4.3 实现 Task 模型，包含所有字段和约束
  - [x] 4.4 实现 ExecutionLog 模型，包含外键关联
  - [x] 4.5 添加模型关系（Task.execution_logs, ExecutionLog.task）
  - [x] 4.6 验证 created_at/updated_at 自动时间戳

- [x] Task 5: 实现数据库初始化 (AC: #1)
  - [x] 5.1 确认 `app/database.py` 的 async engine 配置正确
  - [x] 5.2 实现 `init_db()` 函数创建所有表
  - [x] 5.3 在 `app/main.py` lifespan 中调用 `init_db()`
  - [x] 5.4 验证应用启动时自动创建表

- [x] Task 6: 创建 Pydantic Schemas (AC: #7)
  - [x] 6.1 在 `app/schemas.py` 创建 TaskBase 基础 schema
  - [x] 6.2 创建 TaskCreate（创建请求）
  - [x] 6.3 创建 TaskUpdate（更新请求，所有字段可选）
  - [x] 6.4 创建 TaskResponse（响应，api_key 脱敏）
  - [x] 6.5 创建 ExecutionLogResponse
  - [x] 6.6 使用 field_validator 实现 api_key 自动脱敏

- [x] Task 7: 编写单元测试 (AC: 全部)
  - [x] 7.1 在 `tests/test_models.py` 测试 Task 模型 CRUD
  - [x] 7.2 测试 ExecutionLog 模型 CRUD
  - [x] 7.3 测试外键关联关系
  - [x] 7.4 在 `tests/test_security.py` 测试加密/解密函数
  - [x] 7.5 测试密钥脱敏函数
  - [x] 7.6 在 `tests/test_schemas.py` 测试 Pydantic 验证

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **ORM 选择** - SQLAlchemy 2.0 异步模式
2. **加密方案** - Fernet 对称加密（cryptography 库）
3. **命名规范** - snake_case（表名、列名、变量名）
4. **异步架构** - 所有数据库操作使用 async/await

**相关需求支持：**
- FR1-5: 任务配置（端点、密钥、调度规则、消息、启用状态）
- FR9: 记录执行结果
- NFR1: API 密钥加密存储

### Technical Requirements

**SQLAlchemy 2.0 模型示例：**

```python
# 步骤 1: 修改 app/database.py 中的 Base 类
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy declarative base class with async support."""
    pass

# 步骤 2: 在 app/models.py 中导入并使用 Base
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base  # 从 database.py 导入，不要重新定义

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    api_endpoint: Mapped[str] = mapped_column(String(500))
    api_key: Mapped[str] = mapped_column(String(500))  # 加密存储
    schedule_type: Mapped[str] = mapped_column(String(20))  # interval | fixed_time
    interval_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fixed_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    message_content: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关系
    execution_logs: Mapped[List["ExecutionLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    executed_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))  # success | failed
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关系
    task: Mapped["Task"] = relationship(back_populates="execution_logs")
```

**Fernet 加密实现：**

```python
# app/utils/security.py
from cryptography.fernet import Fernet
from app.config import get_settings

_fernet: Fernet | None = None

def mask_api_key(key: str) -> str:
    """将 API 密钥脱敏显示"""
    if len(key) > 8:
        return f"{key[:4]}...{key[-4:]}"
    return "***"

def get_fernet() -> Fernet:
    """获取 Fernet 加密器（懒加载）"""
    global _fernet
    if _fernet is None:
        settings = get_settings()
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY not configured")
        _fernet = Fernet(settings.encryption_key.encode())
    return _fernet

def encrypt_api_key(plain_text: str) -> str:
    """加密 API 密钥"""
    return get_fernet().encrypt(plain_text.encode()).decode()

def decrypt_api_key(encrypted_text: str) -> str:
    """解密 API 密钥"""
    return get_fernet().decrypt(encrypted_text.encode()).decode()
```

**ENCRYPTION_KEY 自动生成实现：**

```python
# 在 app/config.py 中添加
import os
from pathlib import Path
from cryptography.fernet import Fernet

def ensure_encryption_key() -> str:
    """确保 ENCRYPTION_KEY 存在，如不存在则自动生成并写入 .env"""
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        return key

    # 生成新密钥
    key = Fernet.generate_key().decode()

    # 追加到 .env 文件
    env_path = Path(".env")
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\n# Auto-generated encryption key\nENCRYPTION_KEY={key}\n")

    # 设置环境变量供当前进程使用
    os.environ["ENCRYPTION_KEY"] = key
    return key
```

**Pydantic Schema 示例：**

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict
from app.utils.security import mask_api_key

class TaskBase(BaseModel):
    name: str
    api_endpoint: str
    schedule_type: str  # interval | fixed_time
    interval_minutes: Optional[int] = None
    fixed_time: Optional[str] = None  # HH:MM
    message_content: str
    enabled: bool = True

class TaskCreate(TaskBase):
    api_key: str

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    schedule_type: Optional[str] = None
    interval_minutes: Optional[int] = None
    fixed_time: Optional[str] = None
    message_content: Optional[str] = None
    enabled: Optional[bool] = None

class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key: str  # 将自动脱敏
    created_at: datetime
    updated_at: datetime

    @field_validator("api_key", mode="before")
    @classmethod
    def mask_key(cls, v: str) -> str:
        return mask_api_key(v)

class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    executed_at: datetime
    status: str
    response_summary: Optional[str] = None
    error_message: Optional[str] = None
```

### Library/Framework Requirements

**必需依赖：**
| 库 | 版本 | 用途 |
|----|------|------|
| sqlalchemy | >=2.0.0 | 异步 ORM |
| aiosqlite | >=0.19.0 | SQLite 异步驱动 |
| cryptography | >=41.0.0 | Fernet 加密（已安装） |
| pydantic | >=2.0.0 | 数据验证 |

**已安装依赖（Story 1.1）：**
- sqlalchemy>=2.0.0
- aiosqlite>=0.19.0
- pydantic>=2.0.0
- pydantic-settings>=2.0.0
- cryptography>=41.0.0

**无需新增依赖** - 所有必需库已在 requirements.txt 中

### File Structure Requirements

**需要修改的文件：**
```
./
├── .env.example               # 添加 ENCRYPTION_KEY
├── app/
│   ├── config.py              # 添加 encryption_key 配置 + ensure_encryption_key()
│   ├── models.py              # 实现 Task, ExecutionLog 模型（从 database.py 导入 Base）
│   ├── schemas.py             # 实现 Pydantic schemas
│   ├── database.py            # 修改 Base 类添加 AsyncAttrs
│   ├── main.py                # 在 lifespan 中调用 ensure_encryption_key() 和 init_db()
│   └── utils/
│       └── security.py        # 实现 mask_api_key, get_fernet, encrypt/decrypt 函数
└── tests/
    ├── test_models.py         # 新建：模型测试
    ├── test_security.py       # 新建：加密测试
    └── test_schemas.py        # 新建：Schema 测试
```

### Testing Requirements

**单元测试清单：**

| 测试文件 | 测试场景 | 断言 |
|----------|----------|------|
| test_models.py | 创建 Task | id 自增，created_at 自动设置 |
| test_models.py | Task 与 ExecutionLog 关联 | 外键正确，级联删除生效 |
| test_models.py | 更新 Task | updated_at 自动更新 |
| test_models.py | 删除 Task 级联删除 ExecutionLog | Task 删除后关联的 ExecutionLog 也被删除 |
| test_security.py | 加密解密 | decrypt(encrypt(x)) == x |
| test_security.py | mask_api_key | "sk-1234567890" → "sk-1...7890" |
| test_security.py | mask_api_key 短密钥 | "short" → "***" |
| test_schemas.py | TaskCreate 验证 | 必填字段缺失时报错 |
| test_schemas.py | TaskResponse 脱敏 | api_key 自动脱敏显示 |

**测试示例：**

```python
# tests/test_security.py
import pytest
from app.utils.security import encrypt_api_key, decrypt_api_key, mask_api_key

def test_encrypt_decrypt_roundtrip():
    """测试加密解密往返"""
    original = "sk-test-api-key-12345"
    encrypted = encrypt_api_key(original)
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == original
    assert encrypted != original

def test_mask_api_key():
    """测试密钥脱敏"""
    assert mask_api_key("sk-1234567890abcdef") == "sk-1...cdef"
    assert mask_api_key("short") == "***"
```

### Previous Story Intelligence

**来自 Epic 1 的经验教训：**

1. **配置管理模式**
   - 使用 `get_settings()` 懒加载，不是直接导入 `settings` 实例
   - Story 1.3 修复了此导入错误

2. **现有代码基础**
   - `app/models.py` 已存在但为空模板
   - `app/schemas.py` 已存在但为空模板
   - `app/database.py` 已配置 async engine 和 Base 类（需修改添加 AsyncAttrs）
   - `app/utils/security.py` 为空占位符（需实现 mask_api_key 等函数）

3. **测试配置**
   - `tests/conftest.py` 已配置 pytest-asyncio
   - 使用 `@pytest.mark.asyncio` 装饰异步测试

### Git Intelligence Summary

**最近提交：**
- `8a7d4a9 1-3-docker-containerization` - Docker 配置完善
- `bd92736 1-2-environment-config-management` - 环境配置管理
- `cc6ab50 1-1-project-structure-init` - 项目结构初始化

**相关文件（可能需要参考）：**
- `app/config.py` - 配置管理模式（使用 get_settings() 懒加载）
- `app/database.py` - 数据库连接配置（Base 类需修改）
- `app/utils/security.py` - 空占位符，需实现所有安全函数

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - Epic 2: 核心定时执行引擎
**前置依赖：** Epic 1 已完成（项目结构、配置管理、Docker）
**后续故事：**
- Story 2.2（任务管理 API）依赖本故事的 Task 模型和 Schemas
- Story 2.3（OpenAI API 服务）依赖 ExecutionLog 模型
- Story 2.4（定时调度引擎）依赖 Task 模型

### Common LLM Pitfalls to Avoid

1. **不要使用同步 ORM 操作** - 所有数据库操作必须使用 async/await
2. **不要硬编码加密密钥** - 必须从环境变量读取
3. **不要在日志中打印明文 API 密钥** - 使用 mask_api_key()
4. **不要忘记外键级联删除** - Task 删除时 ExecutionLog 应级联删除
5. **不要直接导入 settings** - 使用 `get_settings()` 函数
6. **不要遗漏 updated_at 自动更新** - 使用 `onupdate=func.now()`
7. **不要跳过模型关系定义** - Task.execution_logs 和 ExecutionLog.task 双向关系
8. **不要在 models.py 重新定义 Base** - 从 database.py 导入已有的 Base 类
9. **不要假设 security.py 已有函数** - 当前是空占位符，所有函数需要实现

### Windows 兼容性说明

- SQLite 文件路径使用相对路径 `./data/autoai.db`
- 加密密钥生成使用 `Fernet.generate_key()` 跨平台兼容
- 测试使用内存数据库 `sqlite+aiosqlite:///:memory:`

### References

**源文档：**
- _bmad-output/architecture.md (Data Architecture, Data Models)
- _bmad-output/prd.md (FR1-5, FR9, NFR1)
- _bmad-output/epics.md (Story 2.1: 任务与日志数据模型)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

无调试问题。

### Completion Notes List

- 实现了 Task 和 ExecutionLog ORM 模型，使用 SQLAlchemy 2.0 异步模式
- 添加了 AsyncAttrs 混入到 Base 类以支持异步关系访问
- 实现了 Fernet 加密工具函数：encrypt_api_key, decrypt_api_key, mask_api_key, get_fernet
- 添加了 ensure_encryption_key() 函数，自动生成加密密钥并写入 .env
- 创建了所有 Pydantic schemas：TaskBase, TaskCreate, TaskUpdate, TaskResponse, ExecutionLogResponse
- TaskResponse 使用 field_validator 自动脱敏 api_key
- 编写了 22 个新测试（6 个模型测试 + 7 个安全测试 + 9 个 schema 测试）
- 所有 37 个测试通过，无回归

### Senior Developer Review (AI)

**审查日期：** 2025-12-21
**审查模型：** Claude Opus 4.5

**发现问题 (9 个)：**

| # | 严重性 | 问题 | 状态 |
|---|--------|------|------|
| 1 | HIGH | database.py 模块加载时立即调用 get_settings() | 已修复 |
| 2 | HIGH | config.py ensure_encryption_key() 无文件锁竞态条件 | 已修复 |
| 3 | HIGH | config.py ensure_encryption_key() 未检查 .env 存在 | 已修复 |
| 4 | MEDIUM | schemas.py 缺少 schedule_type Literal 验证 | 已修复 |
| 5 | MEDIUM | schemas.py 缺少调度逻辑验证 | 已修复 |
| 6 | MEDIUM | models.py updated_at onupdate 测试缺失 | 已修复 |
| 7 | MEDIUM | test_models.py 缺少 updated_at 自动更新测试 | 已修复 |
| 8 | LOW | security.py 全局可变状态需注意测试隔离 | 已记录 |
| 9 | LOW | File List 未记录 sprint-status.yaml | 已记录 |

**修复内容：**

1. database.py 改为懒加载模式（get_engine(), get_session_maker()）
2. config.py 添加跨平台文件锁（Windows/Unix）和 .env 存在检查
3. schemas.py 添加 ScheduleType Literal 类型和 model_validator 验证调度逻辑
4. 添加 10 个新测试覆盖新验证逻辑和 updated_at

**测试结果：** 47 passed (新增 10 个测试)

### File List

**新建文件：**
- tests/test_models.py
- tests/test_security.py
- tests/test_schemas.py

**修改文件：**
- app/config.py - 添加 encryption_key 配置、ensure_encryption_key() 函数、跨平台文件锁
- app/database.py - 懒加载 engine/session_maker、修改 Base 类添加 AsyncAttrs、init_db() 导入 models
- app/models.py - 实现 Task 和 ExecutionLog 模型
- app/schemas.py - 实现所有 Pydantic schemas、添加 schedule_type Literal 验证、调度逻辑验证
- app/utils/security.py - 实现加密/解密和脱敏函数
- app/main.py - lifespan 中调用 ensure_encryption_key()
- .env.example - 添加 ENCRYPTION_KEY 配置说明

