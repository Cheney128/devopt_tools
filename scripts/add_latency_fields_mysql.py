"""
MySQL数据库迁移脚本 - 添加延迟检测字段
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("DATABASE_URL 环境变量未设置")
        return
    
    # 解析数据库连接信息
    # mysql+pymysql://root:password@host:port/database
    try:
        url_part = database_url.replace('mysql+pymysql://', '')
        auth, host_db = url_part.split('@')
        username, password = auth.split(':')
        
        if ':' in host_db.split('/')[0]:
            host_port, database = host_db.split('/')
            host, port = host_port.split(':')
            port = int(port)
        else:
            host, database = host_db.split('/')
            port = 3306
        
        # URL解码密码
        from urllib.parse import unquote
        password = unquote(password)
        
        print(f"连接到MySQL服务器: {host}:{port}/{database}")
        
        conn = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("SHOW COLUMNS FROM devices LIKE 'latency'")
        latency_exists = cursor.fetchone()
        
        cursor.execute("SHOW COLUMNS FROM devices LIKE 'last_latency_check'")
        last_check_exists = cursor.fetchone()
        
        cursor.execute("SHOW COLUMNS FROM devices LIKE 'latency_check_enabled'")
        enabled_exists = cursor.fetchone()
        
        # 添加 latency 字段
        if not latency_exists:
            cursor.execute("ALTER TABLE devices ADD COLUMN latency INT NULL COMMENT '设备延迟(ms)，999表示连接失败' AFTER status")
            print("已添加 latency 字段")
        else:
            print("latency 字段已存在")
        
        # 添加 last_latency_check 字段
        if not last_check_exists:
            cursor.execute("ALTER TABLE devices ADD COLUMN last_latency_check DATETIME NULL COMMENT '上次延迟检测时间' AFTER latency")
            print("已添加 last_latency_check 字段")
        else:
            print("last_latency_check 字段已存在")
        
        # 添加 latency_check_enabled 字段
        if not enabled_exists:
            cursor.execute("ALTER TABLE devices ADD COLUMN latency_check_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用延迟检测' AFTER last_latency_check")
            print("已添加 latency_check_enabled 字段")
        else:
            print("latency_check_enabled 字段已存在")
        
        # 添加索引
        try:
            cursor.execute("CREATE INDEX idx_devices_latency ON devices(latency)")
            print("已添加 latency 索引")
        except Exception as e:
            if 'Duplicate key name' in str(e):
                print("latency 索引已存在")
            else:
                raise
        
        try:
            cursor.execute("CREATE INDEX idx_devices_last_latency_check ON devices(last_latency_check)")
            print("已添加 last_latency_check 索引")
        except Exception as e:
            if 'Duplicate key name' in str(e):
                print("last_latency_check 索引已存在")
            else:
                raise
        
        try:
            cursor.execute("CREATE INDEX idx_devices_latency_check_enabled ON devices(latency_check_enabled)")
            print("已添加 latency_check_enabled 索引")
        except Exception as e:
            if 'Duplicate key name' in str(e):
                print("latency_check_enabled 索引已存在")
            else:
                raise
        
        conn.commit()
        print("MySQL数据库迁移完成!")
        
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_database()
