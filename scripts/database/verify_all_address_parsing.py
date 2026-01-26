#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证所有订单的地址解析修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Order
from printer_client import PrinterSystemClient
from printer_config import PRINTER_SYSTEM_CONFIG

def verify_all_address_parsing():
    """验证所有订单的地址解析修复"""
    
    print("🔍 验证所有订单的地址解析修复...")
    
    with app.app_context():
        # 1. 查找有完整地址信息的订单
        orders_with_address = Order.query.filter(
            Order.shipping_info.isnot(None),
            Order.shipping_info != '',
            Order.shipping_info.like('%province%')
        ).all()
        
        print(f"📊 找到 {len(orders_with_address)} 个有完整地址信息的订单")
        
        # 2. 测试每个订单的地址解析
        success_count = 0
        total_count = len(orders_with_address)
        
        for order in orders_with_address:
            print(f"\n📦 订单: {order.order_number}")
            
            try:
                import json
                shipping_data = json.loads(order.shipping_info)
                
                # 检查地址信息
                receiver = shipping_data.get('receiver', '')
                province = shipping_data.get('province', '')
                city = shipping_data.get('city', '')
                district = shipping_data.get('district', '')
                address = shipping_data.get('address', '')
                
                print(f"   收件人: {receiver}")
                print(f"   省份: {province}")
                print(f"   城市: {city}")
                print(f"   区县: {district}")
                print(f"   地址: {address}")
                
                # 检查是否有Unicode编码
                has_unicode = False
                for key, value in [('receiver', receiver), ('province', province), ('city', city), ('district', district), ('address', address)]:
                    if isinstance(value, str) and '\\u' in value:
                        print(f"   ⚠️ {key} 包含Unicode编码: {value}")
                        has_unicode = True
                
                if not has_unicode and (province or city or district):
                    print(f"   ✅ 地址解析正确")
                    success_count += 1
                else:
                    print(f"   ❌ 地址解析有问题")
                    
            except Exception as e:
                print(f"   ❌ 解析失败: {str(e)}")
        
        # 3. 测试冲印系统数据构建
        print(f"\n🏭 测试冲印系统数据构建:")
        test_order = orders_with_address[0] if orders_with_address else None
        
        if test_order and test_order.hd_image:
            hd_image_path = os.path.join(app.config['HD_FOLDER'], test_order.hd_image)
            if os.path.exists(hd_image_path):
                printer_client = PrinterSystemClient(PRINTER_SYSTEM_CONFIG)
                order_data = printer_client._build_order_data(test_order, hd_image_path)
                
                shipping_receiver = order_data.get('shipping_receiver', {})
                print(f"   冲印系统收件人信息:")
                print(f"     姓名: {shipping_receiver.get('name')}")
                print(f"     电话: {shipping_receiver.get('mobile')}")
                print(f"     省份: {shipping_receiver.get('province')}")
                print(f"     城市: {shipping_receiver.get('city')}")
                print(f"     区县: {shipping_receiver.get('city_part')}")
                print(f"     街道: {shipping_receiver.get('street')}")
                
                # 检查是否还有Unicode编码
                has_unicode = False
                for key, value in shipping_receiver.items():
                    if isinstance(value, str) and '\\u' in value:
                        print(f"     ⚠️ {key} 包含Unicode编码: {value}")
                        has_unicode = True
                
                if not has_unicode:
                    print(f"   ✅ 冲印系统地址信息正确")
                else:
                    print(f"   ❌ 冲印系统地址信息仍有Unicode编码")
            else:
                print(f"   ⚠️ 测试订单没有高清图片")
        else:
            print(f"   ⚠️ 没有可测试的订单")
        
        # 4. 总结
        print(f"\n📊 验证总结:")
        print(f"   ✅ 总订单数: {total_count}")
        print(f"   ✅ 解析成功: {success_count}")
        print(f"   ✅ 成功率: {success_count/total_count*100:.1f}%" if total_count > 0 else "   ✅ 成功率: 0%")
        
        if success_count == total_count:
            print(f"\n🎉 所有订单地址解析都正确！")
        else:
            print(f"\n⚠️ 部分订单地址解析需要检查")

if __name__ == "__main__":
    verify_all_address_parsing()
