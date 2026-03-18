
import pymysql
from datetime import datetime

conn = pymysql.connect(
    host="10.21.65.20", 
    port=3307, 
    user="root", 
    password="1qaz@WSX", 
    database="switch_manage"
)
cursor = conn.cursor()

print("=" * 80)
print("备份计划检查")
print("=" * 80)

cursor.execute("SELECT id, device_id, schedule_type, time, is_active, last_run_time FROM backup_schedules ORDER BY id")
schedules = cursor.fetchall()
print(f"\n备份计划数量: {len(schedules)}")
for s in schedules:
    print(f"  计划ID: {s[0]}, 设备ID: {s[1]}, 类型: {s[2]}, 时间: {s[3]}, 上次执行: {s[5]}")

print("\n" + "=" * 80)
print("备份执行日志 (最近10条)")
print("=" * 80)

cursor.execute("""
    SELECT id, device_id, trigger_type, status, error_message, execution_time, created_at 
    FROM backup_execution_logs 
    ORDER BY created_at DESC 
    LIMIT 10
""")
logs = cursor.fetchall()

print(f"\n执行日志数量: {len(logs)}")
for log in logs:
    log_id, device_id, trigger_type, status, error_msg, execution_time, created_at = log
    print(f"\n  日志ID: {log_id}")
    print(f"  设备ID: {device_id}")
    print(f"  触发类型: {trigger_type}")
    print(f"  状态: {status}")
    print(f"  错误信息: {error_msg}")
    print(f"  耗时: {execution_time}s")
    print(f"  创建时间: {created_at}")

print("\n" + "=" * 80)
print("定时备份执行记录统计")
print("=" * 80)

cursor.execute("""
    SELECT trigger_type, status, COUNT(*) as count 
    FROM backup_execution_logs 
    WHERE created_at &gt;= CURDATE()
    GROUP BY trigger_type, status
""")
stats = cursor.fetchall()

print("\n今日执行统计:")
for stat in stats:
    print(f"  触发类型: {stat[0]}, 状态: {stat[1]}, 数量: {stat[2]}")

conn.close()
print("\n检查完成!")

