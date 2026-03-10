#!/usr/bin/env python3
"""
数据库回滚脚本
用于在迁移失败时恢复数据库到之前的状态

使用方法:
1. 列出可用的备份: python3 /unified-app/scripts/db_rollback.py --list
2. 回滚到指定备份: python3 /unified-app/scripts/db_rollback.py --backup /backups/db_backup_20240223_120000.sql
3. 回滚到最新的备份: python3 /unified-app/scripts/db_rollback.py --latest

注意:
- 回滚会丢失备份后产生的数据变更
- 建议在回滚前再次备份当前数据库
"""

import sys
import os
import argparse
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


def list_backups():
    """列出所有可用的备份文件"""
    backup_dir = Path('/backups')
    
    if not backup_dir.exists():
        logger.error(f"备份目录不存在: {backup_dir}")
        return []
    
    # 查找所有备份文件
    backups = sorted(backup_dir.glob('db_backup_*.sql'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not backups:
        logger.info("没有找到备份文件")
        return []
    
    logger.info("可用的备份文件:")
    logger.info("-" * 80)
    
    for i, backup in enumerate(backups[:10], 1):  # 只显示最近的10个
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"{i}. {backup.name}")
        logger.info(f"   大小: {size_mb:.2f} MB")
        logger.info(f"   时间: {mtime}")
        logger.info("")
    
    return backups


def get_latest_backup():
    """获取最新的备份文件"""
    backup_dir = Path('/backups')
    
    if not backup_dir.exists():
        return None
    
    backups = sorted(backup_dir.glob('db_backup_*.sql'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    return backups[0] if backups else None


def backup_current_database():
    """在回滚前备份当前数据库"""
    logger.info("=" * 60)
    logger.info("步骤 1/3: 备份当前数据库")
    logger.info("=" * 60)
    
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        logger.error("错误: DATABASE_URL 环境变量未设置")
        return False
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url.replace('mysql+pymysql', 'mysql'))
        
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 3306
        database = parsed.path.lstrip('/')
        
        backup_dir = Path('/backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"db_pre_rollback_backup_{timestamp}.sql"
        
        cmd = [
            'mysqldump',
            '-h', host,
            '-P', str(port),
            '-u', user,
            f'-p{password}',
            '--single-transaction',
            database
        ]
        
        logger.info(f"正在备份当前数据库到: {backup_file}")
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            logger.info(f"✓ 当前数据库备份成功: {backup_file}")
            return str(backup_file)
        else:
            logger.error(f"✗ 当前数据库备份失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 备份过程出错: {str(e)}")
        return False


def restore_database(backup_file):
    """从备份文件恢复数据库"""
    logger.info("=" * 60)
    logger.info("步骤 2/3: 恢复数据库")
    logger.info("=" * 60)
    
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        logger.error("错误: DATABASE_URL 环境变量未设置")
        return False
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url.replace('mysql+pymysql', 'mysql'))
        
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 3306
        database = parsed.path.lstrip('/')
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error(f"备份文件不存在: {backup_file}")
            return False
        
        logger.info(f"正在从备份恢复数据库: {backup_file}")
        
        # 构建恢复命令
        cmd = [
            'mysql',
            '-h', host,
            '-P', str(port),
            '-u', user,
            f'-p{password}',
            database
        ]
        
        with open(backup_path, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            logger.info("✓ 数据库恢复成功")
            return True
        else:
            logger.error(f"✗ 数据库恢复失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 恢复过程出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_restore():
    """验证恢复结果"""
    logger.info("=" * 60)
    logger.info("步骤 3/3: 验证恢复结果")
    logger.info("=" * 60)
    
    try:
        from sqlalchemy import create_engine, inspect
        
        db_url = os.environ.get('DATABASE_URL')
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        # 检查表是否存在
        tables = inspector.get_table_names()
        
        if 'backup_schedules' not in tables:
            logger.error("✗ 验证失败: backup_schedules 表不存在")
            return False
        
        logger.info(f"✓ 数据库表正常，共 {len(tables)} 个表")
        
        # 检查备份计划数量
        from sqlalchemy.orm import sessionmaker
        from app.models.models import BackupSchedule
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            count = db.query(BackupSchedule).count()
            logger.info(f"✓ 备份计划数量: {count}")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 验证过程出错: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数据库回滚工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有备份
  python3 db_rollback.py --list
  
  # 回滚到最新备份
  python3 db_rollback.py --latest
  
  # 回滚到指定备份
  python3 db_rollback.py --backup /backups/db_backup_20240223_120000.sql
        """
    )
    
    parser.add_argument('--list', action='store_true', help='列出所有可用的备份')
    parser.add_argument('--latest', action='store_true', help='回滚到最新的备份')
    parser.add_argument('--backup', type=str, help='指定要恢复的备份文件路径')
    parser.add_argument('--force', action='store_true', help='跳过确认提示')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if not any([args.list, args.latest, args.backup]):
        parser.print_help()
        return 0
    
    # 列出备份
    if args.list:
        list_backups()
        return 0
    
    # 获取要恢复的备份文件
    backup_file = None
    
    if args.latest:
        backup_file = get_latest_backup()
        if not backup_file:
            logger.error("没有找到可用的备份文件")
            return 1
        logger.info(f"将使用最新的备份: {backup_file}")
    elif args.backup:
        backup_file = args.backup
    
    if not backup_file:
        logger.error("请指定要恢复的备份文件")
        return 1
    
    # 确认提示
    if not args.force:
        logger.warning("⚠ 警告: 数据库回滚将丢失备份后产生的所有数据变更!")
        response = input("是否继续? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("操作已取消")
            return 0
    
    # 执行回滚
    logger.info("=" * 60)
    logger.info("开始数据库回滚")
    logger.info("=" * 60)
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1: 备份当前数据库
    current_backup = backup_current_database()
    if not current_backup:
        logger.error("当前数据库备份失败，是否继续?")
        if not args.force:
            response = input("是否继续? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("操作已取消")
                return 0
    
    # 步骤2: 恢复数据库
    if not restore_database(backup_file):
        logger.error("=" * 60)
        logger.error("数据库恢复失败!")
        logger.error("=" * 60)
        if current_backup:
            logger.info(f"可以尝试从当前备份恢复: {current_backup}")
        return 1
    
    # 步骤3: 验证恢复
    if not verify_restore():
        logger.error("=" * 60)
        logger.error("恢复验证失败!")
        logger.error("=" * 60)
        return 1
    
    # 完成
    logger.info("=" * 60)
    logger.info("数据库回滚成功完成!")
    logger.info("=" * 60)
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if current_backup:
        logger.info(f"当前数据库已备份到: {current_backup}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
