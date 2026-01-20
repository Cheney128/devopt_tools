"""
创建数据库脚本
创建项目所需的数据库（如果不存在）
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


def create_database():
    """
    创建数据库（如果不存在）
    """
    print("=" * 60)
    print("数据库创建脚本")
    print("=" * 60)

    # 解析数据库 URL
    db_url = urlparse(settings.DATABASE_URL)
    db_name = db_url.path[1:]  # 去掉开头的 '/'

    print(f"\n数据库配置:")
    print(f"  主机: {db_url.hostname}")
    print(f"  端口: {db_url.port}")
    print(f"  数据库名: {db_name}")
    print(f"  用户名: {db_url.username}")

    try:
        # 解析密码（URL 解码）
        from urllib.parse import unquote
        password = unquote(db_url.password) if db_url.password else ""

        # 先连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=db_url.hostname,
            port=db_url.port,
            user=db_url.username,
            password=password,
            connect_timeout=10,
            charset='utf8mb4'
        )

        cursor = connection.cursor()

        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"\n[✓] 数据库 '{db_name}' 已存在，无需创建。")
        else:
            # 创建数据库
            create_sql = f"""
            CREATE DATABASE `{db_name}`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
            """
            cursor.execute(create_sql)
            connection.commit()
            print(f"\n[✓] 成功创建数据库 '{db_name}'！")

        # 验证数据库创建
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"    字符集: utf8mb4")
            print(f"    排序规则: utf8mb4_unicode_ci")
        else:
            print(f"\n[✗] 数据库创建验证失败！")

        cursor.close()
        connection.close()

        print(f"\n[✓] 数据库操作完成！")
        return True

    except pymysql.Error as e:
        print(f"\n[✗] MySQL 操作失败!")
        print(f"    错误代码: {e.args[0]}")
        print(f"    错误信息: {e.args[1]}")
        return False

    except Exception as e:
        print(f"\n[✗] 操作过程中发生错误!")
        print(f"    错误信息: {str(e)}")
        return False


if __name__ == "__main__":
    create_database()
