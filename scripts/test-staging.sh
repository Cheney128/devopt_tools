#!/bin/bash
# switch_manage 测试环境测试脚本
# 用法：./test-staging.sh

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  switch_manage 测试环境测试"
echo "========================================"
echo ""

# 切换到测试环境
echo "1. 切换到测试环境..."
"$SCRIPT_DIR/switch-scene.sh" test
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
    
    # 检查 IP 定位数据
    cursor.execute("SELECT COUNT(*) FROM ip_location_current")
    ip_count = cursor.fetchone()[0]
    print(f"✅ IP 定位表：{ip_count} 条记录")
    
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败：{e}")
    exit(1)
PYEOF
echo ""

# 验证 API
echo "3. 验证 API 连接..."
API_URL="http://10.21.65.20:8080/api/v1/devices"
response=$(curl -s -w "\n%{http_code}" "$API_URL")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" == "200" ]; then
    echo "✅ API 连接成功！$API_URL"
else
    echo "⚠️  API 响应码：$http_code"
fi
echo ""

echo "========================================"
echo "  测试环境验证完成！"
echo "========================================"
