"""
更新数据库中设备的配置为正确的华为交换机信息
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.models import Device

def update_device():
    """更新设备配置"""
    print("=" * 60)
    print("更新设备配置")
    print("=" * 60)

    db = next(get_db())

    try:
        # 获取设备ID为1的设备
        device = db.query(Device).filter(Device.id == 1).first()

        if not device:
            print("FAIL 设备ID=1不存在")
            return False

        print("当前设备信息:")
        print("  ID: " + str(device.id))
        print("  主机名: " + str(device.hostname))
        print("  IP: " + str(device.ip_address))
        print("  用户名: " + str(device.username))
        print("  密码: " + str(device.password))
        print("  厂商: " + str(device.vendor))

        # 更新为正确的华为交换机信息
        device.ip_address = "192.168.80.21"
        device.username = "njadmin"
        device.password = "Huawei@1234"
        device.hostname = "huawei"
        device.vendor = "huawei"
        device.login_port = 22
        device.login_method = "ssh"

        db.commit()

        print("\n更新后的设备信息:")
        print("  ID: " + str(device.id))
        print("  主机名: " + str(device.hostname))
        print("  IP: " + str(device.ip_address))
        print("  用户名: " + str(device.username))
        print("  密码: " + str(device.password))
        print("  厂商: " + str(device.vendor))

        print("\n" + "=" * 60)
        print("OK 设备配置更新成功")
        print("=" * 60)
        return True

    except Exception as e:
        print("FAIL 更新失败: " + str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_device()
    sys.exit(0 if success else 1)
