#!/usr/bin/env python3
"""
自动数据库迁移脚本
在应用启动前自动执行数据库迁移

使用方法:
- 在entrypoint.sh中调用: python3 /unified-app/scripts/auto_migrate.py

特性:
- 检查是否需要迁移
- 幂等性执行
- 失败时记录日志但不阻止应用启动
"""

import sys
import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, '/unified-app')
sys.path.insert(0, '/unified-app/app')


def check_migration_needed():
    """检查是否需要进行迁移"""
    try:
        from sqlalchemy import create_engine, inspect
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.warning("DATABASE_URL 未设置，跳过迁移检查")
            return False
        
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        # 检查字段是否存在
        columns = [col['name'] for col in inspector.get_columns('backup_schedules')]
        
        if 'last_run_time' in columns:
            logger.info("✓ last_run_time 字段已存在，无需迁移")
            return False
        
        logger.info("⚠ last_run_time 字段不存在，需要迁移")
        return True
        
    except Exception as e:
        logger.error(f"检查迁移状态时出错: {str(e)}")
        # 出错时返回True，尝试执行迁移
        return True


def run_migration():
    """执行迁移"""
    try:
        # 导入迁移脚本
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "db_migrate_docker", 
            "/unified-app/scripts/db_migrate_docker.py"
        )
        migrate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migrate_module)
        
        # 执行迁移
        return migrate_module.main() == 0
        
    except Exception as e:
        logger.error(f"执行迁移时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("自动数据库迁移检查")
    logger.info("=" * 60)
    
    # 检查是否需要迁移
    if not check_migration_needed():
        logger.info("数据库已是最新版本")
        return 0
    
    # 执行迁移
    logger.info("开始执行数据库迁移...")
    
    if run_migration():
        logger.info("✓ 数据库迁移成功")
        return 0
    else:
        logger.error("✗ 数据库迁移失败")
        logger.warning("应用将继续启动，但某些功能可能无法正常工作")
        # 返回0不阻止应用启动，但记录错误
        return 0


if __name__ == "__main__":
    sys.exit(main())
