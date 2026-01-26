#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的物流回调测试脚本
"""

import requests
import json

def test_callback():
    """测试物流回调"""
    
    # 测试数据
    data = {
        "order_number": "PET202509181014143793",
        "tracking_number": "SF1234567890", 
        "logistics_company": "顺丰速运",
        "status": "已发货",
        "remark": "测试回调"
    }
    
    # 测试URL
    url = "https://moeart.cc/api/logistics/callback"
    
    print(f"🚀 测试物流回调")
    print(f"订单: {data['order_number']}")
    print(f"接口: {url}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 回调成功!")
            else:
                print(f"❌ 回调失败: {result.get('message')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_callback()
