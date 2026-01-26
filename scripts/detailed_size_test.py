#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细测试尺寸查找逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, ProductSize

def detailed_size_test():
    """详细测试尺寸查找逻辑"""
    
    print("🔍 详细测试尺寸查找逻辑...")
    
    with app.app_context():
        test_size = "30x30cm肌理画框"
        print(f"📦 测试尺寸: '{test_size}'")
        
        # 1. 直接查找
        print(f"\n1️⃣ 直接查找:")
        size = ProductSize.query.filter_by(size_name=test_size).first()
        if size:
            print(f"   ✅ 找到: {size.size_name} (¥{size.price})")
        else:
            print(f"   ❌ 没找到")
        
        # 2. 模糊查找
        print(f"\n2️⃣ 模糊查找:")
        sizes = ProductSize.query.filter(ProductSize.size_name.contains(test_size)).all()
        if sizes:
            for size in sizes:
                print(f"   ✅ 包含匹配: {size.size_name} (¥{size.price})")
        else:
            print(f"   ❌ 没找到包含匹配")
        
        # 3. 反向查找
        print(f"\n3️⃣ 反向查找:")
        sizes = ProductSize.query.all()
        for size in sizes:
            if test_size in size.size_name:
                print(f"   ✅ 反向匹配: {size.size_name} (¥{size.price})")
        
        # 4. 检查所有尺寸
        print(f"\n4️⃣ 所有尺寸:")
        all_sizes = ProductSize.query.filter_by(is_active=True).all()
        for size in all_sizes:
            print(f"   ID: {size.id}, 名称: '{size.size_name}', 价格: {size.price}")
            if size.size_name == test_size:
                print(f"      ✅ 完全匹配!")
            elif test_size in size.size_name:
                print(f"      ✅ 包含匹配!")
        
        # 5. 检查字符串比较
        print(f"\n5️⃣ 字符串比较:")
        for size in all_sizes:
            print(f"   比较: '{test_size}' == '{size.size_name}' -> {test_size == size.size_name}")
            if test_size == size.size_name:
                print(f"      ✅ 完全匹配!")
                break

if __name__ == "__main__":
    detailed_size_test()
