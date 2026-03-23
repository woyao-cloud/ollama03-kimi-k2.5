# FastAPI 后端实施计划

## 项目概述

基于 BACKEND_ARCHITECTURE.md、API_SPECIFICATION.md、DATABASE_SCHEMA.md 和 AUTHENTICATION_FLOW.md 创建全栈用户管理系统的 FastAPI 后端实现计划。

---

## 一、任务分解（按阶段）

### 阶段 1: 项目初始化与配置
**目标**: 建立基础项目结构和依赖配置

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 1.1 | 创建项目目录结构 | P0 | 30分钟 |
| 1.2 | 配置 pyproject.toml 依赖 | P0 | 1小时 |
| 1.3 | 配置环境变量和设置 | P0 | 1小时 |
| 1.4 | 初始化 Alembic 迁移工具 | P0 | 30分钟 |
| 1.5 | 配置日志和错误处理 | P1 | 1小时 |

### 阶段 2: 数据库模型与迁移
**目标**: 实现所有数据库模型和初始迁移

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 2.1 | 创建基础模型基类 | P0 | 1小时 |
| 2.2 | 实现 User 模型 | P0 | 1.5小时 |
| 2.3 | 实现 Role 模型 | P0 | 1小时 |
| 2.4 | 实现 Permission 模型 | P0 | 1小时 |
| 2.5 | 实现关联表模型 (user_roles, role_permissions) | P0 | 1小时 |
| 2.6 | 实现审计表模型 (audit_logs, user_sessions, login_attempts) | P1 | 2小时 |
| 2.7 | 创建初始数据库迁移脚本 | P0 | 1小时 |
| 2.8 | 创建数据库连接和会话管理 | P0 | 1.5小时 |

### 阶段 3: Pydantic 模式定义
**目标**: 定义所有请求/响应数据验证模式

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 3.1 | 创建基础响应模式 | P0 | 1小时 |
| 3.2 | 定义用户相关模式 (UserCreate, UserUpdate, UserResponse) | P0 | 2小时 |
| 3.3 | 定义认证相关模式 (LoginRequest, TokenResponse) | P0 | 1.5小时 |
| 3.4 | 定义角色相关模式 (RoleCreate, RoleUpdate, RoleResponse) | P0 | 1.5小时 |
| 3.5 | 定义权限相关模式 (PermissionResponse) | P0 | 1小时 |
| 3.6 | 定义分页和查询参数模式 | P1 | 1小时 |

### 阶段 4: 核心服务实现
**目标**: 实现业务逻辑层

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 4.1 | 实现密码哈希服务 (Argon2id) | P0 | 1.5小时 |
| 4.2 | 实现 JWT 令牌服务 | P0 | 2小时 |
| 4.3 | 实现用户服务 (CRUD + 业务逻辑) | P0 | 3小时 |
| 4.4 | 实现认证服务 (登录/登出/刷新) | P0 | 3小时 |
| 4.5 | 实现角色服务 | P0 | 2小时 |
| 4.6 | 实现权限服务 | P0 | 2小时 |
| 4.7 | 实现审计日志服务 | P1 | 2小时 |

### 阶段 5: 认证与权限系统
**目标**: 实现 JWT + OAuth2 + RBAC

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 5.1 | 实现 OAuth2 密码流依赖 | P0 | 2小时 |
| 5.2 | 实现 JWT 验证依赖 | P0 | 2小时 |
| 5.3 | 实现权限检查装饰器/依赖 | P0 | 2.5小时 |
| 5.4 | 实现角色检查中间件 | P0 | 2小时 |
| 5.5 | 实现账户锁定机制 | P1 | 2小时 |
| 5.6 | 实现速率限制中间件 | P1 | 2小时 |

### 阶段 6: API 路由实现
**目标**: 实现 API_SPECIFICATION.md 中定义的所有端点

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 6.1 | 实现认证路由 (/auth/login, /auth/register, /auth/refresh, /auth/me) | P0 | 3小时 |
| 6.2 | 实现用户路由 (/users, /users/{id}) | P0 | 3小时 |
| 6.3 | 实现角色路由 (/roles) | P0 | 2小时 |
| 6.4 | 实现权限路由 (/permissions) | P0 | 1.5小时 |
| 6.5 | 实现健康检查路由 | P1 | 30分钟 |

