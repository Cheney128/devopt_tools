"""
创建备份监控相关的数据库表
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models import engine
from app.config import settings


def create_backup_tables():
    """创建备份相关的表"""
    
    # SQL创建语句
    create_backup_schedules_sql = """
    CREATE TABLE IF NOT EXISTS `backup_schedules` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `device_id` INT NOT NULL,
        `schedule_type` VARCHAR(20) NOT NULL DEFAULT 'daily',
        `time` VARCHAR(10),
        `day` INT,
        `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX `ix_backup_schedules_device_id` (`device_id`),
        FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    create_backup_execution_logs_sql = """
    CREATE TABLE IF NOT EXISTS `backup_execution_logs` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `task_id` VARCHAR(50) NOT NULL,
        `device_id` INT NOT NULL,
        `schedule_id` INT,
        `status` VARCHAR(20) NOT NULL,
        `execution_time` FLOAT,
        `trigger_type` VARCHAR(20) DEFAULT 'scheduled',
        `config_id` INT,
        `error_message` TEXT,
        `error_details` TEXT,
        `started_at` DATETIME,
        `completed_at` DATETIME,
        `config_size` INT,
        `git_commit_id` VARCHAR(40),
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX `ix_backup_execution_logs_task_id` (`task_id`),
        INDEX `ix_backup_execution_logs_device_id` (`device_id`),
        INDEX `ix_backup_execution_logs_created_at` (`created_at`),
        FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE,
        FOREIGN KEY (`schedule_id`) REFERENCES `backup_schedules` (`id`) ON DELETE SET NULL,
        FOREIGN KEY (`config_id`) REFERENCES `configurations` (`id`) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        print("正在创建 backup_schedules 表...")
        with engine.begin() as conn:
            conn.execute(text(create_backup_schedules_sql))
        print("✅ backup_schedules 表创建成功")
        
        print("\n正在创建 backup_execution_logs 表...")
        with engine.begin() as conn:
            conn.execute(text(create_backup_execution_logs_sql))
        print("✅ backup_execution_logs 表创建成功")
        
        print("\n✅ 所有备份相关表创建完成！")
        
    except Exception as e:
        print(f"\n❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_backup_tables()
