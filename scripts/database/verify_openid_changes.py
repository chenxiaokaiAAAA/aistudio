#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 /api/user/openid 接口修改
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_openid_api_changes():
    """验证openid接口的修改"""
    print("🔍 验证 /api/user/openid 接口修改...")
    
    try:
        # 读取test_server.py文件
        with open('test_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查修改是否正确应用
        checks = [
            ("缺少code参数的错误返回格式", "'data': {\n                    'success': False,\n                    'message': '缺少code参数'\n                }"),
            ("成功获取openid的返回格式", "'data': {\n                    'success': True,\n                    'openid': result['openid']"),
            ("获取openid失败的错误返回格式", "'data': {\n                    'success': False,\n                    'message': result.get('errmsg', '获取openid失败')"),
            ("异常处理的错误返回格式", "'data': {\n                'success': False,\n                'message': f'获取openid失败: {str(e)}'")
        ]
        
        all_passed = True
        for check_name, expected_format in checks:
            if expected_format in content:
                print(f"✅ {check_name} - 修改正确")
            else:
                print(f"❌ {check_name} - 修改缺失")
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有修改都已正确应用！")
            print("\n📋 修改总结:")
            print("1. ✅ 缺少code参数的错误返回格式已更新")
            print("2. ✅ 成功获取openid的返回格式已更新") 
            print("3. ✅ 获取openid失败的错误返回格式已更新")
            print("4. ✅ 异常处理的错误返回格式已更新")
            
            print("\n🔄 新的返回格式:")
            print("成功时:")
            print('{\n  "data": {\n    "success": true,\n    "openid": "用户openid",\n    "session_key": "会话密钥"\n  }\n}')
            print("\n失败时:")
            print('{\n  "data": {\n    "success": false,\n    "message": "错误信息"\n  }\n}')
        else:
            print("\n❌ 部分修改未正确应用，请检查代码")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    verify_openid_api_changes()