### 阶段 7: 测试实现
**目标**: 实现单元测试和集成测试，覆盖率 > 85%

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 7.1 | 配置测试环境和 fixtures | P0 | 2小时 |
| 7.2 | 编写模型单元测试 | P0 | 2小时 |
| 7.3 | 编写服务层单元测试 | P0 | 4小时 |
| 7.4 | 编写认证系统单元测试 | P0 | 3小时 |
| 7.5 | 编写 API 集成测试 | P0 | 4小时 |
| 7.6 | 编写权限系统测试 | P0 | 2小时 |
| 7.7 | 生成测试覆盖率报告 | P0 | 1小时 |

### 阶段 8: 文档与优化
**目标**: 完善文档和性能优化

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 8.1 | 配置 OpenAPI 文档 | P1 | 1小时 |
| 8.2 | 编写 API 使用文档 | P1 | 2小时 |
| 8.3 | 性能优化 (数据库索引、查询优化) | P1 | 3小时 |
| 8.4 | 代码审查和重构 | P1 | 2小时 |

---

## 二、文件清单

### 2.1 项目配置文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/pyproject.toml` | Python 依赖配置 | 1.2 |
| `backend/.env.example` | 环境变量模板 | 1.3 |
| `backend/app/config.py` | 应用配置类 | 1.3 |
| `backend/alembic.ini` | Alembic 配置文件 | 1.4 |
| `backend/alembic/env.py` | Alembic 环境脚本 | 1.4 |

### 2.2 数据库相关文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/infrastructure/database/base.py` | SQLAlchemy 基类 | 2.1 |
| `backend/app/infrastructure/database/session.py` | 数据库会话管理 | 2.8 |
| `backend/app/domain/models/user.py` | User 模型 | 2.2 |
| `backend/app/domain/models/role.py` | Role 模型 | 2.3 |
| `backend/app/domain/models/permission.py` | Permission 模型 | 2.4 |
| `backend/app/domain/models/associations.py` | 关联表模型 | 2.5 |
| `backend/app/domain/models/audit.py` | 审计表模型 | 2.6 |
| `backend/alembic/versions/0001_initial.py` | 初始迁移脚本 | 2.7 |

### 2.3 Pydantic 模式文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/schemas/base.py` | 基础模式类 | 3.1 |
| `backend/app/schemas/user.py` | 用户相关模式 | 3.2 |
| `backend/app/schemas/auth.py` | 认证相关模式 | 3.3 |
| `backend/app/schemas/role.py` | 角色相关模式 | 3.4 |
| `backend/app/schemas/permission.py` | 权限相关模式 | 3.5 |
| `backend/app/schemas/common.py` | 通用模式 (分页等) | 3.6 |

### 2.4 核心服务文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/core/security.py` | 密码哈希和加密 | 4.1 |
| `backend/app/core/jwt.py` | JWT 令牌处理 | 4.2 |
| `backend/app/application/services/user_service.py` | 用户服务 | 4.3 |
| `backend/app/application/services/auth_service.py` | 认证服务 | 4.4 |
| `backend/app/application/services/role_service.py` | 角色服务 | 4.5 |
| `backend/app/application/services/permission_service.py` | 权限服务 | 4.6 |
| `backend/app/application/services/audit_service.py` | 审计服务 | 4.7 |

### 2.5 认证与权限文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/core/auth.py` | OAuth2 和 JWT 验证 | 5.1, 5.2 |
| `backend/app/core/permissions.py` | 权限检查逻辑 | 5.3 |
| `backend/app/core/rbac.py` | RBAC 实现 | 5.4 |
| `backend/app/core/rate_limit.py` | 速率限制 | 5.6 |
| `backend/app/core/lockout.py` | 账户锁定 | 5.5 |

### 2.6 API 路由文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/api/v1/router.py` | API 路由聚合 | 6.x |
| `backend/app/api/v1/endpoints/auth.py` | 认证端点 | 6.1 |
| `backend/app/api/v1/endpoints/users.py` | 用户端点 | 6.2 |
| `backend/app/api/v1/endpoints/roles.py` | 角色端点 | 6.3 |
| `backend/app/api/v1/endpoints/permissions.py` | 权限端点 | 6.4 |
| `backend/app/api/v1/endpoints/health.py` | 健康检查 | 6.5 |
| `backend/app/api/deps.py` | 依赖注入 | 6.x |

### 2.7 应用入口文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/app/main.py` | FastAPI 应用入口 | 1.1 |
| `backend/app/__init__.py` | 包初始化 | 1.1 |

### 2.8 测试文件

