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

echo "=========================================="
echo "Starting Supervisor..."
echo "=========================================="

# 执行传入的命令（默认启动supervisord）
exec "$@"
