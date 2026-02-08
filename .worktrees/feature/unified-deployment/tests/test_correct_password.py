import pymysql

print('=== 测试正确密码 ===')

# 测试 1: 使用 URL 编码的密码 (1qaz%40WSX)
print('\n测试 1: 密码 = 1qaz%40WSX (URL 编码)')
try:
    conn = pymysql.connect(
        host='192.168.80.133',
        port=3307,
        user='root',
        password='1qaz%40WSX',
        database='switch_manage',
        charset='utf8mb4',
        connect_timeout=5
    )
    print('✅ 连接成功！')
    conn.close()
except Exception as e:
    print(f'❌ 连接失败: {e}')

# 测试 2: 使用解码后的密码 (1qaz@WSX)
print('\n测试 2: 密码 = 1qaz@WSX (解码后)')
try:
    conn = pymysql.connect(
        host='192.168.80.133',
        port=3307,
        user='root',
        password='1qaz@WSX',
        database='switch_manage',
        charset='utf8mb4',
        connect_timeout=5
    )
    print('✅ 连接成功！')
    conn.close()
except Exception as e:
    print(f'