# 技术规格：真正的并发任务执行

**创建日期：** 2025-12-26
**状态：** 已完成

## 概述

### 问题陈述

当前调度器虽然移除了显式的 `max_instances=1`，但 APScheduler 默认值仍为 1，导致任务实际上是串行执行的。当一个任务执行时间超过调度间隔时，后续触发会被跳过而非并发执行。

### 解决方案

显式设置 `max_instances` 为一个极大值（如 999999），实现真正的 fire-and-forget 并发模式：每次调度触发都立即启动新的任务实例，不等待之前的实例完成。

### 范围

**包含：**
- 修改 `scheduler.py` 中的 `add_job` 调用，添加 `max_instances` 参数

**不包含：**
- 并发实例数上限配置（全局无限制）
- 单任务并发开关（全局设置）
- 资源限制或节流机制

## 开发上下文

### 代码库模式

| 层级 | 技术 | 说明 |
|------|------|------|
| 调度器 | APScheduler AsyncIOScheduler | 异步任务调度 |
| 执行 | asyncio | 协程并发执行 |

### 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `app/scheduler.py:113-120` | 在 `add_job` 调用中添加 `max_instances=999999` |

### 技术决策

1. **max_instances 值**：使用 999999 作为"无限制"的实际值
2. **全局设置**：所有任务统一使用此配置，无需用户选择
3. **coalesce 保持 True**：调度器暂停后恢复时合并错过的执行（极端情况）

## 实现计划

### 任务列表

- [x] **任务 1**：修改 `app/scheduler.py` 的 `register_task` 函数
  - 在 `scheduler.add_job()` 调用中添加 `max_instances=999999`

### 验收标准

- [x] **AC 1**：并发执行正常工作
  - Given: 一个间隔 1 秒的任务，执行时间约 5 秒
  - When: 调度器连续触发 5 次
  - Then: 同时存在 5 个并发执行的实例

- [x] **AC 2**：每次触发独立执行
  - Given: 任务正在执行中
  - When: 到达下一个触发时间
  - Then: 立即启动新实例，不等待、不跳过

## 附加上下文

### 代码修改示例

**修改前 (`scheduler.py:113-120`)：**
```python
scheduler.add_job(
    execute_task,
    trigger=trigger,
    id=job_id,
    args=[task.id],
    replace_existing=True,
    coalesce=True,
)
```

**修改后：**
```python
scheduler.add_job(
    execute_task,
    trigger=trigger,
    id=job_id,
    args=[task.id],
    replace_existing=True,
    coalesce=True,
    max_instances=999999,  # 允许无限并发实例
)
```

### 注意事项

1. **资源消耗**：高频任务 + 慢响应可能导致大量并发连接，用户需自行评估
2. **日志量**：并发执行会产生更多日志记录
3. **数据库连接**：每个实例会使用独立的数据库会话，SQLAlchemy 连接池需足够大

### 测试策略

手动测试：创建一个间隔 1 秒、执行时间 5 秒的任务，观察是否有多个实例同时运行。

## 审查备注

- 对抗性审查已完成
- 发现：5 个总计，2 个已修复，3 个跳过
- 解决方法：自动修复
- 已修复：F1（魔法数字改为常量）、F3（已验证测试范围完整）
- 跳过（噪音/不确定）：F2, F4, F5
