"""
R3 回归测试：用户管理跳转登录

测试用户管理权限检查代码是否完整
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestUserManagementPermission:
    """测试用户管理权限检查代码是否存在"""

    def test_frontend_router_requires_admin(self):
        """测试前端路由是否配置 requiresAdmin"""
        router_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'router', 'index.js'
        )
        assert os.path.exists(router_file), f"路由文件不存在：{router_file}"
        
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "path: '/users'" in content, "路由配置中缺少 /users 路径"
            assert 'requiresAdmin' in content, "路由配置中缺少 requiresAdmin 权限检查"

    def test_frontend_authstore_isadmin_check(self):
        """测试前端 authStore 是否有 isAdmin 检查"""
        authstore_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'stores', 'authStore.js'
        )
        assert os.path.exists(authstore_file), f"authStore 文件不存在：{authstore_file}"
        
        with open(authstore_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'isAdmin' in content, "authStore 中缺少 isAdmin 计算属性"
            assert 'is_superuser' in content or 'roles' in content, "authStore 中缺少角色检查逻辑"

    def test_backend_user_schema_has_roles(self):
        """测试后端用户 Schema 是否包含 roles 字段"""
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'schemas', 'user_schemas.py'
        )
        assert os.path.exists(schema_file), f"用户 Schema 文件不存在：{schema_file}"
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'class UserResponse' in content, "缺少 UserResponse Schema"
            assert 'is_superuser' in content, "UserResponse 中缺少 is_superuser 字段"
            assert 'roles' in content, "UserResponse 中缺少 roles 字段"

    def test_backend_auth_me_endpoint_exists(self):
        """测试后端 /auth/me API 端点是否存在"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'api', 'endpoints', 'auth.py'
        )
        assert os.path.exists(api_file), f"认证 API 文件不存在：{api_file}"
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '@router.get("/me"' in content or '@router.get("/me", ' in content, "缺少 GET /auth/me 端点"
            assert 'get_current_user_info' in content or 'get_current_user' in content, "缺少获取当前用户信息的函数"

    def test_frontend_auth_api_getcurrentuser(self):
        """测试前端认证 API 是否有 getCurrentUser 方法"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'api', 'auth.js'
        )
        assert os.path.exists(api_file), f"认证 API 文件不存在：{api_file}"
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'getCurrentUser' in content, "认证 API 中缺少 getCurrentUser 方法"
            assert "/auth/me" in content, "认证 API 中缺少 /auth/me 路径"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
