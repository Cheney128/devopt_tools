"""
Excel 处理服务
用于处理设备数据的导入导出
"""
from typing import List, Dict, Any, BinaryIO
import pandas as pd
from sqlalchemy.orm import Session
from io import BytesIO
from openpyxl.styles import Font

from app.models.models import Device


def validate_device_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    验证并转换设备数据

    Args:
        df: 包含设备数据的 DataFrame

    Returns:
        验证后的设备数据列表

    Raises:
        ValueError: 数据验证失败
    """
    # 定义必填字段
    required_columns = ['hostname', 'ip_address', 'vendor', 'model']

    # 检查必填列是否存在
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        # 尝试使用列名映射（支持中文列名）
        column_mapping = {
            '主机名': 'hostname',
            '设备名称': 'hostname',
            '名称': 'hostname',
            'IP地址': 'ip_address',
            'IP': 'ip_address',
            'IP Address': 'ip_address',
            '厂商': 'vendor',
            '供应商': 'vendor',
            '厂商品牌': 'vendor',
            '型号': 'model',
            '设备型号': 'model',
            'Model': 'model',
            '位置': 'location',
            '机房位置': 'location',
            'Location': 'location',
            '联系人': 'contact',
            '联系方式': 'contact',
            'Contact': 'contact',
            '状态': 'status',
            'Status': 'status',
            '操作系统版本': 'os_version',
            'OS版本': 'os_version',
            'OS Version': 'os_version',
            # 登录信息字段映射
            '登录方式': 'login_method',
            '连接方式': 'login_method',
            'Login Method': 'login_method',
            '登录端口': 'login_port',
            '连接端口': 'login_port',
            'Login Port': 'login_port',
            '用户名': 'username',
            '账号': 'username',
            'Username': 'username',
            '密码': 'password',
            'Password': 'password',
            '序列号': 'sn',
            'SN': 'sn',
            'Serial Number': 'sn',
        }

        # 尝试映射中文列名
        for required in missing_columns:
            mapped = False
            for cn_col, en_col in column_mapping.items():
                if en_col == required:
                    # 检查中文列名是否存在
                    for df_col in df.columns:
                        if cn_col in df_col or df_col.lower().replace(' ', '_') == en_col.lower():
                            df.rename(columns={df_col: en_col}, inplace=True)
                            mapped = True
                            break
                    if mapped:
                        break
            if not mapped:
                raise ValueError(f"缺少必填列: {required}")

    # 验证必填字段不为空
    valid_devices = []
    for idx, row in df.iterrows():
        # 检查必填字段
        if pd.isna(row['hostname']) or pd.isna(row['ip_address']) or \
           pd.isna(row['vendor']) or pd.isna(row['model']):
            continue

        # 转换为设备数据字典
        device_data = {
            'hostname': str(row['hostname']).strip(),
            'ip_address': str(row['ip_address']).strip(),
            'vendor': str(row['vendor']).strip(),
            'model': str(row['model']).strip(),
            'os_version': str(row.get('os_version', '')).strip() if pd.notna(row.get('os_version')) else '',
            'location': str(row.get('location', '')).strip() if pd.notna(row.get('location')) else '',
            'contact': str(row.get('contact', '')).strip() if pd.notna(row.get('contact')) else '',
            'status': str(row.get('status', 'active')).strip() if pd.notna(row.get('status')) else 'active',
            # 登录信息字段
            'login_method': str(row.get('login_method', 'ssh')).strip().lower() if pd.notna(row.get('login_method')) else 'ssh',
            'login_port': int(row.get('login_port', 22)) if pd.notna(row.get('login_port')) else 22,
            'username': str(row.get('username', '')).strip() if pd.notna(row.get('username')) else '',
            'password': str(row.get('password', '')).strip() if pd.notna(row.get('password')) else '',
            'sn': str(row.get('sn', '')).strip() if pd.notna(row.get('sn')) else '',
        }

        # 验证登录方式只能是ssh或telnet或console
        if device_data['login_method'] not in ['ssh', 'telnet', 'console']:
            device_data['login_method'] = 'ssh'

        # 验证登录端口范围
        if device_data['login_port'] < 1 or device_data['login_port'] > 65535:
            device_data['login_port'] = 22

        # 如果是telnet且端口为22，自动改为23
        if device_data['login_method'] == 'telnet' and device_data['login_port'] == 22:
            device_data['login_port'] = 23

        valid_devices.append(device_data)

    return valid_devices


def read_excel_file(file_content: BinaryIO, sheet_name: str = 0) -> pd.DataFrame:
    """
    从Excel文件内容读取数据

    Args:
        file_content: Excel文件内容的二进制流
        sheet_name: 工作表名称或索引，默认为第一个工作表

    Returns:
        pandas DataFrame

    Raises:
        ValueError: 不支持的文件格式
    """
    # 尝试使用openpyxl读取xlsx文件
    try:
        return pd.read_excel(file_content, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"读取Excel文件失败: {str(e)}")


def import_devices_from_excel(file_content: BinaryIO, session: Session, 
                              skip_existing: bool = False) -> Dict[str, Any]:
    """
    从Excel文件导入设备数据到数据库

    Args:
        file_content: Excel文件内容的二进制流
        session: SQLAlchemy会话
        skip_existing: 是否跳过已存在的设备（根据ip_address判断）

    Returns:
        导入结果统计字典
    """
    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }

    try:
        # 读取Excel文件
        df = read_excel_file(file_content)
        stats['total'] = len(df)

        # 验证设备数据
        devices_data = validate_device_data(df)

        # 导入设备数据
        for device_data in devices_data:
            try:
                # 检查设备是否已存在
                existing = session.query(Device).filter(
                    Device.ip_address == device_data['ip_address']
                ).first()

                if existing:
                    if skip_existing:
                        stats['skipped'] += 1
                        continue
                    else:
                        # 更新现有设备
                        for key, value in device_data.items():
                            if key != 'ip_address':  # IP地址不可更新
                                setattr(existing, key, value)
                        session.commit()
                        stats['success'] += 1
                else:
                    # 创建新设备
                    new_device = Device(**device_data)
                    session.add(new_device)
                    session.commit()
                    stats['success'] += 1

            except Exception as e:
                session.rollback()
                error_msg = f"{device_data['hostname']} ({device_data['ip_address']}): {str(e)}"
                stats['errors'].append(error_msg)
                stats['failed'] += 1

    except Exception as e:
        stats['errors'].append(str(e))
        stats['failed'] = stats['total']

    return stats


def generate_device_template(session: Session = None) -> BytesIO:
    """
    生成设备导入模板

    Args:
        session: SQLAlchemy会话，如果提供则包含现有设备数据

    Returns:
        包含模板数据的BytesIO对象
    """
    # 定义设备字段
    device_fields = [
        'hostname', 'ip_address', 'vendor', 'model', 'os_version', 
        'location', 'contact', 'status', 'login_method', 'login_port', 
        'username', 'password', 'sn'
    ]

    # 创建模板数据
    if session:
        # 获取现有设备数据
        devices = session.query(Device).all()
        if devices:
            # 使用现有设备数据作为模板
            device_data = []
            for device in devices:
                device_dict = {
                    'hostname': device.hostname,
                    'ip_address': device.ip_address,
                    'vendor': device.vendor,
                    'model': device.model,
                    'os_version': device.os_version or '',
                    'location': device.location or '',
                    'contact': device.contact or '',
                    'status': device.status,
                    'login_method': device.login_method,
                    'login_port': device.login_port,
                    'username': device.username or '',
                    'password': '',  # 密码字段为空，确保安全
                    'sn': device.sn or ''
                }
                device_data.append(device_dict)
            df = pd.DataFrame(device_data)
        else:
            # 只有表头的空模板
            df = pd.DataFrame(columns=device_fields)
    else:
        # 只有表头的空模板
        df = pd.DataFrame(columns=device_fields)

    # 创建Excel文件，确保正确处理中文字符
    output = BytesIO()
    # 使用openpyxl直接创建工作簿，避免pandas的编码问题
    from openpyxl import Workbook
    
    wb = Workbook()
    ws = wb.active
    ws.title = "设备清单"
    
    # 写入表头
    ws.append(device_fields)
    
    # 写入数据
    for _, row in df.iterrows():
        ws.append(row.tolist())
    
    # 保存到BytesIO对象
    wb.save(output)
    output.seek(0)
    
    return output
