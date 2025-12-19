---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - '_bmad-output/analysis/brainstorming-session-2025-12-18.md'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 1
  projectDocs: 0
workflowType: 'prd'
lastStep: 11
project_name: 'AutoAI'
user_name: 'Hkfires'
date: 'Thursday, December 18, 2025'
---

# Product Requirements Document - AutoAI

**Author:** Hkfires
**Date:** Thursday, December 18, 2025

## Executive Summary

AutoAI 是一个定时自动化系统，能够按照预设的时间表向指定 AI 发送消息。系统采用 Docker 容器化部署，通过 Web 管理后台进行任务配置，确保 24/7 稳定运行。

核心目标是**简单可靠**：用户配置好任务后，系统按时执行，不遗漏、不重复。

### What Makes This Special

- **可靠性优先**：执行状态锁防止重复发送，自动重试机制应对网络波动
- **简单易用**：Web 后台管理任务，无需复杂配置
- **稳定部署**：Docker 容器化，VPS 上持续运行

## Project Classification

**Technical Type:** api_backend（附带 web_app 管理界面）
**Domain:** general（通用自动化工具）
**Complexity:** low
**Project Context:** Greenfield - 新项目

## Success Criteria

### User Success

- 任务按预设时间准时执行
- 消息成功发送到指定 AI
- 无需人工干预即可持续运行

### Business Success

- 个人工具，满足自用需求
- 稳定运行，不需要日常管理和维护
- 设置好后"放着就能用"

### Technical Success

- 系统能够正常运行
- 基本的错误重试机制
- Docker 容器化便于部署和迁移

### Measurable Outcomes

- 任务按时执行率：正常工作即可
- 系统稳定性：无需频繁重启或干预

## Product Scope

### MVP - Minimum Viable Product

- 定时触发功能（间隔/固定时间两种模式）
- 向 AI API 发送消息
- 基本的任务配置
- Docker 容器化部署

### Growth Features (Post-MVP)

- Web 管理后台（任务增删改查）
- 执行状态锁（防重复发送）
- 自动重试机制
- 执行日志记录

### Vision (Future)

- 历史日志查看界面
- 多 AI 目标支持
- 消息模板管理

## User Journeys

### Journey 1: Hkfires - 自动化流程触发

Hkfires 需要定期触发某个自动化流程，但不想每次都手动操作。他决定搭建一个定时系统来自动完成这项工作。

**第一天：初始设置**
Hkfires 在 VPS 上部署 AutoAI 的 Docker 容器。他配置好 AI 的 API 地址和认证信息，设置定时规则（比如每天早上 9 点），填入要发送的消息内容。测试一次，确认消息成功发送，流程被正确触发。

**日常运行：无感知**
系统在后台默默运行。每天按时发送消息，触发自动化流程。Hkfires 不需要做任何事情，系统自己处理一切。偶尔网络波动导致发送失败时，系统自动重试，无需人工干预。

**偶尔检查：确认状态**
每隔一段时间，Hkfires 登录查看一下执行日志，确认系统正常运行。看到任务都按时执行、消息都成功发送，他满意地关掉页面，继续做其他事情。

**成功结局**
几个月过去了，系统一直稳定运行。Hkfires 几乎忘了它的存在——这正是他想要的结果。

### Journey Requirements Summary

此旅程揭示的功能需求：

- **配置功能**：AI API 地址、认证信息、定时规则、消息内容
- **执行功能**：按时触发、消息发送、自动重试
- **监控功能**：执行日志、状态查看
- **部署功能**：Docker 容器化、VPS 部署

## API Backend 特定需求

### 项目类型概述

AutoAI 是一个后端服务，核心功能是定时调用 OpenAI API 发送消息。附带 Web 管理后台用于任务配置和状态查看。

### 技术架构考虑

**API 调用目标：**
- OpenAI API（Chat Completions 等端点）
- 使用 API Key 认证
- JSON 数据格式

**系统认证：**
- Web 管理后台需要登录认证
- 保护任务配置和 API 密钥安全

### 端点设计（内部管理 API）

| 端点 | 方法 | 用途 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/tasks | GET/POST | 获取/创建任务 |
| /api/tasks/:id | PUT/DELETE | 更新/删除任务 |
| /api/tasks/:id/logs | GET | 查看执行日志 |

### 数据模型

**任务配置：**
- AI API 地址和密钥
- 定时规则（间隔模式：每X分钟/小时；固定时间模式：每天HH:MM）
- 消息内容
- 启用/禁用状态

**执行日志：**
- 执行时间
- 成功/失败状态
- 响应摘要

### 实现考虑

- **简化设计**：个人工具，不需要速率限制、版本控制、SDK
- **安全存储**：API 密钥需加密存储
- **错误处理**：基本重试机制应对网络波动

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP 方法：** Problem-Solving MVP
**目标：** 用最小功能集解决核心问题——定时向 AI 发送消息
**资源需求：** 单人开发，个人项目

### MVP Feature Set (Phase 1)

**核心用户旅程支持：**
- 初始设置：配置 AI API 和定时规则
- 日常运行：自动执行，无需干预

**必备功能：**
- 定时触发（间隔/固定时间模式）
- OpenAI API 调用
- 基本任务配置（配置文件或环境变量）
- Docker 容器化部署
- 基本错误重试

### Post-MVP Features

**Phase 2（增强）：**
- Web 管理后台（任务 CRUD）
- 用户登录认证
- 执行状态锁（防重复发送）
- 执行日志记录

**Phase 3（扩展）：**
- 历史日志查看界面
- 多 AI 目标支持
- 消息模板管理

### Risk Mitigation Strategy

**技术风险：** 低 - 使用成熟技术栈（Docker + Cron + HTTP 请求）
**市场风险：** 无 - 个人工具，无需市场验证
**资源风险：** 低 - 单人可完成，范围可控

## Functional Requirements

### 任务配置

- FR1: 用户可以配置 OpenAI API 端点地址
- FR2: 用户可以配置 API 认证密钥
- FR3: 用户可以设置定时规则（支持两种模式：间隔模式如"每2小时"，固定时间模式如"每天09:00"）
- FR4: 用户可以定义要发送的消息内容
- FR5: 用户可以启用或禁用任务

### 任务执行

- FR6: 系统按照定时规则自动触发任务执行
- FR7: 系统向配置的 OpenAI API 发送消息
- FR8: 系统在发送失败时自动重试
- FR9: 系统记录每次执行的结果（成功/失败）

### 用户认证（Phase 2）

- FR10: 用户可以通过登录认证访问管理后台
- FR11: 系统保护 API 密钥和任务配置的安全

### 监控与日志（Phase 2）

- FR12: 用户可以查看任务执行日志
- FR13: 用户可以查看任务执行状态

### 部署

- FR14: 系统支持 Docker 容器化部署
- FR15: 系统支持通过配置文件或环境变量进行初始配置

## Non-Functional Requirements

### 安全

- NFR1: API 密钥必须加密存储，不得明文保存
- NFR2: 管理后台登录凭证必须加密存储
- NFR3: 敏感信息不得出现在日志中

### 可靠性

- NFR4: 系统支持基本错误重试机制（网络失败时自动重试）
- NFR5: 系统能够在 VPS 重启后自动恢复运行（Docker 自动重启）

### 集成

- NFR6: 系统支持 OpenAI 标准 API 格式（Chat Completions）
- NFR7: 系统使用 JSON 作为数据交换格式
