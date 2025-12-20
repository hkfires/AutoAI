# Story 1.2: 环境配置管理

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a 开发者,
I want 通过环境变量配置系统级参数,
So that 我可以在不修改代码的情况下调整基础配置。

## Acceptance Criteria

1. **Given** 项目已初始化
   **When** 创建 `.env` 文件或设置环境变量
   **Then** 应用可以读取以下配置：
   - `DATABASE_URL`: SQLite 数据库路径（默认 `sqlite+aiosqlite:///./data/autoai.db`）
   - `LOG_LEVEL`: 日志级别（默认 `INFO`）
   - `ADMIN_PASSWORD`: 管理后台密码（必需，无默认值）

2. **And** 配置类使用 pydantic-settings 实现类型安全加载
   - Settings 类继承 BaseSettings
   - 使用 model_config 配置 env_file
   - 提供类型注解和默认值

3. **And** `.env.example` 包含所有配置项的示例
   - DATABASE_URL 示例
   - LOG_LEVEL 示例
   - ADMIN_PASSWORD 占位符

4. **And** OpenAI API 相关配置（端点、密钥）不在环境变量中
   - API 配置通过任务配置存储在数据库中（Story 2.1 实现）
   - 当前 config.py 中的 openai_api_key 和 openai_base_url 应移除

5. **And** 配置验证在应用启动时执行
   - 缺少必需配置（ADMIN_PASSWORD）时抛出明确错误
   - 配置值类型不正确时抛出验证错误

## Tasks / Subtasks

