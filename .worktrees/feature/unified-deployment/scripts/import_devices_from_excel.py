"""
从 Excel 文件导入设备数据到数据库
支持 .xlsx 和 .xls 格式
"""
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.models import SessionLocal
from app.models.models import Device


def load_excel_to_dataframe(file_path: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    从 Excel 文件加载数据到 DataFrame

    Args:
        file_path: Excel 文件路径
        sheet_name: 工作表名称或索引，默认为第一个工作表

    Returns:
        pandas DataFrame
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 判断文件类型
    if file_path.endswith('.xlsx'):
        return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    elif file_path.endswith('.xls'):
        return pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
    else:
        raise ValueError("不支持的文件格式，仅支持 .xlsx 和 .xls 文件")


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
        df_columns_lower = {col.lower(): col for col in df.columns}
        mapped_columns = []
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
    row_num = 0
    for idx, row in df.iterrows():
        row_num += 1
        # 检查必填字段
        if pd.isna(row['hostname']) or pd.isna(row['ip_address']) or \
           pd.isna(row['vendor']) or pd.isna(row['model']):
            print("  [警告] 第", row_num + 1, "行: 缺少必填字段，已跳过")
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

        # 验证登录方式只能是ssh或telnet
        if device_data['login_method'] not in ['ssh', 'telnet']:
            print("  [警告] 第", row_num + 1, "行: 登录方式无效，默认使用ssh")
            device_data['login_method'] = 'ssh'

        # 验证登录端口范围
        if device_data['login_port'] < 1 or device_data['login_port'] > 65535:
            print("  [警告] 第", row_num + 1, "行: 端口号无效，默认使用22")
            device_data['login_port'] = 22

        # 如果是telnet且端口为22，自动改为23
        if device_data['login_method'] == 'telnet' and device_data['login_port'] == 22:
            device_data['login_port'] = 23

        valid_devices.append(device_data)

    return valid_devices


def import_devices_to_db(devices_data: List[Dict[str, Any]], session: Session,
                      skip_existing: bool = True) -> Dict[str, int]:
    """
    导入设备数据到数据库

    Args:
        devices_data: 设备数据列表
        session: SQLAlchemy 会话
        skip_existing: 是否跳过已存在的设备（根据 ip_address 判断）

    Returns:
        导入结果统计字典
    """
    stats = {
        'total': len(devices_data),
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }

    for device_data in devices_data:
        try:
            # 检查设备是否已存在
            existing = session.query(Device).filter(
                Device.ip_address == device_data['ip_address']
            ).first()

            if existing:
                if skip_existing:
                    print(f"  [跳过] 设备 {device_data['hostname']} ({device_data['ip_address']}) 已存在")
                    stats['skipped'] += 1
                    continue
                else:
                    # 更新现有设备
                    for key, value in device_data.items():
                        if key != 'ip_address':  # IP地址不可更新
                            setattr(existing, key, value)
                    session.commit()
                    print(f"  [更新] 设备 {device_data['hostname']} ({device_data['ip_address']}) 已更新")
                    stats['success'] += 1
            else:
                # 创建新设备
                new_device = Device(**device_data)
                session.add(new_device)
                session.commit()
                print(f"  [成功] 设备 {device_data['hostname']} ({device_data['ip_address']}) 已导入")
                stats['success'] += 1

        except Exception as e:
            session.rollback()
            error_msg = f"{device_data['hostname']} ({device_data['ip_address']}): {str(e)}"
            stats['errors'].append(error_msg)
            stats['failed'] += 1
            print(f"  [失败] {error_msg}")

    return stats


def main():
    """
    主函数：从 Excel 导入设备数据
    """
    print("=" * 60)
    print("设备数据导入工具")
    print("=" * 60)

    # 默认 Excel 文件路径
    default_excel_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "devices.xlsx"
    )

    # 如果指定了文件参数，使用参数
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = default_excel_file

    print(f"\nExcel 文件: {excel_file}")

    # 检查文件是否存在
    if not os.path.exists(excel_file):
        print(f"\n[错误] Excel 文件不存在: {excel_file}")
        print(f"\n提示: 请将 Excel 文件放置在 {default_excel_file}")
        return

    try:
        # 加载 Excel 数据
        print("\n[1/3] 加载 Excel 数据...")
        df = load_excel_to_dataframe(excel_file)
        print(f"      共 {len(df)} 行数据")
        print(f"      列: {', '.join(df.columns.tolist())}")

        # 验证数据
        print("\n[2/3] 验证设备数据...")
        devices_data = validate_device_data(df)
        if not devices_data:
            print("[错误] 没有有效的设备数据可导入")
            return
        print(f"      有效设备数: {len(devices_data)}")

        # 显示前3条数据
        print("\n      前3条预览:")
        for i, device in enumerate(devices_data[:3]):
            print(f"        {i+1}. {device['hostname']} - {device['ip_address']} - {device['vendor']} {device['model']}")

        # 导入数据库
        print("\n[3/3] 导入到数据库...")
        session = SessionLocal()
        try:
            stats = import_devices_to_db(devices_data, session, skip_existing=True)

            # 显示统计结果
            print("\n" + "=" * 60)
            print("导入完成统计:")
            print(f"  总计: {stats['total']} 条")
            print(f"  成功: {stats['success']} 条")
            print(f"  跳过: {stats['skipped']} 条")
            print(f"  失败: {stats['failed']} 条")

            if stats['errors']:
                print("\n失败详情:")
                for error in stats['errors']:
                    print(f"  - {error}")

            print("=" * 60)

        finally:
            session.close()

    except FileNotFoundError as e:
        print(f"\n[错误] {str(e)}")
    except ValueError as e:
        print(f"\n[错误] {str(e)}")
    except Exception as e:
        print(f"\n[错误] 导入过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 创建 data 目录（如果不存在）
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"已创建数据目录: {data_dir}")

    main()
