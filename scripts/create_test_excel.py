"""
创建测试用的 Excel 设备清单文件
"""
import os
import sys
import pandas as pd

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def create_test_excel():
    """
    创建测试用的 Excel 文件
    """
    # 测试设备数据
    test_devices = [
        {
            'hostname': 'SW-CORE-01',
            'ip_address': '10.0.1.1',
            'vendor': 'Huawei',
            'model': 'S12700E',
            'os_version': 'V200R022C00SPC500',
            'location': '核心机房-A区',
            'contact': 'admin@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-CORE-02',
            'ip_address': '10.0.1.2',
            'vendor': 'Huawei',
            'model': 'S12700E',
            'os_version': 'V200R022C00SPC500',
            'location': '核心机房-A区',
            'contact': 'admin@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-AGG-01',
            'ip_address': '10.0.2.1',
            'vendor': 'Huawei',
            'model': 'S6720-30C-EI-24S',
            'os_version': 'V200R021C00SPC100',
            'location': '汇聚机房-B区',
            'contact': 'netops@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-AGG-02',
            'ip_address': '10.0.2.2',
            'vendor': 'Huawei',
            'model': 'S6720-30C-EI-24S',
            'os_version': 'V200R021C00SPC100',
            'location': '汇聚机房-B区',
            'contact': 'netops@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-ACC-F1-01',
            'ip_address': '10.0.3.1',
            'vendor': 'Huawei',
            'model': 'S5700-28C-SI-24S',
            'os_version': 'V200R019C10SPC500',
            'location': '接入机房-F1层',
            'contact': 'support@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-ACC-F1-02',
            'ip_address': '10.0.3.2',
            'vendor': 'Huawei',
            'model': 'S5700-28C-SI-24S',
            'os_version': 'V200R019C10SPC500',
            'location': '接入机房-F1层',
            'contact': 'support@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-ACC-F2-01',
            'ip_address': '10.0.4.1',
            'vendor': 'H3C',
            'model': 'S5130S-28S-EI',
            'os_version': 'Release 1115P12',
            'location': '接入机房-F2层',
            'contact': 'support@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-ACC-F3-01',
            'ip_address': '10.0.5.1',
            'vendor': 'H3C',
            'model': 'S5130S-28S-EI',
            'os_version': 'Release 1115P12',
            'location': '接入机房-F3层',
            'contact': 'support@company.com',
            'status': 'active'
        },
        {
            'hostname': 'SW-TEST-01',
            'ip_address': '10.0.10.1',
            'vendor': 'Huawei',
            'model': 'S5735-L48T4S-A',
            'os_version': 'V200R021C00SPC300',
            'location': '测试实验室',
            'contact': 'test@company.com',
            'status': 'maintenance'
        },
        {
            'hostname': 'SW-TEST-02',
            'ip_address': '10.0.10.2',
            'vendor': 'Huawei',
            'model': 'S5735-L48T4S-A',
            'os_version': 'V200R021C00SPC300',
            'location': '测试实验室',
            'contact': 'test@company.com',
            'status': 'offline'
        }
    ]

    # 创建 DataFrame
    df = pd.DataFrame(test_devices)

    # 保存到 Excel 文件
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, 'devices.xlsx')
    df.to_excel(output_file, index=False, sheet_name='设备清单')

    print("=" * 60)
    print("测试 Excel 文件创建成功")
    print("=" * 60)
    print(f"\n文件路径: {output_file}")
    print(f"设备数量: {len(test_devices)}")
    print("\n设备列表:")
    for i, device in enumerate(test_devices, 1):
        print(f"  {i}. {device['hostname']:15} | {device['ip_address']:15} | {device['vendor']:8} {device['model']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    create_test_excel()
