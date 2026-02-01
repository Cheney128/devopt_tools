#!/usr/bin/env python3
"""
简单测试模板下载API端点
"""
import requests

def test_template_download():
    """测试模板下载API"""
    try:
        url = "http://localhost:8000/api/v1/devices/template"
        print(f"测试API端点: {url}")
        
        # 发送GET请求，获取模板文件
        response = requests.get(url)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容大小: {len(response.content)} 字节")
        
        if response.status_code == 200:
            # 保存模板文件到本地
            with open("test_template.xlsx", "wb") as f:
                f.write(response.content)
            print("✅ API端点测试成功!")
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
    success = test_template_download()
    if success:
        print("✅ 测试通过!")
    else:
        print("❌ 测试失败!")
