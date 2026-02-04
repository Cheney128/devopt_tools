#!/bin/bash
set -e

# 容器入口脚本

echo "=========================================="
echo "Starting Unified Deployment Container"
echo "=========================================="

# 创建日志目录
mkdir -p /var/log/supervisor /var/log/nginx /unified-app/logs

# 设置权限
chown -R www-data:www-data /var/log/nginx
chown -R root:root /var/log/supervisor

# 打印环境信息（调试用，生产环境可注释）
echo "[Entrypoint] DEPLOY_MODE: ${DEPLOY_MODE:-not set}"
echo "[Entrypoint] APP_NAME: ${APP_NAME:-not set}"

# 检查数据库连接（隐藏密码）
if [ -n "$DATABASE_URL" ]; then
    masked_url=$(echo "$DATABASE_URL" | sed -E 's/:\/\/[^:]+:[^@]+@/:\/\/***:***@/')
    echo "[Entrypoint] DATABASE_URL: $masked_url"
else
    echo "[Entrypoint] WARNING: DATABASE_URL is not set!"
fi

# 初始化数据库（仅在第一次启动时执行）
echo "=========================================="
echo "Initializing Database..."
echo "=========================================="

# 等待数据库启动
echo "Waiting for database to be ready..."

# 检查是否已初始化
if [ ! -f "/unified-app/.db_initialized" ]; then
    echo "Creating database tables..."
    
    # 简单的等待和尝试
    max_retries=10
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "Waiting for database... ($retry_count/$max_retries)"
        sleep 3
        
        # 尝试运行初始化脚本
        if python3 /unified-app/scripts/init_auth_data.py; then
            echo "✓ Database initialization successful!"
            # 标记已初始化
            touch /unified-app/.db_initialized
            break
        fi
        
        retry_count=$((retry_count + 1))
    done
    
    if [ $retry_count -ge $max_retries ]; then
        echo "✗ Error: Database initialization failed!"
        echo "Starting services anyway..."
    else
        echo "✓ Database initialization completed!"
    fi
else
    echo "✓ Database already initialized, skipping..."
fi

echo "=========================================="
echo "Starting Supervisor..."
echo "=========================================="

# 执行传入的命令（默认启动supervisord）
exec "$@"
