# 数据库设计文档

## 核心表结构

### users - 用户表
```sql
id UUID PRIMARY KEY
username VARCHAR(50) UNIQUE NOT NULL
email VARCHAR(255) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
first_name VARCHAR(100)
last_name VARCHAR(100)
is_active BOOLEAN DEFAULT true
is_verified BOOLEAN DEFAULT false
last_login_at TIMESTAMP
created_at TIMESTAMP DEFAULT NOW()
```

### roles - 角色表
```sql
id UUID PRIMARY KEY
name VARCHAR(50) UNIQUE NOT NULL
description TEXT
is_default BOOLEAN DEFAULT false
```

### permissions - 权限表
```sql
id UUID PRIMARY KEY
name VARCHAR(100) UNIQUE NOT NULL
resource VARCHAR(50) NOT NULL
action VARCHAR(50) NOT NULL
```

### 关联表
- **user_roles**: user_id + role_id
- **role_permissions**: role_id + permission_id

### 审计表
- **audit_logs**: 记录所有操作变更
- **user_sessions**: 管理用户会话
- **login_attempts**: 登录安全审计

## 迁移规范

- 使用 Alembic 管理迁移
- 命名格式: `YYYYMMDD_HHMMSS_description.py`
- 每个迁移必须包含 upgrade/downgrade
