#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物流回调接口诊断脚本
用于检查接口是否正常工作
"""

import requests
import json
import time
from datetime import datetime

def diagnose_callback_api():
    """诊断物流回调接口"""
    
    print("🔍 物流回调接口诊断")
    print("=" * 40)
    
    api_url = "https://photogooo/api/logistics/callback"
    test_order = "PET17582664981342618"
    
    # 测试数据
    test_data = {
        "order_number": test_order,
        "tracking_number": f"TEST{int(time.time())}",
        "logistics_company": "测试快递"
    }
    
    print(f"🌐 接口地址: {api_url}")
    print(f"📦 测试订单: {test_order}")
    print(f"📋 快递单号: {test_data['tracking_number']}")
    print()
    
    # 1. 检查网络连接
    print("1️⃣ 检查网络连接...")
    try:
        response = requests.get("https://photogooo", timeout=5)
        print(f"   ✅ 网站可访问 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ 网站无法访问: {str(e)}")
        return
    
    # 2. 检查接口响应
    print("\n2️⃣ 检查接口响应...")
    try:
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📥 响应状态码: {response.status_code}")
        print(f"   📥 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   📥 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print("   ✅ 接口调用成功!")
                else:
                    print(f"   ⚠️ 接口返回失败: {result.get('message', '未知错误')}")
                    
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是JSON格式: {response.text}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"   📥 错误内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("   ❌ 连接错误")
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
    
    # 3. 检查订单状态
    print("\n3️⃣ 检查订单状态...")
    try:
        # 这里可以添加检查订单状态的逻辑
        print("   ℹ️ 请在后台管理界面查看订单状态是否更新")
    except Exception as e:
        print(f"   ❌ 检查订单状态失败: {str(e)}")
    
    print("\n" + "=" * 40)
    print("🎉 诊断完成!")
    print()
    print("📝 建议:")
    print("1. 如果网络连接正常但接口调用失败，可能是服务器问题")
    print("2. 如果接口调用成功但订单状态没更新，可能是数据库问题")
    print("3. 如果所有测试都正常，说明接口工作正常")

if __name__ == "__main__":
    diagnose_callback_api()
