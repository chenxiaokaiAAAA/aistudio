#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支付接口诊断脚本
"""

import requests
import json
import time

def test_payment_create():
    """测试支付创建接口"""
    print("🔍 测试 /api/payment/create 接口...")
    
    url = "http://localhost:8000/api/payment/create"
    
    # 测试数据
    test_data = {
        "orderId": "TEST_ORDER_123456",
        "totalPrice": "0.01",  # 1分钱测试
        "openid": "080c-181egKUh1G-ewmG00ePJUPE"  # 你提到的openid
    }
    
    print(f"📤 发送数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 错误响应: {response.text}")
            
            # 尝试解析JSON错误信息
            try:
                error_data = response.json()
                print(f"📝 错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                print("📝 无法解析错误信息为JSON")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_server_connection():
    """测试服务器连接"""
    print("🔍 测试服务器连接...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("支付接口诊断")
    print("=" * 50)
    
    # 测试服务器连接
    if not test_server_connection():
        print("\n❌ 服务器未运行，请先启动服务器")
        return
    
    # 测试支付接口
    test_payment_create()
    
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)

if __name__ == "__main__":
    main()

