#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细测试尺寸显示功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, ProductSize, Product, Order

def detailed_test():
    """详细测试尺寸显示功能"""
    with app.app_context():
        print("=== 详细测试size_name过滤器 ===")
        
        # 获取过滤器函数
        size_name_filter = app.jinja_env.filters['size_name']
        
        # 测试keychain
        print("\n1. 测试keychain:")
        result = size_name_filter('keychain')
        print(f"   keychain -> {result}")
        
        # 检查ProductSize表中的第一个记录
        print("\n2. 检查ProductSize表中的第一个记录:")
        first_size = ProductSize.query.filter_by(is_active=True).first()
        if first_size:
            print(f"   尺寸ID: {first_size.id}")
            print(f"   产品ID: {first_size.product_id}")
            print(f"   尺寸名: {first_size.size_name}")
            print(f"   价格: {first_size.price}")
            print(f"   冲印ID: {first_size.printer_product_id}")
        
        # 测试通过ID查找
        print("\n3. 测试通过ID查找:")
        if first_size:
            result = size_name_filter(str(first_size.id))
            print(f"   ID {first_size.id} -> {result}")
        
        # 测试通过冲印ID查找
        print("\n4. 测试通过冲印ID查找:")
        if first_size and first_size.printer_product_id:
            result = size_name_filter(first_size.printer_product_id)
            print(f"   冲印ID {first_size.printer_product_id} -> {result}")
        
        # 检查是否有其他价格来源
        print("\n5. 检查所有ProductSize记录:")
        all_sizes = ProductSize.query.all()
        for size in all_sizes:
            print(f"   ID: {size.id}, 尺寸: {size.size_name}, 价格: {size.price}")

if __name__ == "__main__":
    detailed_test()




