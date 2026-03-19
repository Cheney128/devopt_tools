"""
IP 定位功能数据库迁移脚本
创建 arp_entries 表，更新 mac_addresses 表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings
from urllib.parse import quote_plus, urlparse, urlunparse


def migrate():
    # Parse the URL properly to handle special characters in password
    parsed = urlparse(settings.DATABASE_URL)
    if parsed.password:
        # Reconstruct the URL with encoded password
        encoded_password = quote_plus(parsed.password)
        netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        database_url = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    else:
        database_url = settings.DATABASE_URL

    engine = create_engine(database_url)

    # Use begin() for transactional context
    with engine.begin() as conn:
        # 1. 创建 arp_entries 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS arp_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device_id INT NOT NULL,
                ip_address VARCHAR(50) NOT NULL,
                mac_address VARCHAR(17) NOT NULL,
                vlan_id INT,
                interface VARCHAR(100),
                arp_type VARCHAR(20),
                age_minutes INT,
                last_seen DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_arp_device_id (device_id),
                INDEX idx_arp_ip_address (ip_address),
                INDEX idx_arp_mac_address (mac_address),
                INDEX idx_arp_vlan_id (vlan_id),
                INDEX idx_arp_last_seen (last_seen),
                INDEX idx_arp_ip_last_seen (ip_address, last_seen),
                INDEX idx_arp_mac_last_seen (mac_address, last_seen),
                INDEX idx_arp_device_last_seen (device_id, last_seen),
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

        # 2. 为 mac_addresses 表新增字段（如果不存在）
        # 检查字段是否存在，不存在则添加
        result = conn.execute(text("""
            SHOW COLUMNS FROM mac_addresses LIKE 'is_trunk'
        """))
        if not result.fetchone():
            conn.execute(text("""
                ALTER TABLE mac_addresses
                ADD COLUMN is_trunk BOOLEAN AFTER address_type,
                ADD COLUMN learned_from VARCHAR(100) AFTER is_trunk,
                ADD COLUMN aging_time INT AFTER learned_from,
                ADD INDEX idx_mac_mac_last_seen (mac_address, last_seen),
                ADD INDEX idx_mac_device_interface (device_id, interface, last_seen)
            """))

        print("IP 定位数据库迁移完成")


if __name__ == "__main__":
    migrate()
