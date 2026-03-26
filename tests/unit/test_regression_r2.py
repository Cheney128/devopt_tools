"""
R2 回归测试：配置计划加载失败

测试配置计划 API 和数据库表是否正常
"""
import pytest
import os
import sys
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBackupSchedulesExists:
    """测试配置计划相关代码是否存在"""

    def test_database_table_exists(self):
        """测试数据库表 backup_schedules 是否存在"""
        # 读取 .env 文件获取数据库配置
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '.env'
        )
        assert os.path.exists(env_file), f".env 文件不存在：{env_file}"
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查数据库配置
            assert 'DATABASE_URL' in content, ".env 中缺少 DATABASE_URL 配置"
            assert '10.21.65.20' in content or 'localhost' in content, "数据库地址配置异常"

    def test_backend_model_exists(self):
        """测试后端 BackupSchedule 模型是否存在"""
        models_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'models', 'models.py'
        )
        assert os.path.exists(models_file), f"模型文件不存在：{models_file}"
        
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'class BackupSchedule' in content, "缺少 BackupSchedule 模型"
            assert '__tablename__ = "backup_schedules"' in content, "BackupSchedule 表名配置错误"

    def test_backend_schema_exists(self):
        """测试后端 BackupSchedule Schema 是否存在"""
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'schemas', 'schemas.py'
        )
        assert os.path.exists(schema_file), f"Schema 文件不存在：{schema_file}"
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'class BackupScheduleBase' in content, "缺少 BackupScheduleBase Schema"
            assert 'class BackupScheduleCreate' in content, "缺少 BackupScheduleCreate Schema"
            assert 'class BackupSchedule' in content, "缺少 BackupSchedule Schema"

    def test_backend_api_endpoint_exists(self):
        """测试后端 API 端点是否存在"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'api', 'endpoints', 'configurations.py'
        )
        assert os.path.exists(api_file), f"API 文件不存在：{api_file}"
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '@router.get("/backup-schedules"' in content, "缺少 GET /backup-schedules 端点"
            assert 'def get_backup_schedules' in content, "缺少 get_backup_schedules 函数"

    def test_frontend_api_config_exists(self):
        """测试前端 API 配置是否存在"""
        api_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'api', 'index.js'
        )
        assert os.path.exists(api_file), f"API 文件不存在：{api_file}"
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'getBackupSchedules' in content, "前端 API 缺少 getBackupSchedules 方法"
            assert '/configurations/backup-schedules' in content, "前端 API 路径配置错误"

    def test_frontend_view_exists(self):
        """测试前端视图是否存在"""
        view_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'frontend', 'src', 'views', 'BackupScheduleManagement.vue'
        )
        assert os.path.exists(view_file), f"视图文件不存在：{view_file}"
        
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'getBackupSchedules' in content or 'backup-schedules' in content, "视图文件缺少 API 调用"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
