#!/usr/bin/env python3
"""
简单测试Excel模板下载API端点
直接使用FastAPI测试客户端
"""
import sys

# 添加项目根目录到Python路径
sys.path.append('/d/BaiduSyncdisk/5.code/netdevops/switch_manage')

def test_api_endpoint():
    """测试API端点"""
    try:
        # 导入FastAPI测试客户端
        from fastapi.testclient import TestClient
        
        # 导入FastAPI应用
        from app.main import app
        
        # 创建测试客户端
        client = TestClient(app)
        
        # 测试设备模板下载端点
        print("测试设备模板下载API端点...")
        response = client.get("/api/devices/template")
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容大小: {len(response.content)} 字节")
        
        if response.status_code == 200:
            print("✅ API端点测试成功!")
            # 保存模板文件到本地，方便检查
            with open("test_template.xlsx", "wb") as f:
                f.write(response.content)
            print(f"模板文件已保存到: test_template.xlsx")
            return True
        else:
            print(f"❌ API端点测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试API端点...")
    success = test_api_endpoint()
    if success:
        print("✅ 测试通过!")
        sys.exit(0)
    else:
        print("❌ 测试失败!")
        sys.exit(1)