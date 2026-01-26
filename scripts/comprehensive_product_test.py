#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合测试产品映射系统
"""

import sqlite3
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, Product, ProductSize, size_name_filter, _get_product_id_from_size

def comprehensive_product_test():
    """综合测试产品映射系统"""
    
    print("🔍 综合测试产品映射系统...")
    print("📝 测试订单: PET17582664981342618")
    
    with app.app_context():
        # 1. 检查订单数据
        db_file = 'instance/pet_painting.db'
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT size, product_name, style_name, price FROM "order" WHERE order_number = ?', ('PET17582664981342618',))
        order = cursor.fetchone()
        
        if order:
            order_size, order_product_name, order_style_name, order_price = order
            print(f"\n📦 订单数据:")
            print(f"   尺寸: '{order_size}'")
            print(f"   产品名称: '{order_product_name}'")
            print(f"   风格名称: '{order_style_name}'")
            print(f"   价格: {order_price}")
            
            # 2. 测试产品ID映射
            print(f"\n🎯 产品ID映射:")
            product_id = _get_product_id_from_size(order_size)
            print(f"   尺寸: '{order_size}' -> 产品ID: {product_id}")
            
            # 3. 测试尺寸显示
            print(f"\n📏 尺寸显示:")
            size_display = size_name_filter(order_size)
            print(f"   尺寸: '{order_size}' -> 显示: '{size_display}'")
            
            # 4. 验证数据库中的产品配置
            print(f"\n🛍️ 数据库产品配置:")
            product = Product.query.filter_by(name=order_product_name).first()
            if product:
                print(f"   产品: {product.name} (代码: {product.code})")
                sizes = ProductSize.query.filter_by(product_id=product.id, is_active=True).all()
                
                for size in sizes:
                    print(f"      📏 {size.size_name} (ID: {size.id}, 价格: {size.price})")
                    if size.size_name == order_size:
                        print(f"         ✅ 匹配订单尺寸!")
            
            # 5. 验证SIZE_MAPPING
            print(f"\n🗺️ SIZE_MAPPING验证:")
            from printer_config import SIZE_MAPPING
            found_mapping = False
            for key, value in SIZE_MAPPING.items():
                if order_size in value['product_name'] or value['product_name'] in order_size:
                    print(f"   映射: {key} -> {value['product_name']} -> {value['product_id']}")
                    if value['product_id'] == product_id:
                        print(f"      ✅ 产品ID匹配!")
                    found_mapping = True
            
            if not found_mapping:
                print(f"   ❌ 没有找到SIZE_MAPPING匹配")
            
            # 6. 总结
            print(f"\n📋 总结:")
            print(f"   ✅ 产品ID映射: {product_id}")
            print(f"   ✅ 尺寸显示: {size_display}")
            print(f"   ✅ 产品名称: {order_product_name}")
            print(f"   ✅ 风格名称: {order_style_name}")
            print(f"   ✅ 价格: {order_price}")
            
            # 7. 检查是否所有信息都正确
            expected_product_id = "33673"
            expected_size_display = "30x30cm肌理画框 (¥99.0)"
            
            all_correct = True
            if product_id != expected_product_id:
                print(f"   ❌ 产品ID错误: 期望 {expected_product_id}, 实际 {product_id}")
                all_correct = False
            
            if expected_size_display not in size_display:
                print(f"   ❌ 尺寸显示错误: 期望包含 {expected_size_display}, 实际 {size_display}")
                all_correct = False
            
            if all_correct:
                print(f"\n🎉 所有产品映射都正确!")
            else:
                print(f"\n⚠️ 部分产品映射需要调整")
        
        conn.close()

if __name__ == "__main__":
    comprehensive_product_test()
