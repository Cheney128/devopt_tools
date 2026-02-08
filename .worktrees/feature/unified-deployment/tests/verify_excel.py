#!/usr/bin/env python3
"""
验证生成的Excel模板文件
"""
import pandas as pd

def verify_excel_file():
    """验证Excel文件"""
    try:
        # 读取Excel文件
        df = pd.read_excel('test_template.xlsx')
        
        print('✅ Excel文件读取成功！')
        print(f'列名: {list(df.columns)}')
        print(f'行数: {len(df)}')
        
        if len(df) > 0:
            print('前5行数据:')
            print(df.head())
        
        # 验证是否包含所有必要字段
        required_fields = ['hostname', 'ip_address', 'vendor', 'model', 'os_version', 
                          'location', 'contact', 'status', 'login_method', 'login_port', 
                          'username', 'password', 'sn']
        
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            print(f'❌ 缺少必要字段: {missing_fields}')
            return False
        else:
            print('✅ 包含所有必要字段！')
            return True
            
    except Exception as e:
        print(f'❌ 验证失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print('开始验证Excel文件...')
    success = verify_excel_file()
    if success:
        print('✅ 验证通过！')
    else:
        print('❌ 验证失败！')
