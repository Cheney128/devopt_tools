# IP 定位 Ver3 数据采集链路修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补充完整 IP 定位 Ver3 的数据采集链路，使 arp_current 和 mac_current 表能够正常写入数据，从而让 IP 定位预计算能够产出结果。

**Architecture:** 
- 新增 ARP 采集端点，采集结果直接写入 arp_current 表
- 修改现有 MAC 采集端点，改为写入 mac_current 表（不再写入旧表 mac_addresses）
- 新增批量采集调度器，定时触发 ARP+MAC 采集并自动触发 IP 定位计算
- 所有采集操作使用事务保护，确保采集失败时不污染数据

**Tech Stack:** FastAPI, SQLAlchemy, PyMySQL, APScheduler

---

## 文件结构概览

### 新增文件
- `app/models/ip_location_current.py` - ARP 和 MAC 当前数据表模型定义
- `app/api/endpoints/arp_collection.py` - ARP 采集 API 端点
- `app/services/arp_mac_scheduler.py` - ARP+MAC 批量采集调度器
- `tests/unit/test_arp_collection.py` - ARP 采集单元测试
- `tests/unit/test_mac_collection.py` - MAC 采集单元测试
- `tests/integration/test_ip_location_collection_flow.py` - 完整数据流集成测试

### 修改文件
- `app/api/endpoints/device_collection.py` - 修改 collect_mac_table 端点，改为写入 mac_current 表
- `app/models/__init__.py` - 导出新的模型类
- `app/main.py` - 注册新的 API 路由

---

## 前置条件

### 数据库表结构

需要确认以下表已创建（通过 SQLAlchemy 自动创建或手动迁移）：

```sql
-- arp_current 表
CREATE TABLE IF NOT EXISTS arp_current (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    vlan_id INT,
    arp_interface VARCHAR(100),
    last_seen DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device (device_id),
    INDEX idx_ip_mac (ip_address, mac_address),
    INDEX idx_last_seen (last_seen)
);

-- mac_current 表
CREATE TABLE IF NOT EXISTS mac_current (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    mac_address VARCHAR(17) NOT NULL,
    vlan_id INT,
    mac_interface VARCHAR(100) NOT NULL,
    is_trunk BOOLEAN DEFAULT FALSE,
    interface_description VARCHAR(255),
    last_seen DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device (device_id),
    INDEX idx_mac (mac_address),
    INDEX idx_last_seen (last_seen)
);
```

---

## 任务分解

### Task 1: 创建 ARP 和 MAC 当前数据表模型

