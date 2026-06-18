#!/bin/bash

echo "🚀 Starting local deployment..."

# 1. 确保 Docker 在运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# 2. 停止并清理旧容器
echo "🧹 Stopping and removing old containers..."
docker compose down

# 3. 重新构建并启动
echo "🔧 Building and starting containers..."
docker compose up -d --build

# 4. 等待数据库就绪
echo "⏳ Waiting for database to be ready..."
sleep 10

# 5. 执行迁移
echo "📦 Running migrations..."
docker exec my_site_web python manage.py migrate

# 6. 检查服务是否运行
echo "✅ Checking service status..."
if curl -s http://localhost:8001/ > /dev/null; then
    echo "✅ Deployment successful! Application running at http://localhost:8001/"
else
    echo "❌ Deployment failed. Please check logs."
    docker compose logs web
fi