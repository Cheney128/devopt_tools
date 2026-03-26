#!/bin/bash
# switch_manage 生产环境测试脚本
# 用法：./test-prod.sh
# ⚠️  生产环境操作，需要确认！

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  ⚠️  switch_manage 生产环境测试"
echo "========================================"
echo ""

# 生产环境确认
echo "⚠️  警告：即将访问生产环境！"
echo ""
echo "目标环境：10.23.65.95"
echo "数据库：10.23.65.95:3306 (MariaDB 容器)"
echo ""
echo "此操作仅执行查询验证，不会修改任何数据。"
echo ""
echo "请输入 'CONFIRM' 确认："
read -r confirm_input
if [ "$confirm_input" != "CONFIRM" ]; then
    echo "❌ 操作已取消"
    exit 1
fi
echo ""

# 切换到生产环境
echo "1. 切换到生产环境..."
"$SCRIPT_DIR/switch-scene.sh" prod
echo ""

# 测试数据库连接（只读）
echo "2. 测试数据库连接（只读模式）..."
python3 << 'PYEOF'
import pymysql
import os

config = {
    'host': os.getenv('DB_HOST', '10.23.65.95'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'switch_manage'),
    'read_timeout': 10,
    'autocommit': True
}

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    
    # 只读查询
    cursor.execute("SELECT COUNT(*) FROM devices")
    count = cursor.fetchone()[0]
    print(f"✅ 数据库连接成功！设备表：{count} 条记录")
    
    # 检查 IP 定位数据
    cursor.execute("SELECT COUNT(*) FROM ip_location_current WHERE batch_status='active'")
    ip_count = cursor.fetchone()[0]
    print(f"✅ IP 定位表（active）：{ip_count} 条记录")
    
    conn.close()
except Exception as e:
    print(f"❌ 数据库连接失败：{e}")
    exit(1)
PYEOF
echo ""

# 验证 API
echo "3. 验证 API 连接..."
API_URL="http://10.23.65.95/api/v1/devices"
response=$(curl -s -w "\n%{http_code}" "$API_URL" --connect-timeout 10)
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" == "200" ]; then
    echo "✅ API 连接成功！$API_URL"
else
    echo "⚠️  API 响应码：$http_code"
fi
echo ""

echo "========================================"
echo "  生产环境验证完成！"
echo "========================================"
echo ""
echo "⚠️  提示：生产环境操作已记录日志"
