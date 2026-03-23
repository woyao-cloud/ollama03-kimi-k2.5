# 部署指南

## 环境配置

| 环境 | 用途 | 访问 |
|------|------|------|
| 开发 | 本地开发 | 本地网络 |
| 测试 | CI/CD 测试 | 内部网络 |
| 预发布 | 生产验证 | 受限访问 |
| 生产 | 正式运行 | 公共访问 |

## 容器化部署

### 开发环境
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 生产环境
- 后端: 3 副本, 512MB 内存限制
- 前端: 3 副本, 256MB 内存限制
- PostgreSQL: 主从架构
- Redis: 集群模式

## CI/CD 流程

1. 代码提交触发构建
2. 运行测试套件
3. 构建 Docker 镜像
4. 部署到 Kubernetes
5. 运行冒烟测试

## 监控告警

- Prometheus + Grafana
- 日志聚合: ELK Stack
- 错误追踪: Sentry
