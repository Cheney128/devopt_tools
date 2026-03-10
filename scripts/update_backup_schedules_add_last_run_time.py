"""
数据库更新脚本：为backup_schedules表添加last_run_time字段
第二阶段数据库优化
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, DateTime, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from app.models.models import Base, BackupSchedule, BackupExecutionLog
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_database():
    """更新数据库结构"""
    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)
    
    # 检查字段是否已存在
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('backup_schedules')]
    
    if 'last_run_time' in columns:
        logger.info("last_run_time字段已存在，跳过添加")
    else:
        # 添加last_run_time字段
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE backup_schedules 
                ADD COLUMN last_run_time DATETIME NULL
            """))
            conn.execute(text("""
                CREATE INDEX ix_backup_schedules_last_run_time 
                ON backup_schedules(last_run_time)
            """))
        logger.info("成功添加last_run_time字段和索引")
    
    # 同步现有数据：从backup_execution_logs表迁移最后执行时间
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
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
        logger.info(f"成功同步{updated_count}条备份计划的last_run_time")
        
    except Exception as e:
        db.rollback()
        logger.error(f"同步数据失败: {str(e)}")
        raise
    finally:
        db.close()
    
    logger.info("数据库更新完成")


if __name__ == "__main__":
    update_database()
