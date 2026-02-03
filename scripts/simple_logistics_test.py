#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物流回调测试脚本 - 单次测试
针对订单 PET17582664981342618
"""

import requests
import json

def main():
    print("🚚 物流回调测试 - 单次测试")
    print("=" * 40)
    
    # 接口配置
    api_url = "https://photogooo/api/logistics/callback"
    order_number = "PET17582664981342618"
    
    # 测试数据
    test_data = {
        "order_number": order_number,
        "tracking_number": "SF1234567890",
        "logistics_company": "顺丰速运",
        "estimated_delivery": "2025-09-21",
        "status": "已发货",
        "remark": "商品已发出，请注意查收"
    }
    
    print(f"📦 目标订单: {order_number}")
    print(f"🌐 接口地址: {api_url}")
    print()
    
    # 显示请求数据
    print("📤 请求数据:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    try:
        # 发送请求
        print("\n🚀 发送请求...")
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # 显示响应
        print(f"📥 响应状态码: {response.status_code}")
        print("📥 响应数据:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
            
            # 分析结果
            if response_data.get('success'):
                print("\n✅ 测试成功!")
                if 'data' in response_data:
                    data = response_data['data']
                    print(f"   📦 订单号: {data.get('order_number')}")
                    print(f"   🚚 快递公司: {data.get('logistics_company')}")
                    print(f"   📋 快递单号: {data.get('tracking_number')}")
                    print(f"   📊 订单状态: {data.get('status')}")
                    if 'commission' in data:
                        print(f"   💰 佣金: ¥{data.get('commission')}")
            else:
                print("\n❌ 测试失败!")
                print(f"   错误信息: {response_data.get('message', '未知错误')}")
                
        except json.JSONDecodeError:
            print("\n❌ 响应不是有效的JSON格式")
            print(f"   原始响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接错误")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {str(e)}")
    
    print("\n" + "=" * 40)
    print("🎉 测试完成!")

if __name__ == "__main__":
    main()
