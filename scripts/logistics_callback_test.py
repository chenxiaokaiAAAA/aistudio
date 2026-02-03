#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物流回调测试脚本 - 针对订单 PET17582664981342618
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_logistics_callback():
    """测试物流回调接口"""
    
    print("🚚 物流回调测试脚本")
    print("=" * 50)
    
    # 接口配置
    api_url = "https://photogooo/api/logistics/callback"
    order_number = "PET17582664981342618"
    
    # 测试数据
    test_cases = [
        {
            "name": "顺丰速运测试",
            "data": {
                "order_number": order_number,
                "tracking_number": "SF1234567890",
                "logistics_company": "顺丰速运",
                "estimated_delivery": "2025-09-21",
                "status": "已发货",
                "remark": "商品已发出，请注意查收"
            }
        },
        {
            "name": "圆通速递测试",
            "data": {
                "order_number": order_number,
                "tracking_number": "YT9876543210",
                "logistics_company": "圆通速递",
                "estimated_delivery": "2025-09-22",
                "status": "已发货",
                "remark": "包裹已发出"
            }
        },
        {
            "name": "中通快递测试",
            "data": {
                "order_number": order_number,
                "tracking_number": "ZT5556667778",
                "logistics_company": "中通快递",
                "estimated_delivery": "2025-09-23",
                "status": "已发货",
                "remark": "快递已发出，预计3天内送达"
            }
        },
        {
            "name": "简化格式测试",
            "data": {
                "order_number": order_number,
                "tracking_number": "JD8889990001",
                "logistics_company": "京东物流"
            }
        }
    ]
    
    print(f"📦 目标订单: {order_number}")
    print(f"🌐 接口地址: {api_url}")
    print(f"📊 测试用例数量: {len(test_cases)}")
    print()
    
    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 测试用例 {i}: {test_case['name']}")
        print("-" * 30)
        
        # 显示请求数据
        print("📤 请求数据:")
        print(json.dumps(test_case['data'], ensure_ascii=False, indent=2))
        
        try:
            # 发送请求
            print("🚀 发送请求...")
            response = requests.post(
                api_url,
                json=test_case['data'],
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
                    print("✅ 测试成功!")
                    if 'data' in response_data:
                        data = response_data['data']
                        print(f"   📦 订单号: {data.get('order_number')}")
                        print(f"   🚚 快递公司: {data.get('logistics_company')}")
                        print(f"   📋 快递单号: {data.get('tracking_number')}")
                        print(f"   📊 订单状态: {data.get('status')}")
                        if 'commission' in data:
                            print(f"   💰 佣金: ¥{data.get('commission')}")
                else:
                    print("❌ 测试失败!")
                    print(f"   错误信息: {response_data.get('message', '未知错误')}")
                    
            except json.JSONDecodeError:
                print("❌ 响应不是有效的JSON格式")
                print(f"   原始响应: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误")
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {str(e)}")
        
        print()
        
        # 等待一下再执行下一个测试
        if i < len(test_cases):
            print("⏳ 等待3秒后执行下一个测试...")
            time.sleep(3)
            print()
    
    print("=" * 50)
    print("🎉 所有测试完成!")
    print()
    print("📝 测试说明:")
    print("1. 每个测试用例都会更新订单的物流信息")
    print("2. 订单状态会更新为 'processing'（已发货）")
    print("3. 可以在后台管理界面查看更新结果")
    print("4. 建议按顺序执行，观察每次的变化")

def test_single_callback():
    """单个测试用例 - 推荐使用"""
    
    print("🚚 物流回调测试 - 单个测试用例")
    print("=" * 50)
    
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
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")

if __name__ == "__main__":
    print("请选择测试模式:")
    print("1. 完整测试 (多个测试用例)")
    print("2. 单个测试 (推荐)")
    
    choice = input("\n请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        test_logistics_callback()
    elif choice == "2":
        test_single_callback()
    else:
        print("无效选择，执行单个测试...")
        test_single_callback()