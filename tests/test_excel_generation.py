"""
测试Excel生成功能的脚本
用于排查模板下载失败问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal
from app.services.excel_service import generate_device_template

def test_excel_generation():
    """测试Excel生成功能"""
    print("=== 测试Excel生成功能 ===")
    
    # 测试1: 不使用数据库会话，生成空模板
    print("\n1. 测试生成空模板...")
    try:
        template_stream = generate_device_template()
        print("✓ 空模板生成成功")
        print(f"  模板大小: {len(template_stream.getvalue())} 字节")
    except Exception as e:
        print(f"✗ 空模板生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 使用数据库会话，生成包含设备数据的模板
    print("\n2. 测试生成包含设备数据的模板...")
    try:
        session = SessionLocal()
        template_stream = generate_device_template(session)
        session.close()
        print("✓ 包含设备数据的模板生成成功")
        print(f"  模板大小: {len(template_stream.getvalue())} 字节")
    except Exception as e:
        print(f"✗ 包含设备数据的模板生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 测试数据库连接和查询
    print("\n3. 测试数据库连接和查询...")
    try:
        session = SessionLocal()
        # 测试数据库连接
        session.execute("SELECT 1")
        print("✓ 数据库连接成功")
        
        # 测试查询设备数据
        from app.models.models import Device
        devices = session.query(Device).all()
        print(f"✓ 查询设备数据成功，共找到 {len(devices)} 台设备")
        
        if devices:
            print("  设备列表前3个:")
            for i, device in enumerate(devices[:3]):
                print(f"  {i+1}. {device.hostname} ({device.ip_address})")
        
        session.close()
    except Exception as e:
        print(f"✗ 数据库操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_excel_generation()