| 文件路径 | 描述 | 所属阶段 |
|----------|------|----------|
| `backend/tests/conftest.py` | pytest 配置和 fixtures | 7.1 |
| `backend/tests/unit/test_models.py` | 模型单元测试 | 7.2 |
| `backend/tests/unit/test_services.py` | 服务层单元测试 | 7.3 |
| `backend/tests/unit/test_auth.py` | 认证系统单元测试 | 7.4 |
| `backend/tests/integration/test_api.py` | API 集成测试 | 7.5 |
| `backend/tests/integration/test_permissions.py` | 权限系统测试 | 7.6 |
| `backend/tests/__init__.py` | 测试包初始化 | 7.1 |

---

## 三、依赖关系

### 3.1 任务依赖图

```
阶段 1: 项目初始化
    |
    v
阶段 2: 数据库模型  <-- 依赖阶段 1 (配置完成)
    |
    v
阶段 3: Pydantic 模式 <-- 依赖阶段 2 (模型定义)
    |
    v
阶段 4: 核心服务  <-- 依赖阶段 2, 3 (模型 + 模式)
    |
    v
阶段 5: 认证权限  <-- 依赖阶段 4 (服务层)
    |
    v
阶段 6: API 路由  <-- 依赖阶段 3, 4, 5 (模式 + 服务 + 认证)
    |
    v
阶段 7: 测试     <-- 依赖阶段 2-6 (所有实现)
    |
    v
阶段 8: 文档优化 <-- 依赖阶段 6, 7 (API + 测试)
```

### 3.2 文件依赖关系

```
config.py
    |
    +--> database/session.py
    |       |
    |       +--> domain/models/*.py
    |               |
    |               +--> schemas/*.py
    |                       |
    |                       +--> application/services/*.py
    |                               |
    |                               +--> core/auth.py, permissions.py
    |                                       |
    |                                       +--> api/v1/endpoints/*.py
    |                                               |
    |                                               +--> api/v1/router.py
    |                                                       |
    +------------------------------------------------------+--> main.py
```

### 3.3 关键依赖说明

| 依赖项 | 被依赖项 | 说明 |
|--------|----------|------|
| 数据库模型 | 所有服务层 | 服务层操作数据库实体 |
| Pydantic 模式 | API 路由、服务层 | 数据验证和序列化 |
| JWT 服务 | 认证路由、权限检查 | 令牌生成和验证 |
| 权限服务 | 受保护的路由 | 访问控制检查 |
| 用户服务 | 认证服务 | 用户验证和查询 |

---

## 四、风险点

### 4.1 技术风险

| 风险ID | 风险描述 | 影响程度 | 缓解措施 |
|--------|----------|----------|----------|
| R1 | SQLAlchemy 2.0 新语法学习曲线 | 中 | 预留额外学习时间，参考官方文档 |
| R2 | JWT 刷新令牌安全存储 | 高 | 使用 HttpOnly Cookie，实现令牌黑名单 |
| R3 | 并发下的账户锁定竞争条件 | 中 | 使用数据库行级锁或 Redis 原子操作 |
| R4 | 速率限制分布式部署 | 中 | 使用 Redis 作为共享存储 |
| R5 | 测试覆盖率达标困难 | 中 | 采用 TDD，定期生成覆盖率报告 |

### 4.2 进度风险

| 风险ID | 风险描述 | 影响程度 | 缓解措施 |
|--------|----------|----------|----------|
| R6 | 权限系统复杂度超预期 | 高 | 先实现基础 RBAC，后续迭代优化 |
| R7 | 数据库迁移问题 | 中 | 充分测试迁移脚本，保留回滚方案 |
| R8 | 第三方库版本冲突 | 低 | 锁定依赖版本，使用虚拟环境 |

### 4.3 安全风险

| 风险ID | 风险描述 | 影响程度 | 缓解措施 |
|--------|----------|----------|----------|
| R9 | 密码哈希算法选择 | 高 | 使用 Argon2id，符合 OWASP 建议 |
| R10 | JWT 密钥管理 | 高 | 环境变量存储，生产环境定期轮换 |
| R11 | SQL 注入风险 | 中 | 使用 SQLAlchemy ORM，避免原始 SQL |
| R12 | 敏感数据泄露 | 高 | Pydantic 模式排除敏感字段，日志脱敏 |

---

## 五、测试策略

### 5.1 测试分层

