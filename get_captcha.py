import pymysql
conn = pymysql.connect(host="10.21.65.20", port=3307, user="root", password="1qaz@WSX", database="switch_manage")
cursor = conn.cursor()
cursor.execute("SELECT captcha_code FROM captcha_records ORDER BY created_at DESC LIMIT 1")
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print("NOT_FOUND")
conn.close()
