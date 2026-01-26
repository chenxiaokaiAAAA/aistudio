#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商家物流回调测试脚本 - 超精简版
"""

import requests
import json

# 配置信息
API_URL = "https://moeart.cc/api/logistics/callback"
ORDER_NUMBER = "PET17582664981342618"  # 替换为实际订单号

def test_callback():
    """测试物流回调"""
    
    # 测试数据
    data = {
        "order_number": ORDER_NUMBER,
        "tracking_number": "SF1234567890",
        "logistics_company": "顺丰速运"
    }
    
    print(f"🚚 测试订单: {ORDER_NUMBER}")
    print(f"📤 发送数据: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=10)
        result = response.json()
        
        print(f"📥 响应结果: {json.dumps(result, ensure_ascii=False)}")
        
        if result.get('success'):
            print("✅ 测试成功!")
        else:
            print("❌ 测试失败!")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_callback()
