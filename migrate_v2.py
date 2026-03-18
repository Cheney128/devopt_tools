import pymysql

conn = pymysql.connect(host="db", port=3306, user="root", password="[OylKbYLJf*Hx((4dEIf]", database="switch_manage")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE devices ADD COLUMN latency INT NULL")
    conn.commit()
    print("Added latency column")
except Exception as e:
    print(f"latency: {e}")

try:
    cursor.execute("ALTER TABLE devices ADD COLUMN last_latency_check DATETIME NULL")
    conn.commit()
    print("Added last_latency_check column")
except Exception as e:
    print(f"last_latency_check: {e}")

try:
    cursor.execute("ALTER TABLE devices ADD COLUMN latency_check_enabled TINYINT(1) NOT NULL DEFAULT 1")
    conn.commit()
    print("Added latency_check_enabled column")
except Exception as e:
    print(f"latency_check_enabled: {e}")

conn.close()
print("Done!")
