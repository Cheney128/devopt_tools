#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IP 定位表迁移脚本 - 添加冗余字段

功能：
1. 为 ip_location_current 表添加设备冗余字段
2. 添加索引优化查询性能
3. 支持事务回滚

使用方式：
    python scripts/migrate_ip_location_add_columns.py [--dry-run] [--rollback]
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from pymysql import MySQLError
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class IPLocationMigration:
    """IP 定位表迁移类"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.connection = None
        self.db_config = {
            'host': os.getenv('DB_HOST', '10.21.65.20'),
            'port': int(os.getenv('DB_PORT', '3307')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '1qaz@WSX'),
            'database': os.getenv('DB_NAME', 'switch_manage'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    def connect(self):
        """建立数据库连接"""
        print(f"连接数据库 {self.db_config['host']}:{self.db_config['port']}...")
        self.connection = pymysql.connect(**self.db_config)
        print("数据库连接成功")

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")

    def check_columns_exist(self) -> dict:
        """检查冗余字段是否已存在"""
        with self.connection.cursor() as cursor:
            cursor.execute("DESCRIBE ip_location_current")
            columns = {row['Field']: row for row in cursor.fetchall()}

        required_columns = [
            'arp_device_hostname', 'arp_device_ip', 'arp_device_location',
            'mac_device_hostname', 'mac_device_ip', 'mac_device_location'
        ]

        result = {}
        for col in required_columns:
            result[col] = col in columns

        return result

    def add_columns(self):
        """添加冗余字段"""
        print("\n=== 添加冗余字段 ===")

        columns_exist = self.check_columns_exist()
        print(f"当前字段状态: {columns_exist}")

        alter_statements = []

        # ARP 来源设备冗余字段
        if not columns_exist.get('arp_device_hostname'):
            alter_statements.append(
                "ADD COLUMN arp_device_hostname VARCHAR(255) COMMENT 'ARP来源设备主机名' AFTER arp_source_device_id"
            )

        if not columns_exist.get('arp_device_ip'):
            alter_statements.append(
                "ADD COLUMN arp_device_ip VARCHAR(50) COMMENT 'ARP来源设备IP' AFTER arp_device_hostname"
            )

        if not columns_exist.get('arp_device_location'):
            alter_statements.append(
                "ADD COLUMN arp_device_location VARCHAR(255) COMMENT 'ARP来源设备位置' AFTER arp_device_ip"
            )

        # MAC 命中设备冗余字段
        if not columns_exist.get('mac_device_hostname'):
            alter_statements.append(
                "ADD COLUMN mac_device_hostname VARCHAR(255) COMMENT 'MAC命中设备主机名' AFTER mac_hit_device_id"
            )

        if not columns_exist.get('mac_device_ip'):
            alter_statements.append(
                "ADD COLUMN mac_device_ip VARCHAR(50) COMMENT 'MAC命中设备IP' AFTER mac_device_hostname"
            )

        if not columns_exist.get('mac_device_location'):
            alter_statements.append(
                "ADD COLUMN mac_device_location VARCHAR(255) COMMENT 'MAC命中设备位置' AFTER mac_device_ip"
            )

        if not alter_statements:
            print("所有冗余字段已存在，跳过添加")
            return True

        sql = f"ALTER TABLE ip_location_current {', '.join(alter_statements)}"

        if self.dry_run:
            print(f"[DRY-RUN] 将执行 SQL:\n{sql}")
            return True

        try:
            with self.connection.cursor() as cursor:
                print(f"执行 SQL: {sql}")
                cursor.execute(sql)
            self.connection.commit()
            print(f"成功添加 {len(alter_statements)} 个冗余字段")
            return True
        except MySQLError as e:
            self.connection.rollback()
            print(f"添加字段失败: {e}")
            return False

    def add_indexes(self):
        """添加索引"""
        print("\n=== 添加索引 ===")

        indexes = [
            ("idx_ip_location_status", "batch_status"),
            ("idx_ip_location_last_seen", "last_seen"),
            ("idx_ip_location_confidence", "confidence"),
        ]

        # 检查现有索引
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW INDEX FROM ip_location_current")
            existing = {row['Key_name'] for row in cursor.fetchall()}

        added = 0
        for idx_name, idx_column in indexes:
            if idx_name in existing:
                print(f"索引 {idx_name} 已存在，跳过")
                continue

            sql = f"CREATE INDEX {idx_name} ON ip_location_current({idx_column})"

            if self.dry_run:
                print(f"[DRY-RUN] 将执行 SQL: {sql}")
                continue

            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(sql)
                self.connection.commit()
                print(f"已创建索引 {idx_name}")
                added += 1
            except MySQLError as e:
                print(f"创建索引 {idx_name} 失败: {e}")

        print(f"共创建 {added} 个索引")
        return True

    def rollback(self):
        """回滚：删除新增字段"""
        print("\n=== 回滚：删除冗余字段 ===")

        columns_to_drop = [
            'arp_device_hostname', 'arp_device_ip', 'arp_device_location',
            'mac_device_hostname', 'mac_device_ip', 'mac_device_location'
        ]

        if self.dry_run:
            print(f"[DRY-RUN] 将删除字段: {columns_to_drop}")
            return True

        try:
            with self.connection.cursor() as cursor:
                for col in columns_to_drop:
                    sql = f"ALTER TABLE ip_location_current DROP COLUMN IF EXISTS {col}"
                    print(f"执行: {sql}")
                    cursor.execute(sql)
            self.connection.commit()
            print("回滚完成")
            return True
        except MySQLError as e:
            self.connection.rollback()
            print(f"回滚失败: {e}")
            return False

    def verify(self):
        """验证迁移结果"""
        print("\n=== 验证迁移结果 ===")

        with self.connection.cursor() as cursor:
            # 检查表结构
            cursor.execute("DESCRIBE ip_location_current")
            columns = [row['Field'] for row in cursor.fetchall()]
            print(f"当前表字段数: {len(columns)}")

            # 检查记录数
            cursor.execute("SELECT COUNT(*) as cnt FROM ip_location_current")
            count = cursor.fetchone()['cnt']
            print(f"当前记录数: {count}")

            # 检查冗余字段是否有数据
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM ip_location_current
                WHERE arp_device_hostname IS NOT NULL
            """)
            filled = cursor.fetchone()['cnt']
            print(f"冗余字段已填充记录数: {filled}")

        return True

    def run(self, rollback: bool = False):
        """执行迁移"""
        print(f"\n{'='*60}")
        print(f"IP 定位表迁移脚本")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"模式: {'DRY-RUN (仅预览)' if self.dry_run else '正式执行'}")
        print(f"{'='*60}")

        try:
            self.connect()

            if rollback:
                return self.rollback()

            success = self.add_columns()
            if success:
                self.add_indexes()
                self.verify()

            return success

        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description='IP 定位表迁移脚本')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际执行')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移')
    args = parser.parse_args()

    migration = IPLocationMigration(dry_run=args.dry_run)
    success = migration.run(rollback=args.rollback)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()