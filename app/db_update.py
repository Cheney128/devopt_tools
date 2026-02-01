"""
数据库结构更新脚本
用于添加新字段和创建新表到现有的数据库
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models import engine


def update_configurations_table():
    """
    更新configurations表，添加缺失的字段
    """
    print("正在更新 configurations 表...")
    
    connection = engine.connect()
    try:
        # 检查 version 列是否存在
        result = connection.execute(text("SHOW COLUMNS FROM configurations LIKE 'version'"))
        if not result.fetchone():
            print("添加 version 列...")
            connection.execute(text("""
                ALTER TABLE configurations
                ADD COLUMN version VARCHAR(50) NOT NULL DEFAULT '1.0'
                AFTER config_time
            """))
            print("  ✓ version 列已添加")
        else:
            print("  ✓ version 列已存在")
        
        # 检查 change_description 列是否存在
        result = connection.execute(text("SHOW COLUMNS FROM configurations LIKE 'change_description'"))
        if not result.fetchone():
            print("添加 change_description 列...")
            connection.execute(text("""
                ALTER TABLE configurations
                ADD COLUMN change_description TEXT NULL
                AFTER version
            """))
            print("  ✓ change_description 列已添加")
        else:
            print("  ✓ change_description 列已存在")
        
        # 检查 git_commit_id 列是否存在
        result = connection.execute(text("SHOW COLUMNS FROM configurations LIKE 'git_commit_id'"))
        if not result.fetchone():
            print("添加 git_commit_id 列...")
            connection.execute(text("""
                ALTER TABLE configurations
                ADD COLUMN git_commit_id VARCHAR(64) NULL
                AFTER change_description
            """))
            print("  ✓ git_commit_id 列已添加")
        else:
            print("  ✓ git_commit_id 列已存在")
        
        # 提交事务
        connection.commit()
        print("\nconfigurations 表更新完成!")
        
    finally:
        connection.close()


def create_git_configs_table():
    """
    创建git_configs表
    """
    print("\n正在创建 git_configs 表...")
    
    connection = engine.connect()
    try:
        # 检查 git_configs 表是否存在
        result = connection.execute(text("SHOW TABLES LIKE 'git_configs'"))
        if not result.fetchone():
            print("创建 git_configs 表...")
            connection.execute(text("""
                CREATE TABLE git_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    repo_url VARCHAR(255) NOT NULL UNIQUE,
                    username VARCHAR(100) NULL,
                    password VARCHAR(255) NULL,
                    branch VARCHAR(50) NOT NULL DEFAULT 'main',
                    ssh_key_path VARCHAR(255) NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """))
            print("  ✓ git_configs 表已创建")
        else:
            print("  ✓ git_configs 表已存在")
        
        # 提交事务
        connection.commit()
        print("\ngit_configs 表创建完成!")
        
    finally:
        connection.close()


def create_command_templates_table():
    """
    创建command_templates表
    """
    print("\n正在创建 command_templates 表...")
    
    connection = engine.connect()
    try:
        # 检查 command_templates 表是否存在
        result = connection.execute(text("SHOW TABLES LIKE 'command_templates'"))
        if not result.fetchone():
            print("创建 command_templates 表...")
            connection.execute(text("""
                CREATE TABLE command_templates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT NULL,
                    command TEXT NOT NULL,
                    vendor VARCHAR(50) NULL,
                    device_type VARCHAR(50) NULL,
                    variables JSON NULL,
                    tags JSON NULL,
                    is_public BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by VARCHAR(100) NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_name (name),
                    INDEX idx_vendor (vendor),
                    INDEX idx_device_type (device_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """))
            print("  ✓ command_templates 表已创建")
        else:
            print("  ✓ command_templates 表已存在")
        
        # 提交事务
        connection.commit()
        print("\ncommand_templates 表创建完成!")
        
    finally:
        connection.close()


def create_command_history_table():
    """
    创建command_history表
    """
    print("\n正在创建 command_history 表...")
    
    connection = engine.connect()
    try:
        # 检查 command_history 表是否存在
        result = connection.execute(text("SHOW TABLES LIKE 'command_history'"))
        if not result.fetchone():
            print("创建 command_history 表...")
            connection.execute(text("""
                CREATE TABLE command_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id INT NOT NULL,
                    command TEXT NOT NULL,
                    output TEXT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT NULL,
                    executed_by VARCHAR(100) NULL,
                    execution_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    duration FLOAT NULL,
                    INDEX idx_device_id (device_id),
                    INDEX idx_execution_time (execution_time),
                    INDEX idx_success (success),
                    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
            """))
            print("  ✓ command_history 表已创建")
        else:
            print("  ✓ command_history 表已存在")
        
        # 提交事务
        connection.commit()
        print("\ncommand_history 表创建完成!")
        
    finally:
        connection.close()


if __name__ == "__main__":
    update_configurations_table()
    create_git_configs_table()
    create_command_templates_table()
    create_command_history_table()
    print("\n所有数据库更新操作已完成!")
