# 全栈用户管理系统 - Claude Code 项目配置

## 项目概述

全栈用户管理系统，采用 FastAPI 后端和 Next.js 前端，提供用户注册、登录、权限管理、角色分配等功能。

## 技术栈

### 后端
- FastAPI + Python 3.11
- SQLAlchemy 2.0 + Alembic
- PostgreSQL (生产) / SQLite (开发)
- JWT + OAuth2 认证

### 前端
- Next.js 14 (App Router)
- TypeScript 5+
- shadcn/ui + Tailwind CSS
- Zustand 状态管理

### 基础设施
- Docker + Docker Compose
- GitHub Actions CI/CD

## 开发原则

1. 类型安全: TypeScript + Python 类型提示
2. 测试驱动: 覆盖率 > 85%
3. 分层架构: 路由 → 服务 → 仓储 → 模型
4. 安全第一: 最小权限、输入验证、防御性编程

## 项目结构

```
fastapi-nextjs-chain03/
├── backend/          # FastAPI 后端
├── frontend/         # Next.js 前端
├── docs/            # 文档
└── scripts/         # 脚本
```

## 关键文档

- AGENTS.md - 多代理协作配置
- DATABASE_SCHEMA.md - 数据库设计
- API_SPECIFICATION.md - API 接口规范
- AUTHENTICATION_FLOW.md - 认证流程
- BACKEND_ARCHITECTURE.md - 后端架构
- FRONTEND_ARCHITECTURE.md - 前端架构
- TESTING_STRATEGY.md - 测试策略
- DEPLOYMENT_GUIDE.md - 部署指南
- DEVELOPMENT_WORKFLOW.md - 开发流程

## 质量指标

- 后端测试覆盖率 ≥ 85%
- 前端测试覆盖率 ≥ 80%
- API 响应时间 P95 < 200ms
