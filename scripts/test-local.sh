#!/bin/bash
# switch_manage 本地开发环境测试脚本
# 用法：./test-local.sh

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  switch_manage 本地开发环境测试"
echo "========================================"
echo ""

# 切换到本地开发环境
echo "1. 切换到本地开发环境..."
"$SCRIPT_DIR/switch-scene.sh" local
echo ""

# 测试数据库连接
echo "2. 测试数据库连接..."
python3 << 'PYEOF'
import pymysql
import os

config = {
    'host': os.getenv('DB_HOST', '10.21.65.20'),
    'port': int(os.getenv('DB_PORT', 3307)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1qaz@WSX'),
    'database': os.getenv('DB_NAME', 'switch_manage')
}

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM devices")
    count = cursor.fetchone()[0]
    print(f"✅ 数据库连接成功！设备表：{count} 条记录")
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败：{e}")
    exit(1)
PYEOF
echo ""

# 启动开发服务器
echo "3. 启动开发服务器..."
echo "   后端：http://localhost:8000"
echo "   前端：http://localhost:5173"
echo ""
echo "提示：按 Ctrl+C 停止服务器"
echo ""

cd "$PROJECT_DIR"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
