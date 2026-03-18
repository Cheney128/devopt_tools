import pymysql

conn = pymysql.connect(host="db", port=3306, user="root", password="[OylKbYLJf*Hx((4dEIf]", database="switch_manage")
cursor = conn.cursor()

migrations = [
    "ALTER TABLE devices ADD COLUMN latency INT NULL",
    "ALTER TABLE devices ADD COLUMN last_latency_check DATETIME NULL",
    "ALTER TABLE devices ADD COLUMN latency_check_enabled TINYINT(1) NOT NULL DEFAULT 1",
]

for sql in migrations:
    try:
        cursor.execute(sql)
        print(f"OK: {sql}")
    except Exception as e:
        if "Duplicate column" in str(e):
            print(f"SKIP: {sql} (already exists)")
        else:
            print(f"ERROR: {sql} - {e}")

conn.commit()
conn.close()
print("Migration completed!")
