import pymysql
conn = pymysql.connect(host="db", port=3306, user="root", password="[OylKbYLJf*Hx((4dEIf]", database="switch_manage")
cursor = conn.cursor()
cursor.execute("SELECT captcha_code FROM captcha_records ORDER BY created_at DESC LIMIT 1")
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print("NOT_FOUND")
conn.close()
