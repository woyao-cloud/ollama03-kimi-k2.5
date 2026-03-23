# 后端架构设计

## 技术栈

- FastAPI + Python 3.11
- SQLAlchemy 2.0 + Alembic
- PostgreSQL / SQLite
- JWT + OAuth2
- Redis (缓存)

## 项目结构

```
backend/
├── app/
│   ├── main.py           # 应用入口
│   ├── config.py         # 配置
│   ├── api/v1/           # API 路由
│   ├── core/             # 安全、认证、权限
│   ├── domain/           # 领域模型
│   ├── application/      # 应用服务
│   ├── infrastructure/   # 数据库、缓存、邮件
│   └── schemas/          # Pydantic 模式
├── alembic/              # 数据库迁移
├── tests/                # 测试
└── pyproject.toml        # 依赖配置
```

## 分层架构

1. **API 层**: HTTP 请求处理
2. **应用层**: 业务逻辑协调
3. **领域层**: 核心业务规则
4. **基础设施层**: 外部依赖

## 安全设计

- JWT 认证 (访问令牌 + 刷新令牌)
- RBAC 权限控制
- 速率限制
- SQL 注入防护
- XSS 防护

## 性能优化

- 数据库连接池
- Redis 缓存
- 异步处理
- 查询优化