```
                    ▲
                   / \
                  / E2E \        10% - 关键用户流程
                 /─────────\
                /  Integration \  20% - API + 数据库
               /─────────────────\
              /       Unit         \ 70% - 函数、类、方法
             /─────────────────────────\
```

### 5.2 单元测试策略

| 测试对象 | 测试内容 | 覆盖率目标 |
|----------|----------|------------|
| 领域模型 | 属性验证、关系、约束 | 90% |
| 服务层 | 业务逻辑、异常处理 | 90% |
| 工具函数 | 边界条件、错误输入 | 95% |
| 安全模块 | 哈希、JWT 生成验证 | 100% |

### 5.3 集成测试策略

| 测试对象 | 测试内容 | 测试数据 |
|----------|----------|----------|
| API 端点 | 请求/响应、状态码、错误处理 | 内存 SQLite |
| 数据库 | 迁移、CRUD、事务 | 测试数据库 |
| 认证流程 | 登录/登出/刷新完整流程 | 模拟用户数据 |
| 权限检查 | 不同角色访问控制 | 预定义角色权限 |

### 5.4 测试环境配置

```python
# pytest 配置策略
# conftest.py 关键 fixtures:

- app: FastAPI 测试应用实例
- client: TestClient 客户端
- db_session: 数据库会话 (每个测试隔离)
- test_user: 预创建测试用户
- auth_headers: 认证请求头
- mock_services: 服务层 Mock
```

### 5.5 测试数据管理

| 数据类型 | 管理方式 | 说明 |
|----------|----------|------|
| 静态测试数据 | pytest fixtures | 基础用户、角色数据 |
| 动态测试数据 | factory-boy | 批量生成测试实体 |
| 数据库状态 | 事务回滚 | 每个测试后清理 |

### 5.6 覆盖率检查点

| 阶段 | 检查项 | 目标覆盖率 |
|------|--------|------------|
| 阶段 4 完成 | 服务层单元测试 | 70% |
| 阶段 5 完成 | 认证权限测试 | 80% |
| 阶段 6 完成 | API 集成测试 | 85% |
| 阶段 7 完成 | 整体覆盖率 | >= 85% |

### 5.7 测试执行命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term-missing

# 运行特定模块测试
pytest tests/unit/test_auth.py -v
```

---

## 六、技术选型与依赖

### 6.1 核心依赖 (pyproject.toml)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = {extras = ["email"], version = "^2.5.0"}
pydantic-settings = "^2.1.0"
sqlalchemy = {extras = ["asyncpg"], version = "^2.0.23"}
alembic = "^1.12.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["argon2"], version = "^1.7.4"}
python-multipart = "^0.0.6"
httpx = "^0.25.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
factory-boy = "^3.3.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.7.0"
```

### 6.2 可选依赖

| 依赖 | 用途 | 阶段 |
|------|------|------|
| redis | 速率限制、缓存 | 5.6 |
| celery | 异步任务 (邮件等) | 未来 |
| sentry-sdk | 错误监控 | 8.x |

---

## 七、实施检查清单

### 7.1 代码质量检查

- [ ] 所有函数有类型注解
- [ ] 所有公共方法有 docstring
- [ ] 代码符合 PEP 8 (Black + Ruff)
- [ ] 无硬编码敏感信息
- [ ] 错误处理完善

### 7.2 安全检查

- [ ] 密码使用 Argon2id 哈希
- [ ] JWT 密钥从环境变量读取
- [ ] 所有端点有适当权限控制
- [ ] 输入数据经过验证
- [ ] 敏感字段不在响应中暴露

### 7.3 性能检查

- [ ] 数据库查询使用 join 避免 N+1
- [ ] 适当的数据库索引
- [ ] 响应时间 P95 < 200ms

### 7.4 测试检查

- [ ] 单元测试覆盖率 >= 85%
- [ ] 所有 API 端点有集成测试
- [ ] 认证流程完整测试
- [ ] 权限检查完整测试

---

## 八、总结

本实施计划涵盖从项目初始化到测试完成的完整 FastAPI 后端开发流程，共 8 个阶段，预计总工时约 70-80 小时。

**关键成功因素**:
1. 严格按照分层架构实现
2. 测试驱动开发，确保覆盖率达标
3. 安全优先，特别是认证和权限部分
4. 文档同步更新

**里程碑**:
- M1 (阶段 1-2): 基础架构和数据库完成
- M2 (阶段 3-5): 核心业务逻辑完成
- M3 (阶段 6): API 接口全部可用
- M4 (阶段 7-8): 测试通过，文档完善