**Files:**
- Create: `app/models/ip_location_current.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1: 创建模型文件**

```python
# -*- coding: utf-8 -*-
"""
IP 定位当前数据表模型

包含：
- ARPEntry: ARP 当前数据表
- MACAddressCurrent: MAC 当前数据表
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.models import Base


class ARPEntry(Base):
    """
    ARP 当前数据表

    存储设备最新的 ARP 表项，用于 IP 定位预计算。
    """
    __tablename__ = "arp_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment='设备 ID')
    ip_address = Column(String(50), nullable=False, index=True, comment='IP 地址')
    mac_address = Column(String(17), nullable=False, comment='MAC 地址')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')
    arp_interface = Column(String(100), nullable=True, comment='ARP 接口')
    last_seen = Column(DateTime, nullable=True, index=True, comment='最后发现时间')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')

    # 关联关系
    device = relationship("Device", back_populates="arp_entries")

    # 复合索引
    __table_args__ = (
        Index('idx_ip_mac', 'ip_address', 'mac_address'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'vlan_id': self.vlan_id,
            'arp_interface': self.arp_interface,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }


class MACAddressCurrent(Base):
    """
    MAC 当前数据表

    存储设备最新的 MAC 地址表，用于 IP 定位预计算。
    """
    __tablename__ = "mac_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True, comment='设备 ID')
    mac_address = Column(String(17), nullable=False, index=True, comment='MAC 地址')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')
    mac_interface = Column(String(100), nullable=False, comment='MAC 接口')
    is_trunk = Column(Boolean, nullable=False, default=False, comment='是否 Trunk 接口')
    interface_description = Column(String(255), nullable=True, comment='接口描述')
    last_seen = Column(DateTime, nullable=True, index=True, comment='最后发现时间')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')

    # 关联关系
    device = relationship("Device", back_populates="mac_entries_current")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'mac_address': self.mac_address,
            'vlan_id': self.vlan_id,
            'mac_interface': self.mac_interface,
            'is_trunk': self.is_trunk,
            'interface_description': self.interface_description,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }
```

- [ ] **Step 2: 在 Device 模型中添加关联关系**

Modify `app/models/models.py`:

```python
# 在 Device 类中添加关联关系
class Device(Base):
    # ... 现有字段 ...
    
    # 新增关联关系
    arp_entries = relationship("ARPEntry", back_populates="device", cascade="all, delete-orphan")
    mac_entries_current = relationship("MACAddressCurrent", back_populates="device", cascade="all, delete-orphan")
```

- [ ] **Step 3: 更新 models/__init__.py 导出**

```python
from app.models.ip_location_current import ARPEntry, MACAddressCurrent

__all__ = [
    'Base', 'get_db', 'engine', 'SessionLocal',
    'User', 'Role', 'Permission', 'CaptchaRecord',
    'user_roles', 'role_permissions',
    'IPLocationCurrent', 'IPLocationHistory', 'IPLocationSettings',
    'ARPEntry', 'MACAddressCurrent',
]
```

- [ ] **Step 4: 运行数据库迁移**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
python -c "from app.models import engine, Base; Base.metadata.create_all(bind=engine)"
```

Expected: 无错误输出，arp_current 和 mac_current 表创建成功

- [ ] **Step 5: 验证表已创建**

```bash
mysql -u root -p -e "USE switch_manage; SHOW TABLES LIKE '%current%';"
```

Expected: 显示 arp_current 和 mac_current 表

- [ ] **Step 6: 提交**

```bash
git add app/models/ip_location_current.py app/models/models.py app/models/__init__.py
git commit -m "feat: add ARP and MAC current table models for IP location v3"
```

---

### Task 2: 实现 ARP 采集端点

**Files:**
- Create: `app/api/endpoints/arp_collection.py`
- Modify: `app/api/endpoints/__init__.py`
- Test: `tests/unit/test_arp_collection.py`

- [ ] **Step 1: 编写失败的测试**

```python
# tests/unit/test_arp_collection.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_collect_arp_table_single_device():
    """测试单个设备的 ARP 采集"""
    response = client.post("/api/arp-collection/1/collect")
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'arp_entries_count' in data['data']

def test_collect_arp_table_batch():
    """测试批量 ARP 采集"""
    response = client.post("/api/arp-collection/batch/collect", json={"device_ids": [1, 2, 3]})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
pytest tests/unit/test_arp_collection.py -v
```

Expected: FAIL with "404 Not Found" (端点不存在)

- [ ] **Step 3: 实现 ARP 采集端点**

```python
# -*- coding: utf-8 -*-
"""
ARP 表采集 API 路由

提供 ARP 表采集功能，采集结果写入 arp_current 表。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import get_db
from app.models.models import Device
from app.models.ip_location_current import ARPEntry
from app.services.netmiko_service import netmiko_service, get_netmiko_service
from app.schemas.schemas import DeviceCollectionResult

# 创建路由器
router = APIRouter(prefix="/api/arp-collection", tags=["ARP 采集"])


