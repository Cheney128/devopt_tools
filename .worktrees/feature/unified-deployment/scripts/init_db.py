"""
数据库初始化脚本
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
from app.models.models import Device, Port, VLAN, Inspection, Configuration, MACAddress, DeviceVersion, BackupSchedule


def init_db():
    """
    初始化数据库表结构
    """
    print("开始初始化数据库...")
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成！")


if __name__ == "__main__":
    init_db()
