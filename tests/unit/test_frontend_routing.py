"""
前端路由问题测试
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFrontendRouting:
    """测试前端路由配置"""

    def test_ip_location_redirect_config(self):
        """测试 IP 定位重定向配置"""
        router_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'router', 'index.js'
        )
        assert os.path.exists(router_file), f"路由文件不存在：{router_file}"
        
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查 IP 定位重定向是否为绝对路径
            assert "redirect: '/ip-location/search'" in content, "IP 定位重定向应该使用绝对路径 '/ip-location/search'"

    def test_ip_location_tabs_config(self):
        """测试 IP 定位 tabs 配置"""
        index_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'views', 'ip-location', 'IPLocationIndex.vue'
        )
        assert os.path.exists(index_file), f"IP 定位索引文件不存在：{index_file}"
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "path: '/ip-location/search'" in content, "IP 搜索 tab 路径应该是 '/ip-location/search'"
            assert "path: '/ip-location/list'" in content, "IP 列表 tab 路径应该是 '/ip-location/list'"

    def test_users_route_requires_admin(self):
        """测试用户管理路由需要 admin 权限"""
        router_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'router', 'index.js'
        )
        assert os.path.exists(router_file), f"路由文件不存在：{router_file}"
        
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "path: '/users'" in content, "缺少 /users 路由"
            assert "requiresAdmin: true" in content, "用户管理路由应该需要 admin 权限"

    def test_authstore_isadmin_logic(self):
        """测试 authStore isAdmin 计算属性逻辑"""
        authstore_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'stores', 'authStore.js'
        )
        assert os.path.exists(authstore_file), f"authStore 文件不存在：{authstore_file}"
        
        with open(authstore_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "const isAdmin = computed" in content, "缺少 isAdmin 计算属性"
            assert "user.value.roles.some(role => role.name === 'admin')" in content, "isAdmin 应该检查 admin 角色"
            assert "user.value.is_superuser" in content, "isAdmin 应该检查 is_superuser"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
