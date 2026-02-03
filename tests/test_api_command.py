"""
后端API命令执行测试
测试目标：192.168.80.21
"""
import requests
import sys
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def test_api_command():
    """测试通过API执行命令"""
    print("=" * 60)
    print("测试3: 后端API命令执行")
    print("=" * 60)
    print("API地址: " + API_BASE_URL)
    print("目标设备ID: 1")
    print("-" * 60)

    device_id = 1

    try:
        # 测试1: 查看当前主机名
        print("[1/3] 执行命令查看当前主机名...")
        response = requests.post(
            f"{API_BASE_URL}/devices/{device_id}/execute-command",
            json={
                "command": "display current-configuration | include sysname",
                "variables": {},
                "template_id": None
            },
            timeout=60
        )

        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result.get("success"):
                output = result.get("output", "")
                if "huawei-test" in output:
                    print("OK 当前主机名是 huawei-test")
                elif "huawei" in output:
                    print("OK 当前主机名是 huawei")
                else:
                    print("WARN 无法识别主机名")
            else:
                print("FAIL 命令执行失败: " + result.get("message", "未知错误"))
                return False
        else:
            print("FAIL API请求失败: " + response.text)
            return False

        # 测试2: 修改主机名为 final-test
        print("[2/3] 修改主机名为 final-test...")
        response = requests.post(
            f"{API_BASE_URL}/devices/{device_id}/execute-command",
            json={
                "command": "system-view ; sysname final-test ; commit ; return",
                "variables": {},
                "template_id": None
            },
            timeout=60
        )

        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result.get("success"):
                print("OK 命令执行成功")
            else:
                print("WARN 命令可能未完全成功: " + result.get("message", "未知错误"))
        else:
            print("FAIL API请求失败: " + response.text)
            return False

        # 测试3: 验证主机名修改
        print("[3/3] 验证主机名修改...")
        response = requests.post(
            f"{API_BASE_URL}/devices/{device_id}/execute-command",
            json={
                "command": "display current-configuration | include sysname",
                "variables": {},
                "template_id": None
            },
            timeout=60
        )

        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result.get("success"):
                output = result.get("output", "")
                if "final-test" in output:
                    print("OK 主机名已修改为 final-test")
                    test_result = True
                else:
                    print("FAIL 主机名修改验证失败")
                    test_result = False
            else:
                print("FAIL 命令执行失败")
                test_result = False
        else:
            print("FAIL API请求失败")
            test_result = False

        print("=" * 60)
        print("测试3结果: 后端API - " + ("成功" if test_result else "失败"))
        print("=" * 60)
        return test_result

    except requests.exceptions.ConnectionError as e:
        print("FAIL 无法连接到后端API，请确保服务已启动: " + str(e))
        print("=" * 60)
        print("测试3结果: 后端API - 失败")
        print("=" * 60)
        return False
    except Exception as e:
        print("FAIL API测试失败: " + str(e))
        import traceback
        traceback.print_exc()
        print("=" * 60)
        print("测试3结果: 后端API - 失败")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_api_command()
    sys.exit(0 if success else 1)
