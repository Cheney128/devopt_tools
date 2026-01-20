"""
数据库重建脚本 - 删除所有表并重新创建
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

from app.models import Base, engine
from app.models.models import Device, Port, VLAN, Inspection, Configuration


def rebuild_db():
    """
    重建数据库表结构（删除所有表后重新创建）
    """
    print("警告：此操作将删除数据库中的所有表和数据！")
    print("正在删除所有表...")

    # 删除所有表
    Base.metadata.drop_all(bind=engine)

    print("所有表已删除！")
    print("正在重新创建表...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("数据库重建完成！")
    print(f"\n当前数据库表结构:")
    print(f"  - devices (设备信息表)")
    print(f"    包含字段: id, hostname, ip_address, vendor, model, os_version,")
    print(f"              location, contact, status, login_method, login_port,")
    print(f"              username, password, sn, created_at, updated_at")
    print(f"  - ports (端口信息表)")
    print(f"  - vlans (VLAN信息表)")
    print(f"  - inspections (巡检结果表)")
    print(f"  - configurations (配置信息表)")


if __name__ == "__main__":
    rebuild_db()
