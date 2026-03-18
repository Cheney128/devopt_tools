import pymysql
conn = pymysql.connect(host="db", port=3306, user="root", password="[OylKbYLJf*Hx((4dEIf]", database="switch_manage")
cursor = conn.cursor()
cursor.execute("DESCRIBE devices")
for row in cursor.fetchall():
    print(row)
conn.close()
