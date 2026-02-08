#!/usr/bin/env python3
"""
测试Excel模板生成功能
直接使用当前应用的数据库连接进行测试
"""
import os
import sys
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入设备模型和Excel服务
from app.models.models import Device
from app.services.excel_service import generate_device_template

def test_excel_template_generation():
    """测试Excel模板生成功能"""
    try:
        # 从环境变量或配置文件获取数据库连接信息
        # 这里使用与应用相同的数据库连接字符串
        from app.models import DATABASE_URL
        
        print(f"使用数据库连接: {DATABASE_URL}")
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL)
        
        # 创建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 创建会话
        db = SessionLocal()
        
        try:
            # 测试1: 生成空模板（不提供session）
            print("\n=== 测试1: 生成空模板 ===")
            empty_template = generate_device_template()
            template_size = len(empty_template.getvalue())
            print(f"空模板生成成功，大小: {template_size} 字节")
            
            # 测试2: 使用数据库会话生成模板
            print("\n=== 测试2: 使用数据库会话生成模板 ===")
            db_template = generate_device_template(db)
            db_template_size = len(db_template.getvalue())
            print(f"带数据库数据的模板生成成功，大小: {db_template_size} 字节")
            
            # 测试3: 验证生成的Excel文件可以被pandas读取
            print("\n=== 测试3: 验证Excel文件完整性 ===")
            import pandas as pd
            
            # 重置文件指针到开头
            db_template.seek(0)
            
            # 尝试读取Excel文件
            df = pd.read_excel(db_template, engine='openpyxl')
            print(f"成功读取Excel文件，包含 {len(df)} 行数据")
            print(f"列名: {list(df.columns)}")
            
            # 如果有数据，显示前5行
            if len(df) > 0:
                print("\n前5行数据:")
                print(df.head())
            
            # 测试4: 测试API端点
            print("\n=== 测试4: 测试API端点 ===")
            # 这里我们可以使用FastAPI的测试客户端
            from fastapi.testclient import TestClient
            from app.main import app
            
            client = TestClient(app)
            response = client.get("/api/devices/template")
            print(f"API响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容大小: {len(response.content)} 字节")
            
            if response.status_code == 200:
                print("✅ API端点测试成功!")
            else:
                print(f"❌ API端点测试失败: {response.text}")
                
        finally:
            # 关闭会话
            db.close()
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("开始测试Excel模板生成功能...")
    success = test_excel_template_generation()
    if success:
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)