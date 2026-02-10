import httpx
import traceback

with httpx.Client(base_url="http://localhost:8000") as client:
    # 获取验证码
    r = client.get("/api/v1/auth/captcha")
    data = r.json()
    captcha_id = data.get("captcha_id")
    print(f"验证码ID: {captcha_id}")

    # 尝试登录
    try:
        r = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
            "captcha_id": captcha_id,
            "captcha_code": "ANY",
            "remember": False
        })
        print(f"登录状态: {r.status_code}")
        print(f"响应: {r.text[:1000]}")
    except Exception as e:
        print(f"异常: {e}")
        traceback.print_exc()
