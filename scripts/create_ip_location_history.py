#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IP 定位历史表创建脚本

功能：
1. 创建 ip_location_history 表用于存储下线 IP 历史记录
2. 支持 30 天数据保留
3. 支持事务回滚

使用方式：
    python scripts/create_ip_location_history.py [--dry-run] [--drop]
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


class IPLocationHistoryCreator:
    """IP 定位历史表创建类"""

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

    def check_table_exists(self) -> bool:
        """检查历史表是否已存在"""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.tables
                WHERE table_schema = %s AND table_name = 'ip_location_history'
            """, (self.db_config['database'],))
            return cursor.fetchone()['cnt'] > 0

    def create_table(self):
        """创建历史表"""
        print("\n=== 创建 ip_location_history 表 ===")

        if self.check_table_exists():
            print("表 ip_location_history 已存在")
            return True

        create_sql = """
        CREATE TABLE ip_location_history (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
            ip_address VARCHAR(50) NOT NULL COMMENT 'IP地址',
            mac_address VARCHAR(17) NOT NULL COMMENT 'MAC地址',

            -- ARP 来源设备信息（冗余）
            arp_source_device_id INT COMMENT 'ARP来源设备ID',
            arp_device_hostname VARCHAR(255) COMMENT 'ARP来源设备主机名',
            arp_device_ip VARCHAR(50) COMMENT 'ARP来源设备IP',
            arp_device_location VARCHAR(255) COMMENT 'ARP来源设备位置',

            -- MAC 命中设备信息（冗余）
            mac_hit_device_id INT COMMENT 'MAC命中设备ID',
            mac_device_hostname VARCHAR(255) COMMENT 'MAC命中设备主机名',
            mac_device_ip VARCHAR(50) COMMENT 'MAC命中设备IP',
            mac_device_location VARCHAR(255) COMMENT 'MAC命中设备位置',

            -- 接入信息
            access_interface VARCHAR(100) COMMENT '接入接口',
            vlan_id INT COMMENT 'VLAN ID',

            -- 定位置信度
            confidence DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '置信度',
            is_uplink TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否上行链路',
            is_core_switch TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否核心交换机',
            match_type VARCHAR(20) NOT NULL COMMENT '匹配类型',

            -- 时间信息
            first_seen DATETIME NOT NULL COMMENT '首次发现时间',
            last_seen DATETIME NOT NULL COMMENT '最后发现时间',
            archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '归档时间',

            -- 索引
            INDEX idx_history_ip (ip_address),
            INDEX idx_history_mac (mac_address),
            INDEX idx_history_archived (archived_at),
            INDEX idx_history_device (mac_hit_device_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IP定位历史表（保留30天）'
        """

        if self.dry_run:
            print(f"[DRY-RUN] 将执行 SQL:\n{create_sql}")
            return True

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_sql)
            self.connection.commit()
            print("表 ip_location_history 创建成功")
            return True
        except MySQLError as e:
            self.connection.rollback()
            print(f"创建表失败: {e}")
            return False

    def drop_table(self):
        """删除历史表"""
        print("\n=== 删除 ip_location_history 表 ===")

        if self.dry_run:
            print("[DRY-RUN] 将执行: DROP TABLE IF EXISTS ip_location_history")
            return True

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS ip_location_history")
            self.connection.commit()
            print("表 ip_location_history 已删除")
            return True
        except MySQLError as e:
            self.connection.rollback()
            print(f"删除表失败: {e}")
            return False

    def verify(self):
        """验证表创建结果"""
        print("\n=== 验证表结构 ===")

        with self.connection.cursor() as cursor:
            cursor.execute("DESCRIBE ip_location_history")
            columns = cursor.fetchall()
            print(f"表字段数: {len(columns)}")
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']}")

        return True

    def run(self, drop: bool = False):
        """执行创建"""
        print(f"\n{'='*60}")
        print(f"IP 定位历史表创建脚本")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"模式: {'DRY-RUN (仅预览)' if self.dry_run else '正式执行'}")
        print(f"{'='*60}")

        try:
            self.connect()

            if drop:
                return self.drop_table()

            success = self.create_table()
            if success:
                self.verify()

            return success

        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(description='IP 定位历史表创建脚本')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际执行')
    parser.add_argument('--drop', action='store_true', help='删除表')
    args = parser.parse_args()

    creator = IPLocationHistoryCreator(dry_run=args.dry_run)
    success = creator.run(drop=args.drop)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()