"""
数据库迁移脚本 - 添加延迟检测字段
"""
import sqlite3
import os

def migrate_database():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'switch_manage.db')
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加 latency 字段
        if 'latency' not in columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN latency INTEGER")
            print("已添加 latency 字段")
        else:
            print("latency 字段已存在")
        
        # 添加 last_latency_check 字段
        if 'last_latency_check' not in columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN last_latency_check DATETIME")
            print("已添加 last_latency_check 字段")
        else:
            print("last_latency_check 字段已存在")
        
        # 添加 latency_check_enabled 字段
        if 'latency_check_enabled' not in columns:
            cursor.execute("ALTER TABLE devices ADD COLUMN latency_check_enabled BOOLEAN DEFAULT 1")
            print("已添加 latency_check_enabled 字段")
        else:
            print("latency_check_enabled 字段已存在")
        
        conn.commit()
        print("数据库迁移完成!")
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
