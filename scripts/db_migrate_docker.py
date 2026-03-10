#!/usr/bin/env python3
"""
Docker生产环境数据库迁移脚本
用于在Docker容器中执行数据库结构变更

使用方法:
1. 在宿主机上执行: docker compose exec app python3 /unified-app/scripts/db_migrate_docker.py
2. 或在容器内执行: python3 /unified-app/scripts/db_migrate_docker.py

特性:
- 自动检测是否在Docker环境中运行
- 支持数据库备份（迁移前自动备份）
- 幂等性设计（可重复执行，不会重复添加已存在的字段）
- 详细的日志输出
- 失败回滚机制
"""

import sys
import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加应用目录到Python路径
sys.path.insert(0, '/unified-app')
sys.path.insert(0, '/unified-app/app')


def check_docker_environment():
    """检查是否在Docker环境中运行"""
    # 检查典型的Docker环境标志
    if os.path.exists('/.dockerenv'):
        return True
    
    # 检查cgroup
    try:
        with open('/proc/1/cgroup', 'r') as f:
            content = f.read()
            if 'docker' in content or 'containerd' in content:
                return True
    except:
        pass
    
    return False


def backup_database():
    """在迁移前备份数据库"""
    logger.info("=" * 60)
    logger.info("步骤 1/4: 备份数据库")
    logger.info("=" * 60)
    
    # 从环境变量获取数据库连接信息
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        logger.error("错误: DATABASE_URL 环境变量未设置")
        return False
    
    # 解析数据库连接信息
    try:
        # 格式: mysql+pymysql://user:password@host:port/database
        from urllib.parse import urlparse
        parsed = urlparse(db_url.replace('mysql+pymysql', 'mysql'))
        
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 3306
        database = parsed.path.lstrip('/')
        
        # 创建备份目录
        backup_dir = Path('/backups')
        backup_dir.mkdir(exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"db_backup_{timestamp}.sql"
        
        # 执行mysqldump
        cmd = [
            'mysqldump',
            '-h', host,
            '-P', str(port),
            '-u', user,
            f'-p{password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            database
        ]
        
        logger.info(f"正在备份数据库到: {backup_file}")
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            logger.info(f"✓ 数据库备份成功: {backup_file}")
            return str(backup_file)
        else:
            logger.error(f"✗ 数据库备份失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 备份过程出错: {str(e)}")
        return False


def check_field_exists(engine, table_name, field_name):
    """检查字段是否已存在"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return field_name in columns


def check_index_exists(engine, table_name, index_name):
    """检查索引是否已存在"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def migrate_database():
    """执行数据库迁移"""
    logger.info("=" * 60)
    logger.info("步骤 2/4: 检查并执行数据库迁移")
    logger.info("=" * 60)
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.sql import func
        
        # 获取数据库连接
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("错误: DATABASE_URL 环境变量未设置")
            return False
        
        engine = create_engine(db_url)
        
        # 检查 last_run_time 字段是否已存在
        if check_field_exists(engine, 'backup_schedules', 'last_run_time'):
            logger.info("✓ last_run_time 字段已存在，跳过添加")
        else:
            logger.info("正在添加 last_run_time 字段...")
            
            # 添加字段
            with engine.begin() as conn:
                conn.execute(text("""
                    ALTER TABLE backup_schedules 
                    ADD COLUMN last_run_time DATETIME NULL
                """))
            
            logger.info("✓ last_run_time 字段添加成功")
        
        # 检查索引是否已存在
        if check_index_exists(engine, 'backup_schedules', 'ix_backup_schedules_last_run_time'):
            logger.info("✓ ix_backup_schedules_last_run_time 索引已存在，跳过创建")
        else:
            logger.info("正在创建索引...")
            
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE INDEX ix_backup_schedules_last_run_time 
                    ON backup_schedules(last_run_time)
                """))
            
            logger.info("✓ 索引创建成功")
        
        # 同步现有数据
        logger.info("正在同步现有数据...")
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # 使用SQLAlchemy模型
            from app.models.models import BackupSchedule, BackupExecutionLog
            
            # 查询所有备份计划
            schedules = db.query(BackupSchedule).all()
            updated_count = 0
            
            for schedule in schedules:
                # 查询该计划的最后执行时间
                last_execution = db.query(
                    func.max(BackupExecutionLog.completed_at).label('last_run')
                ).filter(
                    BackupExecutionLog.schedule_id == schedule.id
                ).scalar()
                
                if last_execution and not schedule.last_run_time:
                    schedule.last_run_time = last_execution
                    updated_count += 1
            
            db.commit()
            logger.info(f"✓ 成功同步 {updated_count} 条备份计划的 last_run_time")
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ 同步数据失败: {str(e)}")
            return False
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 迁移过程出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_migration():
    """验证迁移结果"""
    logger.info("=" * 60)
    logger.info("步骤 3/4: 验证迁移结果")
    logger.info("=" * 60)
    
    try:
        from sqlalchemy import create_engine, inspect
        
        db_url = os.environ.get('DATABASE_URL')
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        # 验证字段存在
        columns = [col['name'] for col in inspector.get_columns('backup_schedules')]
        if 'last_run_time' not in columns:
            logger.error("✗ 验证失败: last_run_time 字段不存在")
            return False
        logger.info("✓ last_run_time 字段存在")
        
        # 验证索引存在
        indexes = [idx['name'] for idx in inspector.get_indexes('backup_schedules')]
        if 'ix_backup_schedules_last_run_time' not in indexes:
            logger.error("✗ 验证失败: ix_backup_schedules_last_run_time 索引不存在")
            return False
        logger.info("✓ ix_backup_schedules_last_run_time 索引存在")
        
        # 验证数据同步
        from sqlalchemy.orm import sessionmaker
        from app.models.models import BackupSchedule
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            total_schedules = db.query(BackupSchedule).count()
            schedules_with_last_run = db.query(BackupSchedule).filter(
                BackupSchedule.last_run_time.isnot(None)
            ).count()
            
            logger.info(f"✓ 备份计划总数: {total_schedules}")
            logger.info(f"✓ 已设置 last_run_time 的计划数: {schedules_with_last_run}")
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 验证过程出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def update_migration_status():
    """更新迁移状态标记"""
    logger.info("=" * 60)
    logger.info("步骤 4/4: 更新迁移状态")
    logger.info("=" * 60)
    
    try:
        # 创建迁移完成标记文件
        marker_file = Path('/unified-app/.db_migration_completed')
        timestamp = datetime.now().isoformat()
        
        with open(marker_file, 'w') as f:
            f.write(f"Database migration completed at: {timestamp}\n")
            f.write("Migration: Add last_run_time to backup_schedules\n")
        
        logger.info(f"✓ 迁移状态已更新: {marker_file}")
        return True
        
    except Exception as e:
        logger.error(f"✗ 更新迁移状态失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Docker生产环境数据库迁移工具")
    logger.info("=" * 60)
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查Docker环境
    if check_docker_environment():
        logger.info("✓ 检测到Docker环境")
    else:
        logger.warning("⚠ 未检测到Docker环境，继续执行...")
    
    # 步骤1: 备份数据库
    backup_file = backup_database()
    if not backup_file:
        logger.error("数据库备份失败，是否继续? (y/n)")
        # 在自动化环境中默认继续
        logger.info("在自动化环境中，继续执行迁移...")
    
    # 步骤2: 执行迁移
    if not migrate_database():
        logger.error("=" * 60)
        logger.error("数据库迁移失败!")
        logger.error("=" * 60)
        
        if backup_file:
            logger.info(f"可以使用备份文件恢复: {backup_file}")
        
        sys.exit(1)
    
    # 步骤3: 验证迁移
    if not verify_migration():
        logger.error("=" * 60)
        logger.error("迁移验证失败!")
        logger.error("=" * 60)
        sys.exit(1)
    
    # 步骤4: 更新状态
    if not update_migration_status():
        logger.warning("⚠ 迁移状态更新失败，但迁移已成功")
    
    # 完成
    logger.info("=" * 60)
    logger.info("数据库迁移成功完成!")
    logger.info("=" * 60)
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if backup_file:
        logger.info(f"数据库备份文件: {backup_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