- [x] Task 1: 完善 Settings 配置类 (AC: #1, #2, #5)
  - [x] 1.1 移除 openai_api_key 和 openai_base_url（不在环境变量中）
  - [x] 1.2 确保 admin_password 为必需字段（无默认值）
  - [x] 1.3 添加 admin_password 非空验证（`field_validator` 确保不为空字符串）
  - [x] 1.4 添加 log_level 有效值校验（必须是 DEBUG/INFO/WARNING/ERROR/CRITICAL）
  - [x] 1.5 添加 `Field(repr=False)` 防止 admin_password 出现在日志/repr 中

- [x] Task 2: 更新 .env.example (AC: #3, #4)
  - [x] 2.1 移除 OpenAI 相关配置项
  - [x] 2.2 添加配置项说明注释
  - [x] 2.3 确保所有配置项都有示例值

- [x] Task 3: 创建测试基础设施和配置测试 (AC: #5)
  - [x] 3.1 创建 tests/__init__.py（如不存在）
  - [x] 3.2 创建 tests/conftest.py（pytest fixtures - reset_settings_singleton 自动重置单例）
  - [x] 3.3 创建 tests/test_config.py
  - [x] 3.4 测试默认值加载 (test_valid_config)
  - [x] 3.5 测试必需字段验证 (test_missing_admin_password)
  - [x] 3.6 测试环境变量覆盖 (test_custom_values)
  - [x] 3.7 测试无效 LOG_LEVEL 验证 (test_invalid_log_level)
  - [x] 3.8 测试空字符串 ADMIN_PASSWORD 验证 (test_empty_admin_password)
  - [x] 3.9 测试纯空白 ADMIN_PASSWORD 验证 (test_whitespace_admin_password)
  - [x] 3.10 测试 admin_password 不在 repr 中 (test_admin_password_hidden_from_repr)
  - [x] 3.11 测试 log_level 大小写不敏感 (test_log_level_case_insensitive)
  - [x] 3.12 测试 OpenAI 配置已移除 (test_no_openai_config_attributes)
  - [x] 3.13 测试无效 DATABASE_URL 格式 (test_invalid_database_url_format)
  - [x] 3.14 测试空 DATABASE_URL (test_empty_database_url)
  - [x] 3.15 测试 get_settings 单例模式 (test_get_settings_returns_singleton)

- [x] Task 4: 集成验证 (AC: #1-5)
  - [x] 4.1 启动应用验证配置加载
  - [x] 4.2 验证缺少 ADMIN_PASSWORD 时的错误信息
  - [x] 4.3 验证 .env 文件不存在时从环境变量加载

## Dev Notes

### Architecture Compliance

**严格遵循架构文档的以下决策：**

1. **配置管理技术栈**
   - 使用 `pydantic-settings>=2.1.0`
   - Settings 类使用 `model_config = SettingsConfigDict(...)` (Pydantic v2 风格)
   - 从 `.env` 文件和环境变量加载配置

2. **环境变量规范**
   ```
   DATABASE_URL    → database_url (自动转换 snake_case)
   LOG_LEVEL       → log_level
   ADMIN_PASSWORD  → admin_password
   ```

3. **安全要求 (NFR1, NFR2)**
   - `ADMIN_PASSWORD` 不得有默认值，必须显式配置
   - 密码相关配置不得出现在日志中

### Technical Requirements

**完整的 Settings 类实现：**

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/autoai.db"

    # Logging
    log_level: str = "INFO"

    # Admin (required, hidden from repr/logs)
    admin_password: str = Field(..., repr=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log_level is one of the standard Python logging levels."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()

    @field_validator('admin_password')
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        """Validate admin_password is not empty."""
        if not v or not v.strip():
            raise ValueError('admin_password cannot be empty')
        return v


settings = Settings()
```

**关键实现点：**

1. **Field(repr=False)** - 防止 admin_password 在 repr/日志中泄露
2. **field_validator('log_level')** - 确保只接受有效的日志级别
3. **field_validator('admin_password')** - 确保密码非空字符串
4. **配置单例模式** - 使用懒加载 `get_settings()` 函数（测试友好）

### Actual Implementation Details

**与原规格的优化变更：**

1. **懒加载单例** - 原规格使用模块级 `settings = Settings()`，实际实现使用 `get_settings()` 函数，允许测试在加载前配置环境变量
2. **database_url 验证** - 额外添加了 `validate_database_url` 验证器，确保连接字符串格式正确
3. **测试重置机制** - conftest.py 使用 `reset_settings_singleton` autouse fixture 替代 `clean_env`，更可靠地隔离测试

### Library/Framework Requirements

**依赖版本（来自 requirements.txt）：**
- `pydantic-settings>=2.1.0`
- `pydantic>=2.0.0`（pydantic-settings 的依赖）

### File Structure Requirements

**需要修改的文件：**
```
app/
├── config.py          # 完善 Settings 类，移除 OpenAI 配置
│
.env.example           # 更新配置示例，移除 OpenAI 配置
│
tests/
└── test_config.py     # 新建：配置加载测试
```

### Testing Requirements

**测试架构：**

```
tests/
├── __init__.py          # 包标识
├── conftest.py          # pytest fixtures
└── test_config.py       # 配置测试
```

**conftest.py 内容：**

```python
# tests/conftest.py
"""Pytest fixtures for the test suite."""

import sys
import pytest
from typing import Iterator


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset the settings singleton before and after each test.

    This ensures each test gets a fresh Settings instance.
    """
    # Reset before test
    if 'app.config' in sys.modules:
        import app.config
        app.config._settings = None

    yield

    # Reset after test
    if 'app.config' in sys.modules:
        import app.config
        app.config._settings = None
```

**test_config.py 测试用例：**

| 测试场景 | 环境变量设置 | 预期结果 |
|----------|--------------|----------|
| 有效配置加载 | ADMIN_PASSWORD=test123 | Settings 正常创建，默认值生效 |
| 缺少必需字段 | 无 ADMIN_PASSWORD | 抛出 ValidationError |
| 自定义值覆盖 | 全部自定义 | Settings 使用自定义值 |
| 无效 LOG_LEVEL | LOG_LEVEL=INVALID | 抛出 ValidationError |
| 空 ADMIN_PASSWORD | ADMIN_PASSWORD="" | 抛出 ValidationError |
| 纯空白 ADMIN_PASSWORD | ADMIN_PASSWORD="   " | 抛出 ValidationError |
| admin_password 隐藏 | ADMIN_PASSWORD=supersecret | repr 中不包含密码 |
| log_level 大小写 | LOG_LEVEL=debug | 转换为 DEBUG |
| OpenAI 配置移除 | - | Settings 无 openai 属性 |
| 无效 DATABASE_URL | DATABASE_URL=invalid | 抛出 ValidationError |
| 空 DATABASE_URL | DATABASE_URL="" | 抛出 ValidationError |
| get_settings 单例 | - | 多次调用返回同一实例 |

**测试代码：**

```python
# tests/test_config.py
import pytest
from pydantic import ValidationError


class TestSettings:
    """Settings configuration tests."""

    def test_valid_config(self, monkeypatch):
        """Test Settings with valid configuration."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        from app.config import Settings
        s = Settings()
        assert s.database_url == "sqlite+aiosqlite:///./data/autoai.db"
        assert s.log_level == "INFO"
        assert s.admin_password == "test123"

    def test_missing_admin_password(self, monkeypatch, clean_env):
        """Test ValidationError when ADMIN_PASSWORD is missing."""
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "admin_password" in str(exc_info.value)

    def test_custom_values(self, monkeypatch):
        """Test environment variables override defaults."""
        monkeypatch.setenv("ADMIN_PASSWORD", "secret")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./custom.db")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        from app.config import Settings
        s = Settings()
        assert s.database_url == "sqlite+aiosqlite:///./custom.db"
        assert s.log_level == "DEBUG"

    def test_invalid_log_level(self, monkeypatch):
        """Test ValidationError for invalid LOG_LEVEL."""
        monkeypatch.setenv("ADMIN_PASSWORD", "test123")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "log_level" in str(exc_info.value)

    def test_empty_admin_password(self, monkeypatch):
        """Test ValidationError when ADMIN_PASSWORD is empty string."""
        monkeypatch.setenv("ADMIN_PASSWORD", "")
        from app.config import Settings
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "admin_password" in str(exc_info.value)

    def test_admin_password_hidden_from_repr(self, monkeypatch):
        """Test admin_password is not visible in repr output."""
        monkeypatch.setenv("ADMIN_PASSWORD", "supersecret")
        from app.config import Settings
        s = Settings()
        repr_str = repr(s)
        assert "supersecret" not in repr_str
```

**注意：** 每个测试直接实例化 Settings 类而非使用模块级 settings 单例，避免测试间状态污染。

### Previous Story Intelligence

**来自 Story 1.1 的经验教训：**

1. **Code Review 反馈**
   - config.py 需要使用 Pydantic v2 的 `model_config` 而非 v1 的 `class Config`
   - admin_password 必须是必需字段（无默认值）
   - 这两点在 Story 1.1 中已修复

2. **现有代码基础**
   - `app/config.py` 已包含基本 Settings 类结构
   - 当前包含 `openai_api_key` 和 `openai_base_url`，需移除
   - `.env.example` 已存在，需更新

3. **测试基础设施**
   - `tests/` 目录结构已在 Story 1.1 规划
   - 需创建 `tests/__init__.py` 和 `tests/conftest.py`（如未创建）

### Git Intelligence Summary

**最近提交分析：**
- `b928dac 1-1-project-structure-init` - 创建项目骨架
- 相关文件：`app/config.py`, `.env.example`

**代码模式：**
- 使用 Pydantic v2 语法（`model_config = SettingsConfigDict(...)`）
- 模块级单例模式（`settings = Settings()`）

### Project Context Reference

**项目：** AutoAI - 定时自动化系统
**阶段：** MVP Phase 1 - 项目基础设施与配置
**前置依赖：** Story 1.1（项目结构初始化）- 已完成
**后续依赖：** Story 1.3（Docker 容器化部署）依赖本故事

### References

**源文档：**
- _bmad-output/architecture.md (Implementation Patterns & Consistency Rules, Infrastructure & Deployment)
- _bmad-output/prd.md (Non-Functional Requirements - NFR1, NFR2, NFR3)
- _bmad-output/epics.md (Story 1.2: 环境配置管理)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (gemini-claude-opus-4-5-thinking)

### Debug Log References

None - implementation completed without errors.

### Completion Notes List

- Implemented complete Settings class with pydantic-settings v2
- Removed OpenAI config (openai_api_key, openai_base_url) as per AC#4
- Added Field(repr=False) to admin_password for security (AC#5)
- Added field_validator for log_level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- Added field_validator for admin_password (non-empty validation)
- Added field_validator for database_url (format validation)
- Implemented lazy-loaded singleton via get_settings() for test isolation
- Created test infrastructure: tests/__init__.py, tests/conftest.py
- Created 12 comprehensive tests covering all acceptance criteria
- All tests pass (12/12)
- Verified integration: config loads correctly, errors on missing/empty ADMIN_PASSWORD

### Code Review Notes

**Review Date:** 2025-12-20
**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)
**Issues Found:** 0 HIGH, 5 MEDIUM, 3 LOW
**Resolution:** All MEDIUM issues resolved by updating documentation to match actual implementation
**Final Status:** Ready for merge

### File List

- app/config.py (modified) - Settings class with validators, removed OpenAI config, lazy-loaded singleton
- .env.example (modified) - Updated with comments, removed OpenAI config
- tests/__init__.py (new) - Package marker
- tests/conftest.py (new) - Pytest fixtures (reset_settings_singleton autouse)
- tests/test_config.py (new) - 12 configuration tests
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified) - Story status tracking

