"""
R1 回归测试：IP 定位模块消失

测试 IP 定位模块的前端和后端代码是否完整提交
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestIPLocationModuleExists:
    """测试 IP 定位模块代码是否存在"""

    def test_backend_api_file_exists(self):
        """测试后端 API 文件是否存在"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'api', 'endpoints', 'ip_location.py'
        )
        assert os.path.exists(api_file), f"后端 API 文件不存在：{api_file}"

    def test_backend_schema_file_exists(self):
        """测试后端 Schema 文件是否存在"""
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'schemas', 'ip_location_schemas.py'
        )
        assert os.path.exists(schema_file), f"后端 Schema 文件不存在：{schema_file}"

    def test_frontend_router_config(self):
        """测试前端路由配置是否包含 IP 定位"""
        router_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'router', 'index.js'
        )
        assert os.path.exists(router_file), f"路由文件不存在：{router_file}"
        
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '/ip-location' in content, "路由配置中缺少 /ip-location 路由"
            assert 'ip-location' in content, "路由配置中缺少 ip-location 路由定义"

    def test_frontend_app_menu_config(self):
        """测试前端 App.vue 菜单配置是否包含 IP 定位"""
        app_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'App.vue'
        )
        assert os.path.exists(app_file), f"App.vue 文件不存在：{app_file}"
        
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '/ip-location' in content, "App.vue 菜单配置中缺少 /ip-location 菜单项"
            assert 'IP 定位' in content or 'IP 地址定位' in content, "App.vue 菜单配置中缺少 IP 定位文本"

    def test_frontend_api_config(self):
        """测试前端 API 配置是否包含 IP 定位 API"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'api', 'index.js'
        )
        assert os.path.exists(api_file), f"API 文件不存在：{api_file}"
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'ipLocationApi' in content, "API 配置中缺少 ipLocationApi 导出"
            assert '/ip-location' in content, "API 配置中缺少 /ip-location 路径"

    def test_frontend_views_exist(self):
        """测试前端视图组件是否存在"""
        views_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'views', 'ip-location'
        )
        assert os.path.exists(views_dir), f"IP 定位视图目录不存在：{views_dir}"
        
        required_files = ['IPLocationIndex.vue', 'IPLocationSearch.vue', 'IPLocationList.vue']
        for file in required_files:
            file_path = os.path.join(views_dir, file)
            assert os.path.exists(file_path), f"视图文件不存在：{file_path}"

    def test_frontend_components_exist(self):
        """测试前端组件是否存在"""
        components_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'components', 'ip-location'
        )
        assert os.path.exists(components_dir), f"IP 定位组件目录不存在：{components_dir}"
        
        # CollectionStatus.vue 应该存在
        component_file = os.path.join(components_dir, 'CollectionStatus.vue')
        assert os.path.exists(component_file), f"组件文件不存在：{component_file}"

    def test_backend_router_registered(self):
        """测试后端路由是否已注册"""
        api_init_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'api', '__init__.py'
        )
        assert os.path.exists(api_init_file), f"API 初始化文件不存在：{api_init_file}"
        
        with open(api_init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'ip_location' in content, "API 初始化文件中缺少 ip_location 导入"
            assert '/ip-location' in content, "API 初始化文件中缺少 /ip-location 路由注册"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