@router.post("/{device_id}/collect", response_model=DeviceCollectionResult)
async def collect_arp_table(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集单个设备的 ARP 表
    
    Args:
        device_id: 设备 ID
        db: 数据库会话
        
    Returns:
        采集结果
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    try:
        # 采集 ARP 表
        arp_table = await netmiko_service.collect_arp_table(device)
        
        if not arp_table:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect ARP table for device {device.hostname}",
                data=None
            )
        
        # 清空现有 ARP 数据（当前设备）
        db.query(ARPEntry).filter(ARPEntry.device_id == device_id).delete()
        
        # 保存新的 ARP 数据
        for arp_entry in arp_table:
            entry = ARPEntry(
                device_id=device_id,
                ip_address=arp_entry['ip_address'],
                mac_address=arp_entry['mac_address'],
                vlan_id=arp_entry.get('vlan_id'),
                arp_interface=arp_entry.get('interface'),
                last_seen=datetime.now()
            )
            db.add(entry)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"ARP table collected successfully for device {device.hostname}",
            data={"arp_entries_count": len(arp_table)}
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting ARP table: {str(e)}",
            data=None
        )


@router.post("/batch/collect", response_model=DeviceCollectionResult)
async def batch_collect_arp(
    device_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    批量采集 ARP 表
    
    Args:
        device_ids: 设备 ID 列表
        db: 数据库会话
        
    Returns:
        批量采集结果
    """
    # 获取设备列表
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    
    if not devices:
        return DeviceCollectionResult(
            success=False,
            message="No valid devices found",
            data=None
        )
    
    try:
        # 批量采集
        results = await netmiko_service.batch_collect_arp_table(devices)
        
        # 处理采集结果并保存到数据库
        total_entries = 0
        for detail in results['details']:
            if detail['success'] and 'arp_table' in detail['data']:
                device_id = detail['device_id']
                arp_table = detail['data']['arp_table']
                
                # 清空现有 ARP 数据
                db.query(ARPEntry).filter(ARPEntry.device_id == device_id).delete()
                
                # 保存新的 ARP 数据
                for arp_entry in arp_table:
                    entry = ARPEntry(
                        device_id=device_id,
                        ip_address=arp_entry['ip_address'],
                        mac_address=arp_entry['mac_address'],
                        vlan_id=arp_entry.get('vlan_id'),
                        arp_interface=arp_entry.get('interface'),
                        last_seen=datetime.now()
                    )
                    db.add(entry)
                
                total_entries += len(arp_table)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Batch ARP collection completed: {results['success']} success, {results['failed']} failed",
            data={
                "total_arp_entries": total_entries,
                "details": results['details']
            }
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error in batch ARP collection: {str(e)}",
            data=None
        )
```

- [ ] **Step 4: 在 netmiko_service.py 中添加 ARP 采集方法**

Modify `app/services/netmiko_service.py`:

```python
async def collect_arp_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    """
    采集设备 ARP 表

    Args:
        device: 设备对象

    Returns:
        ARP 表条目列表，每个条目包含：ip_address, mac_address, vlan_id, interface
    """
    try:
        connection = await self._get_connection(device)
        
        # 根据设备厂商选择命令
        if device.vendor == "huawei":
            command = "display arp"
        elif device.vendor == "h3c":
            command = "display arp"
        elif device.vendor == "cisco":
            command = "show ip arp"
        else:
            command = "display arp"  # 默认使用华为命令
        
        output = await connection.execute(command)
        
        # 解析 ARP 表
        arp_entries = self._parse_arp_table(output, device.vendor)
        
        return arp_entries
        
    except Exception as e:
        logger.error(f"Error collecting ARP table from {device.hostname}: {str(e)}")
        return None


async def batch_collect_arp_table(self, devices: List[Device]) -> Dict[str, Any]:
    """
    批量采集 ARP 表

    Args:
        devices: 设备列表

    Returns:
        采集结果统计
    """
    tasks = [self.collect_arp_table(device) for device in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success = 0
    failed = 0
    details = []
    
    for device, result in zip(devices, results):
        if isinstance(result, Exception):
            failed += 1
            details.append({
                'device_id': device.id,
                'success': False,
                'error': str(result)
            })
        elif result is not None:
            success += 1
            details.append({
                'device_id': device.id,
                'success': True,
                'data': {'arp_table': result}
            })
        else:
            failed += 1
            details.append({
                'device_id': device.id,
                'success': False,
                'error': 'Empty result'
            })
    
    return {
        'success': success,
        'failed': failed,
        'details': details
    }


def _parse_arp_table(self, output: str, vendor: str) -> List[Dict[str, Any]]:
    """
    解析 ARP 表输出

    Args:
        output: 命令输出
        vendor: 设备厂商

    Returns:
        ARP 条目列表
    """
    arp_entries = []
    lines = output.strip().split('\n')
    
    # 跳过表头
    start_index = 0
    for i, line in enumerate(lines):
        if 'IP' in line and 'MAC' in line:
            start_index = i + 1
            break
    
    for line in lines[start_index:]:
        if not line.strip():
            continue
        
        # 华为/H3C 格式：IP 地址  MAC 地址     VLAN  接口
        # Cisco 格式：Protocol  Address  Age  MAC Addr  Interface
        parts = line.split()
        if len(parts) >= 4:
            try:
                if vendor in ['huawei', 'h3c']:
                    entry = {
                        'ip_address': parts[0],
                        'mac_address': parts[1].upper(),
                        'vlan_id': int(parts[2]) if parts[2].isdigit() else None,
                        'interface': parts[3] if len(parts) > 3 else None
                    }
                else:  # cisco
                    entry = {
                        'ip_address': parts[1],
                        'mac_address': parts[3].upper(),
                        'vlan_id': None,
                        'interface': parts[4] if len(parts) > 4 else None
                    }
                arp_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return arp_entries
```

- [ ] **Step 5: 注册 API 路由**

Modify `app/api/endpoints/__init__.py`:

```python
from .arp_collection import router as arp_collection_router

__all__ = [
    # ... existing routers ...
    'arp_collection_router',
]
```

Modify `app/main.py`:

```python
from app.api.endpoints import arp_collection_router

app.include_router(arp_collection_router)
```

- [ ] **Step 6: 运行测试验证通过**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
pytest tests/unit/test_arp_collection.py -v
```

Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add app/api/endpoints/arp_collection.py app/api/endpoints/__init__.py app/main.py app/services/netmiko_service.py tests/unit/test_arp_collection.py
git commit -m "feat: add ARP collection API endpoints"
```

---

### Task 3: 修改 MAC 采集端点

**Files:**
- Modify: `app/api/endpoints/device_collection.py`
- Test: `tests/unit/test_mac_collection.py`

- [ ] **Step 1: 编写失败的测试**

```python
# tests/unit/test_mac_collection.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import get_db
from app.models.ip_location_current import MACAddressCurrent

client = TestClient(app)

def test_collect_mac_table_writes_to_current():
    """测试 MAC 采集写入 mac_current 表而不是旧表"""
    response = client.post("/api/device-collection/1/collect/mac-table")
    assert response.status_code == 200
    
    # 验证数据写入 mac_current 表
    db = next(get_db())
    current_entries = db.query(MACAddressCurrent).filter(
        MACAddressCurrent.device_id == 1
    ).count()
    assert current_entries > 0
```

- [ ] **Step 2: 修改 device_collection.py**

Modify `app/api/endpoints/device_collection.py`:

```python
from app.models.ip_location_current import MACAddressCurrent

# ... existing code ...

@router.post("/{device_id}/collect/mac-table", response_model=DeviceCollectionResult)
async def collect_mac_table(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集 MAC 地址表
    
    Args:
        device_id: 设备 ID
        db: 数据库会话
        
    Returns:
        采集结果
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    try:
        # 采集 MAC 地址表
        mac_table = await netmiko_service.collect_mac_table(device)
        
        if not mac_table:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect MAC table for device {device.hostname}",
                data=None
            )
        
        # 清空现有 MAC 地址表（mac_current 表）
        db.query(MACAddressCurrent).filter(MACAddressCurrent.device_id == device_id).delete()
        
        # 保存新的 MAC 地址表到 mac_current
        for mac_entry in mac_table:
            mac_address = MACAddressCurrent(
                device_id=device_id,
                mac_address=mac_entry['mac_address'],
                vlan_id=mac_entry.get('vlan_id'),
                mac_interface=mac_entry['interface'],
                is_trunk=mac_entry.get('is_trunk', False),
                interface_description=mac_entry.get('description'),
                last_seen=datetime.now()
            )
            db.add(mac_address)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"MAC table collected successfully for device {device.hostname}",
            data={"mac_entries_count": len(mac_table)}
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting MAC table: {str(e)}",
            data=None
        )
```

- [ ] **Step 3: 修改批量采集端点**

Modify the batch_collect endpoint in the same file:

```python
# 保存 MAC 地址表部分改为：
if 'mac_table' in detail['data']:
    mac_table = detail['data']['mac_table']
    # 清空现有 MAC 地址表（mac_current 表）
    db.query(MACAddressCurrent).filter(MACAddressCurrent.device_id == device_id).delete()
    # 保存新的 MAC 地址表到 mac_current
    for mac_entry in mac_table:
        mac_address = MACAddressCurrent(
            device_id=device_id,
            mac_address=mac_entry['mac_address'],
            vlan_id=mac_entry.get('vlan_id'),
            mac_interface=mac_entry['interface'],
            is_trunk=mac_entry.get('is_trunk', False),
            interface_description=mac_entry.get('description'),
            last_seen=datetime.now()
        )
        db.add(mac_address)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
pytest tests/unit/test_mac_collection.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add app/api/endpoints/device_collection.py tests/unit/test_mac_collection.py
git commit -m "feat: modify MAC collection to write to mac_current table"
```

---

### Task 4: 新增批量采集调度器

**Files:**
- Create: `app/services/arp_mac_scheduler.py`
- Modify: `app/services/ip_location_scheduler.py`

- [ ] **Step 1: 创建 ARP+MAC 批量采集调度器**

```python
# -*- coding: utf-8 -*-
"""
ARP+MAC 批量采集调度器

功能：
1. 定时批量采集所有设备的 ARP 和 MAC 表
2. 采集完成后自动触发 IP 定位预计算
3. 支持事务保护，采集失败时不污染数据
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.models import Device
from app.models.ip_location_current import ARPEntry, MACAddressCurrent
from app.services.netmiko_service import get_netmiko_service
from app.services.ip_location_calculator import get_ip_location_calculator

logger = logging.getLogger(__name__)


class ARPMACScheduler:
    """
    ARP+MAC 批量采集调度器
    """

    def __init__(self, db: Session):
        """
        初始化调度器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.netmiko = get_netmiko_service(db)

    def collect_all_devices(self) -> dict:
        """
        采集所有活跃设备的 ARP 和 MAC 表

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        logger.info(f"开始批量采集 ARP 和 MAC 表，时间：{start_time}")

        # 获取所有活跃设备
        devices = self.db.query(Device).filter(
            Device.status == 'active'
        ).all()

        if not devices:
            logger.warning("没有活跃设备需要采集")
            return {'success': 0, 'failed': 0, 'error': 'No active devices'}

        logger.info(f"共有 {len(devices)} 台设备需要采集")

        # 采集统计
        stats = {
            'arp_success': 0,
            'arp_failed': 0,
            'mac_success': 0,
            'mac_failed': 0,
            'total_arp_entries': 0,
            'total_mac_entries': 0,
            'devices': []
        }

        # 逐个设备采集
        for device in devices:
            device_stats = self._collect_device(device)
            stats['devices'].append(device_stats)
            
            if device_stats['arp_success']:
                stats['arp_success'] += 1
                stats['total_arp_entries'] += device_stats.get('arp_entries_count', 0)
            else:
                stats['arp_failed'] += 1
            
            if device_stats['mac_success']:
                stats['mac_success'] += 1
                stats['total_mac_entries'] += device_stats.get('mac_entries_count', 0)
            else:
                stats['mac_failed'] += 1

        # 记录总耗时
        end_time = datetime.now()
        stats['start_time'] = start_time.isoformat()
        stats['end_time'] = end_time.isoformat()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()

        logger.info(f"批量采集完成：{stats}")
        return stats

    def _collect_device(self, device: Device) -> dict:
        """
        采集单个设备的 ARP 和 MAC 表

        Args:
            device: 设备对象

        Returns:
            采集结果
        """
        device_stats = {
            'device_id': device.id,
            'device_hostname': device.hostname,
            'arp_success': False,
            'mac_success': False,
            'arp_entries_count': 0,
            'mac_entries_count': 0,
        }

        try:
            # 采集 ARP 表
            arp_table = self.netmiko.collect_arp_table(device)
            if arp_table:
                # 清空并保存
                self.db.query(ARPEntry).filter(
                    ARPEntry.device_id == device.id
                ).delete()
                
                for entry in arp_table:
                    arp_entry = ARPEntry(
                        device_id=device.id,
                        ip_address=entry['ip_address'],
                        mac_address=entry['mac_address'],
                        vlan_id=entry.get('vlan_id'),
                        arp_interface=entry.get('interface'),
                        last_seen=datetime.now()
                    )
                    self.db.add(arp_entry)
                
                device_stats['arp_success'] = True
                device_stats['arp_entries_count'] = len(arp_table)
                logger.info(f"设备 {device.hostname} ARP 采集成功：{len(arp_table)} 条")
            else:
                logger.warning(f"设备 {device.hostname} ARP 采集返回空结果")

            # 采集 MAC 表
            mac_table = self.netmiko.collect_mac_table(device)
            if mac_table:
                # 清空并保存
                self.db.query(MACAddressCurrent).filter(
                    MACAddressCurrent.device_id == device.id
                ).delete()
                
                for entry in mac_table:
                    mac_entry = MACAddressCurrent(
                        device_id=device.id,
                        mac_address=entry['mac_address'],
                        vlan_id=entry.get('vlan_id'),
                        mac_interface=entry['interface'],
                        is_trunk=entry.get('is_trunk', False),
                        interface_description=entry.get('description'),
                        last_seen=datetime.now()
                    )
                    self.db.add(mac_entry)
                
                device_stats['mac_success'] = True
                device_stats['mac_entries_count'] = len(mac_table)
                logger.info(f"设备 {device.hostname} MAC 采集成功：{len(mac_table)} 条")
            else:
                logger.warning(f"设备 {device.hostname} MAC 采集返回空结果")

            # 提交事务
            self.db.commit()

        except Exception as e:
            logger.error(f"设备 {device.hostname} 采集失败：{str(e)}")
            self.db.rollback()
            device_stats['error'] = str(e)

        return device_stats

    def collect_and_calculate(self) -> dict:
        """
        采集 ARP+MAC 并触发 IP 定位计算

        Returns:
            完整结果统计
        """
        logger.info("开始采集 + 计算流程")

        # 步骤 1: 采集 ARP 和 MAC
        collection_stats = self.collect_all_devices()

        if collection_stats.get('arp_success', 0) == 0:
            logger.error("ARP 采集全部失败，跳过 IP 定位计算")
            return {
                'collection': collection_stats,
                'calculation': {'error': 'ARP collection failed'}
            }

        # 步骤 2: 触发 IP 定位计算
        try:
            calculator = get_ip_location_calculator(self.db)
            calculation_stats = calculator.calculate_batch()
            
            logger.info(f"IP 定位计算完成：{calculation_stats}")
            
            return {
                'collection': collection_stats,
                'calculation': calculation_stats
            }
        except Exception as e:
            logger.error(f"IP 定位计算失败：{str(e)}")
            return {
                'collection': collection_stats,
                'calculation': {'error': str(e)}
            }


def get_arp_mac_scheduler(db: Session) -> ARPMACScheduler:
    """
    获取 ARP+MAC 调度器实例

    Args:
        db: 数据库会话

    Returns:
        调度器实例
    """
    return ARPMACScheduler(db)
```

- [ ] **Step 2: 修改 ip_location_scheduler.py 集成采集调度**

Modify `app/services/ip_location_scheduler.py`:

```python
from app.services.arp_mac_scheduler import get_arp_mac_scheduler

# ... existing code ...

def _run_calculation(self):
    """
    执行计算任务（包含采集 + 计算）
    """
    db = next(get_db())
    try:
        # 先采集 ARP 和 MAC
        scheduler = get_arp_mac_scheduler(db)
        result = scheduler.collect_and_calculate()
        
        logger.info(f"定时任务执行完成：{result}")
        
    except Exception as e:
        logger.error(f"定时任务执行失败：{str(e)}")
    finally:
        db.close()
```

- [ ] **Step 3: 提交**

```bash
git add app/services/arp_mac_scheduler.py app/services/ip_location_scheduler.py
git commit -m "feat: add ARP+MAC batch collection scheduler with auto-calculation"
```

---

### Task 5: 集成测试

**Files:**
- Create: `tests/integration/test_ip_location_collection_flow.py`

- [ ] **Step 1: 编写完整数据流集成测试**

```python
# -*- coding: utf-8 -*-
"""
IP 定位数据采集完整流程集成测试

测试完整数据流：采集 → 计算 → 查询
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.models import Device
from app.models.ip_location_current import ARPEntry, MACAddressCurrent
from app.models.ip_location import IPLocationCurrent
from app.services.arp_mac_scheduler import get_arp_mac_scheduler
from app.services.ip_location_calculator import get_ip_location_calculator


class TestIPLocationCollectionFlow:
    """IP 定位数据采集完整流程测试"""

    @pytest.fixture
    def db(self):
        """获取数据库会话"""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def setup_test_device(self, db: Session):
        """准备测试设备"""
        device = Device(
            hostname='test-switch-01',
            ip_address='192.168.1.1',
            vendor='huawei',
            model='S5720',
            status='active'
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        yield device
        # 清理
        db.query(ARPEntry).filter(ARPEntry.device_id == device.id).delete()
        db.query(MACAddressCurrent).filter(MACAddressCurrent.device_id == device.id).delete()
        db.query(IPLocationCurrent).filter(
            IPLocationCurrent.arp_source_device_id == device.id
        ).delete()
        db.delete(device)
        db.commit()

    def test_full_collection_flow(self, db: Session, setup_test_device):
        """测试完整采集流程"""
        device = setup_test_device

        # 步骤 1: 插入模拟 ARP 数据
        arp_entry = ARPEntry(
            device_id=device.id,
            ip_address='192.168.1.100',
            mac_address='AA:BB:CC:DD:EE:FF',
            vlan_id=10,
            arp_interface='GigabitEthernet0/0/1',
            last_seen=datetime.now()
        )
        db.add(arp_entry)
        db.commit()

        # 步骤 2: 插入模拟 MAC 数据
        mac_entry = MACAddressCurrent(
            device_id=device.id,
            mac_address='AA:BB:CC:DD:EE:FF',
            vlan_id=10,
            mac_interface='GigabitEthernet0/0/1',
            is_trunk=False,
            last_seen=datetime.now()
        )
        db.add(mac_entry)
        db.commit()

        # 步骤 3: 执行 IP 定位计算
        calculator = get_ip_location_calculator(db)
        result = calculator.calculate_batch()

        # 验证计算结果
        assert result['matched'] >= 0
        assert result['batch_id'] is not None

        # 步骤 4: 验证 ip_location_current 表有数据
        location = db.query(IPLocationCurrent).filter(
            IPLocationCurrent.ip_address == '192.168.1.100'
        ).first()
        
        assert location is not None
        assert location.mac_address == 'AA:BB:CC:DD:EE:FF'
        assert location.arp_source_device_id == device.id
        assert location.confidence > 0

    def test_scheduler_collect_and_calculate(self, db: Session, setup_test_device):
        """测试调度器完整流程"""
        # 注意：这个测试需要真实的设备连接，可以标记为 skip 或使用 mock
        pytest.skip("需要真实设备连接，使用 mock 测试")
```

- [ ] **Step 2: 运行集成测试**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
pytest tests/integration/test_ip_location_collection_flow.py -v
```

Expected: PASS (或 skip 需要真实设备的测试)

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_ip_location_collection_flow.py
git commit -m "test: add integration tests for IP location collection flow"
```

---

### Task 6: 验证修复

**Files:**
- 无代码变更，仅验证操作

- [ ] **Step 1: 在测试环境执行一次完整采集**

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
python -c "
from app.models import get_db
from app.services.arp_mac_scheduler import get_arp_mac_scheduler

db = next(get_db())
scheduler = get_arp_mac_scheduler(db)
result = scheduler.collect_and_calculate()
print(result)
"
```

Expected: 输出采集和计算统计信息

- [ ] **Step 2: 验证 arp_current 表有数据**

```bash
mysql -u root -p -e "USE switch_manage; SELECT COUNT(*) FROM arp_current;"
```

Expected: 返回大于 0 的记录数

- [ ] **Step 3: 验证 mac_current 表有数据**

```bash
mysql -u root -p -e "USE switch_manage; SELECT COUNT(*) FROM mac_current;"
```

Expected: 返回大于 0 的记录数

- [ ] **Step 4: 验证 ip_location_current 表有数据**

```bash
mysql -u root -p -e "USE switch_manage; SELECT COUNT(*) FROM ip_location_current;"
```

Expected: 返回大于 0 的记录数

- [ ] **Step 5: 验证前端查询返回正确结果**

```bash
curl -X GET "http://localhost:8000/api/ip-location/search?search=192.168" | jq
```

Expected: 返回 IP 定位结果列表

- [ ] **Step 6: 记录验证报告**

创建 `docs/superpowers/verification/2026-03-27-ip-location-collection-verification.md`:

```markdown
# IP 定位数据采集链路修复验证报告

**日期**: 2026-03-27
**验证人**: [姓名]

## 验证结果

### 数据采集验证
- [ ] arp_current 表有数据：___条记录
- [ ] mac_current 表有数据：___条记录
- [ ] ip_location_current 表有数据：___条记录

### 功能验证
- [ ] 单个设备 ARP 采集 API 正常工作
- [ ] 批量 ARP 采集 API 正常工作
- [ ] MAC 采集 API 正常工作（写入 mac_current）
- [ ] IP 定位计算正常产出结果
- [ ] 前端查询返回正确结果

### 性能验证
- [ ] 批量采集耗时：___秒
- [ ] IP 定位计算耗时：___秒

## 问题记录

（如有问题，记录在此）

## 结论

- [ ] 验证通过，可以部署到生产环境
- [ ] 验证失败，需要进一步修复
```

---

## 回滚方案

如果部署后发现问题，按以下步骤回滚：

### 1. 代码回滚

```bash
git revert HEAD~5..HEAD
# 或者
git checkout <previous-commit>
```

### 2. 数据库回滚

```sql
-- 删除新增的表（可选，如果不再需要）
DROP TABLE IF EXISTS arp_current;
DROP TABLE IF EXISTS mac_current;
```

### 3. 恢复旧采集逻辑

如果需要恢复写入旧表（mac_addresses）的逻辑，需要：
- 恢复 `device_collection.py` 中的 `collect_mac_table` 端点
- 重新启动服务

---

## 注意事项

1. **不需要兼容旧表** - mac_addresses 等旧表可不再写入
2. **事务保护** - 所有采集操作使用事务，失败时自动回滚
3. **生产环境零中断** - 先在测试环境验证后再部署
4. **监控告警** - 部署后关注采集成功率和 IP 定位计算结果

---

## 参考文档

- [IP 定位 Ver3 架构设计](./ip-location-v3-design.md)
- [N+1 查询修复 commit cd7a4ef](https://gitlab.com/xxx/switch_manage/commit/cd7a4ef)
