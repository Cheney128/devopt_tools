import sqlite3

conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()

cursor.execute('SELECT username, password_hash FROM users WHERE username = "admin"')
row = cursor.fetchone()

if row:
    print(f"User: {row[0]}")
    print(f"Full hash: {row[1]}")
    print(f"Hash length: {len(row[1])}")
    print()
    print("Hash breakdown:")
    parts = row[1].split('$')
    for i, part in enumerate(parts):
        print(f"  Part {i}: {part[:60]}..." if len(part) > 60 else f"  Part {i}: {part}")
else:
    print("User not found")

conn.close()
