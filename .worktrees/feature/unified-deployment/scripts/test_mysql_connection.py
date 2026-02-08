"""
MySQL 连接测试脚本
测试数据库连接是否正常
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import pymysql
from urllib.parse import urlparse
from app.config import settings


def test_mysql_connection():
    """
    测试 MySQL 连接
    """
    print("=" * 60)
    print("MySQL 连接测试")
    print("=" * 60)

    # 解析数据库 URL
    db_url = urlparse(settings.DATABASE_URL)
    print(f"\n数据库配置:")
    print(f"  主机: {db_url.hostname}")
    print(f"  端口: {db_url.port}")
    print(f"  数据库名: {db_url.path[1:]}")
    print(f"  用户名: {db_url.username}")
    print(f"  密码: {'*' * len(db_url.password)}")

    try:
        # 解析密码（URL 解码）
        from urllib.parse import unquote
        password = unquote(db_url.password) if db_url.password else ""

        # 创建连接
        connection = pymysql.connect(
            host=db_url.hostname,
            port=db_url.port,
            user=db_url.username,
            password=password,
            database=db_url.path[1:],
            connect_timeout=10,
            charset='utf8mb4'
        )

        print(f"\n[✓] 成功连接到 MySQL 数据库!")
        print(f"    MySQL 版本: {connection.get_server_info()}")

        # 测试查询
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"    数据库版本: {version[0]}")

        # 测试当前数据库
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()
        print(f"    当前数据库: {current_db[0]}")

        cursor.close()
        connection.close()

        print(f"\n[✓] 连接测试通过！")
        return True

    except pymysql.Error as e:
        print(f"\n[✗] MySQL 连接失败!")
        print(f"    错误代码: {e.args[0]}")
        print(f"    错误信息: {e.args[1]}")
        return False

    except Exception as e:
        print(f"\n[✗] 测试过程中发生错误!")
        print(f"    错误信息: {str(e)}")
        return False


if __name__ == "__main__":
    test_mysql_connection()
