#!/bin/bash
# 开发环境启动脚本

set -e

echo "🚀 启动开发环境..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动服务
echo "📦 启动 Docker 服务..."
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
sleep 5

# 安装后端依赖
echo "📥 安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -e ".[dev]"

# 初始化数据库
echo "🗄️  初始化数据库..."
python scripts/init-db.py

echo ""
echo "✅ 开发环境启动完成!"
echo ""
echo "可用服务:"
echo "  - 后端 API:   http://localhost:8000"
echo "  - 前端:       http://localhost:3000"
echo "  - 数据库:     localhost:5432"
echo "  - PgAdmin:    http://localhost:5050"
echo ""
echo "启动后端: cd backend && uvicorn app.main:app --reload"
echo "启动前端: cd frontend && npm run dev"
