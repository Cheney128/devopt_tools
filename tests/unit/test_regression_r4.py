"""
R4 回归测试：延迟检测显示不见了

测试设备管理表格中延迟检测列是否完整提交
"""
import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestLatencyDisplayExists:
    """测试延迟检测列代码是否存在"""

    def test_backend_model_has_latency_fields(self):
        """测试后端设备模型是否包含延迟字段"""
        models_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'models', 'models.py'
        )
        assert os.path.exists(models_file), f"模型文件不存在：{models_file}"
        
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'latency' in content, "设备模型中缺少 latency 字段"
            assert 'last_latency_check' in content, "设备模型中缺少 last_latency_check 字段"
            assert 'latency_check_enabled' in content, "设备模型中缺少 latency_check_enabled 字段"

    def test_backend_schema_has_latency_fields(self):
        """测试后端 Schema 是否包含延迟字段"""
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'schemas', 'schemas.py'
        )
        assert os.path.exists(schema_file), f"Schema 文件不存在：{schema_file}"
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'latency' in content, "Schema 中缺少 latency 字段"
            assert 'last_latency_check' in content, "Schema 中缺少 last_latency_check 字段"

    def test_frontend_device_management_has_latency_column(self):
        """测试前端设备管理表格是否包含延迟列"""
        device_mgmt_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'views', 'DeviceManagement.vue'
        )
        assert os.path.exists(device_mgmt_file), f"设备管理视图文件不存在：{device_mgmt_file}"
        
        with open(device_mgmt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'latency' in content, "设备管理表格中缺少延迟列"
            assert '延迟' in content or '延时' in content, "设备管理表格中缺少延迟列标签"
            assert 'last_latency_check' in content, "设备管理表格中缺少检测时间列"
            assert '检测时间' in content, "设备管理表格中缺少检测时间列标签"

    def test_frontend_format_datetime_function_exists(self):
        """测试前端是否有 formatDateTime 函数"""
        device_mgmt_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'views', 'DeviceManagement.vue'
        )
        assert os.path.exists(device_mgmt_file), f"设备管理视图文件不存在：{device_mgmt_file}"
        
        with open(device_mgmt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'formatDateTime' in content, "设备管理视图中缺少 formatDateTime 函数"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
