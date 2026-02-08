"""
测试设备登录相关字段的测试文件
此测试用于验证数据库中设备信息表的新增字段是否正常工作
包括：login_method, login_port, username, password, sn
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal
from app.models.models import Device
from app.schemas.schemas import DeviceCreate, DeviceUpdate
from sqlalchemy.exc import IntegrityError


def test_device_with_login_fields():
    """
    测试：创建包含登录信息的设备
    验证新增的login_method, login_port, username, password, sn字段是否正常工作
    """
    db = SessionLocal()

    try:
        # 创建一个包含完整登录信息的设备
        device_data = DeviceCreate(
            hostname="test-switch-01",
            ip_address="192.168.1.100",
            vendor="Cisco",
            model="Catalyst 3750",
            os_version="IOS 15.2",
            location="Server Room",
            contact="admin@example.com",
            status="active",
            # 新增的登录信息字段
            login_method="ssh",
            login_port=22,
            username="admin",
            password="Cisco@123",
            sn="FCW1234ABCD"
        )

        # 创建设备
        db_device = Device(**device_data.model_dump())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)

        # 验证设备是否创建成功
        assert db_device.id is not None, "设备ID应为None"
        assert db_device.hostname == "test-switch-01"
        assert db_device.ip_address == "192.168.1.100"
        assert db_device.login_method == "ssh"
        assert db_device.login_port == 22
        assert db_device.username == "admin"
        assert db_device.password == "Cisco@123"
        assert db_device.sn == "FCW1234ABCD"

        print(f"测试1通过：设备创建成功，ID={db_device.id}")
        print(f"  - 登录方式: {db_device.login_method}")
        print(f"  - 登录端口: {db_device.login_port}")
        print(f"  - 用户名: {db_device.username}")
        print(f"  - 密码: {db_device.password}")
        print(f"  - 序列号: {db_device.sn}")

        # 查询设备验证数据存储
        queried_device = db.query(Device).filter(Device.id == db_device.id).first()
        assert queried_device is not None, "查询到的设备不应为None"
        assert queried_device.sn == "FCW1234ABCD"
        print(f"测试2通过：设备查询成功，序列号={queried_device.sn}")

        # 测试更新登录信息
        update_data = DeviceUpdate(
            login_method="telnet",
            login_port=23,
            username="newadmin",
            password="NewPass@456"
        )
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_device, field, value)
        db.commit()
        db.refresh(db_device)

        assert db_device.login_method == "telnet"
        assert db_device.login_port == 23
        assert db_device.username == "newadmin"
        print(f"测试3通过：设备登录信息更新成功")

        # 清理测试数据
        db.delete(db_device)
        db.commit()
        print(f"测试4通过：测试数据已清理")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_device_with_telnet():
    """
    测试：创建使用Telnet登录方式的设备
    """
    db = SessionLocal()

    try:
        device_data = DeviceCreate(
            hostname="test-switch-02",
            ip_address="192.168.1.101",
            vendor="Huawei",
            model="S5700",
            os_version="VRP 8.180",
            location="Floor 1",
            contact="netadmin@example.com",
            status="active",
            # Telnet登录配置
            login_method="telnet",
            login_port=23,
            username="huawei",
            password="Huawei@123",
            sn="210235A123456"
        )

        db_device = Device(**device_data.model_dump())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)

        assert db_device.login_method == "telnet"
        assert db_device.login_port == 23
        print(f"测试5通过：Telnet设备创建成功")

        # 清理测试数据
        db.delete(db_device)
        db.commit()
        print(f"测试6通过：测试数据已清理")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_unique_ip_and_sn():
    """
    测试：验证IP地址和序列号的唯一性约束
    """
    db = SessionLocal()

    try:
        # 创建第一个设备
        device1 = DeviceCreate(
            hostname="test-switch-03",
            ip_address="192.168.1.102",
            vendor="H3C",
            model="S5120",
            username="admin",
            password="H3C@123",
            sn="H3C123456789"
        )

        db_device1 = Device(**device1.model_dump())
        db.add(db_device1)
        db.commit()

        print(f"测试7通过：第一个设备创建成功，IP={db_device1.ip_address}, SN={db_device1.sn}")

        # 尝试创建IP地址重复的设备（应该失败）
        device2_same_ip = DeviceCreate(
            hostname="test-switch-04",
            ip_address="192.168.1.102",  # 重复的IP
            vendor="H3C",
            model="S5120",
            username="admin",
            password="H3C@123"
        )

        try:
            db_device2 = Device(**device2_same_ip.model_dump())
            db.add(db_device2)
            db.commit()
            print(f"测试8失败：IP地址重复检查未生效")
            return False
        except IntegrityError:
            db.rollback()
            print(f"测试8通过：IP地址重复检查生效，拒绝创建重复IP设备")

        # 尝试创建序列号重复的设备（应该失败）
        device2_same_sn = DeviceCreate(
            hostname="test-switch-05",
            ip_address="192.168.1.103",  # 不同的IP
            vendor="H3C",
            model="S5120",
            username="admin",
            password="H3C@123",
            sn="H3C123456789"  # 重复的SN
        )

        try:
            db_device3 = Device(**device2_same_sn.model_dump())
            db.add(db_device3)
            db.commit()
            print(f"测试9失败：序列号重复检查未生效")
            return False
        except IntegrityError:
            db.rollback()
            print(f"测试9通过：序列号重复检查生效，拒绝创建重复SN设备")

        # 清理测试数据
        db.delete(db_device1)
        db.commit()
        print(f"测试10通过：测试数据已清理")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试设备登录相关字段...")
    print("=" * 60)
    print()

    # 运行测试
    success = True
    success = test_device_with_login_fields() and success
    print()
    success = test_device_with_telnet() and success
    print()
    success = test_unique_ip_and_sn() and success

    print()
    print("=" * 60)
    if success:
        print("所有测试通过！")
    else:
        print("部分测试失败！")
    print("=" * 60)
